import re
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.detection.rules import Rule, load_rules
from app.models import Alert, Event


def _event_time(event: Event) -> datetime:
    value = event.event_timestamp or event.ingested_at
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


def _matches_value(actual: Any, expected: Any) -> bool:
    if isinstance(expected, dict):
        if "contains" in expected:
            return str(expected["contains"]).lower() in str(actual or "").lower()
        if "regex" in expected:
            return re.search(str(expected["regex"]), str(actual or ""), re.IGNORECASE) is not None
        if "in" in expected:
            return str(actual).lower() in {str(value).lower() for value in expected["in"]}
        if "not_in" in expected:
            return str(actual).lower() not in {str(value).lower() for value in expected["not_in"]}
    if isinstance(expected, list):
        return str(actual).lower() in {str(value).lower() for value in expected}
    return str(actual or "").lower() == str(expected).lower()


def event_matches(event: Event, match: dict[str, Any]) -> bool:
    for field, expected in match.items():
        if field == "any":
            return any(event_matches(event, clause) for clause in expected)
        if field == "all":
            return all(event_matches(event, clause) for clause in expected)
        actual = getattr(event, field, None)
        if not _matches_value(actual, expected):
            return False
    return True


class DetectionEngine:
    def __init__(self, rules: list[Rule]) -> None:
        self.rules = [rule for rule in rules if rule.enabled]

    @classmethod
    def from_path(cls, path) -> "DetectionEngine":
        return cls(load_rules(path))

    def evaluate(self, db: Session, event: Event) -> list[Alert]:
        alerts: list[Alert] = []
        for rule in self.rules:
            if rule.sequence:
                supporting = self._sequence_events(db, event, rule)
                if not supporting:
                    continue
            elif not event_matches(event, rule.match):
                continue
            else:
                supporting = self._supporting_events(db, event, rule)
            required = rule.threshold.count if rule.threshold else 1
            measured = len({getattr(item, rule.threshold.distinct_field, None) for item in supporting}) if rule.threshold and rule.threshold.distinct_field else len(supporting)
            if measured < required:
                continue
            alert = self._upsert_alert(db, rule, event, supporting)
            alerts.append(alert)
        return alerts

    def _supporting_events(self, db: Session, event: Event, rule: Rule) -> list[Event]:
        if not rule.threshold:
            return [event]
        cutoff = datetime.now(UTC) - timedelta(seconds=rule.threshold.timeframe_seconds)
        candidates = list(db.scalars(select(Event).where(Event.ingested_at >= cutoff)).all())
        return [candidate for candidate in candidates if event_matches(candidate, rule.match) and all(getattr(candidate, key, None) == getattr(event, key, None) for key in rule.group_by)]

    @staticmethod
    def _sequence_events(db: Session, event: Event, rule: Rule) -> list[Event]:
        sequence = rule.sequence
        if not sequence or not event_matches(event, sequence.stages[-1]):
            return []
        cutoff = datetime.now(UTC) - timedelta(seconds=sequence.timeframe_seconds)
        candidates = list(db.scalars(select(Event).where(Event.ingested_at >= cutoff).order_by(Event.ingested_at)).all())
        candidates = [item for item in candidates if all(getattr(item, key, None) == getattr(event, key, None) for key in rule.group_by)]
        supporting: list[Event] = []
        position = 0
        for candidate in candidates:
            if event_matches(candidate, sequence.stages[position]):
                supporting.append(candidate)
                position += 1
                if position == len(sequence.stages):
                    return supporting
        return []

    @staticmethod
    def _upsert_alert(db: Session, rule: Rule, event: Event, supporting: list[Event]) -> Alert:
        group = {key: getattr(event, key, None) for key in rule.group_by}
        existing = db.scalar(select(Alert).where(Alert.rule_id == rule.id, Alert.status.in_(["new", "investigating"])).order_by(Alert.last_seen.desc()))
        if existing and all(existing.evidence.get("group", {}).get(key) == value for key, value in group.items()):
            known = {item.id for item in existing.events}
            existing.events.extend(item for item in supporting if item.id not in known)
            existing.event_count = len(existing.events)
            existing.last_seen = max(_event_time(item) for item in existing.events)
            return existing
        alert = Alert(
            title=rule.title, description=rule.description, severity=rule.severity, rule_id=rule.id,
            first_seen=min(_event_time(item) for item in supporting),
            last_seen=max(_event_time(item) for item in supporting),
            event_count=len(supporting), affected_host=event.hostname, source_ip=event.source_ip,
            username=event.username, mitre=rule.mitre, evidence={"group": group, "threshold_met": len(supporting)},
            events=supporting,
        )
        db.add(alert)
        return alert
