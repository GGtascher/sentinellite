from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Alert, Event


def correlate_auth_process(db: Session, event: Event) -> Alert | None:
    """Correlate failures -> success -> suspicious process on the same identity/host."""
    if event.event_type != "process_creation" or not event.hostname:
        return None
    command = (event.command_line or "").lower()
    if not any(token in command for token in ("powershell", "-enc", "-encodedcommand")):
        return None
    cutoff = datetime.now(UTC) - timedelta(minutes=15)
    recent = list(db.scalars(select(Event).where(Event.ingested_at >= cutoff, Event.hostname == event.hostname).order_by(Event.ingested_at)).all())
    failures = [item for item in recent if item.event_type == "authentication_failure" and (not event.username or item.username == event.username)]
    successes = [item for item in recent if item.event_type == "authentication_success" and (not event.username or item.username == event.username)]
    if len(failures) < 3 or not successes:
        return None
    existing = db.scalar(select(Alert).where(Alert.rule_id == "CORR-001", Alert.status.in_(["new", "investigating"]), Alert.affected_host == event.hostname))
    if existing:
        if event not in existing.events:
            existing.events.append(event)
            existing.event_count = len(existing.events)
            existing.last_seen = event.event_timestamp or event.ingested_at
        return existing
    supporting = [*failures[-5:], successes[-1], event]
    alert = Alert(
        title="Authentication compromise sequence", description="Repeated failures were followed by a successful login and suspicious process execution.",
        severity="critical", rule_id="CORR-001", first_seen=supporting[0].event_timestamp or supporting[0].ingested_at,
        last_seen=event.event_timestamp or event.ingested_at, event_count=len(supporting), affected_host=event.hostname,
        source_ip=successes[-1].source_ip, username=event.username or successes[-1].username,
        mitre={"tactic": "Credential Access, Execution", "technique": "T1110, T1059.001"},
        evidence={"sequence": ["authentication_failure", "authentication_success", "process_creation"]}, events=supporting,
    )
    db.add(alert)
    return alert
