from datetime import UTC, datetime

from app.correlation import correlate_auth_process
from app.detection.engine import DetectionEngine, event_matches
from app.detection.rules import Rule, load_rules
from app.models import Alert, Event


def make_event(**values):
    defaults = {"raw_event": "synthetic", "parser_name": "test", "parser_confidence": 1.0, "parse_status": "parsed", "source_type": "test", "ingested_at": datetime.now(UTC)}
    defaults.update(values)
    return Event(**defaults)


def test_all_rules_load_and_have_unique_ids(settings):
    rules = load_rules(settings.rules_path)
    assert len(rules) >= 12
    assert len({rule.id for rule in rules}) == len(rules)
    assert all(rule.description and rule.severity for rule in rules)


def test_match_operators_are_deterministic():
    event = make_event(event_type="process_creation", command_line="powershell.exe -NoP -enc AAA")
    assert event_matches(event, {"event_type": "process_creation", "command_line": {"contains": "-enc"}})
    assert event_matches(event, {"command_line": {"regex": r"powershell.*-nop"}})
    assert not event_matches(event, {"event_type": {"in": ["network"]}})


def test_threshold_rule_creates_and_updates_one_alert(db):
    rule = Rule(id="TST-001", title="Failures", description="Repeated failures", severity="high", match={"event_type": "authentication_failure"}, group_by=["source_ip"], threshold={"count": 3, "timeframe_seconds": 60})
    engine = DetectionEngine([rule])
    for _ in range(3):
        event = make_event(event_type="authentication_failure", source_ip="10.0.0.5")
        db.add(event)
        db.flush()
        engine.evaluate(db, event)
    db.commit()
    alerts = db.query(Alert).all()
    assert len(alerts) == 1
    assert alerts[0].event_count == 3


def test_distinct_threshold_counts_ports_not_duplicate_events(db):
    rule = Rule(id="TST-002", title="Ports", description="Many ports", severity="medium", match={"event_category": "network"}, group_by=["source_ip"], threshold={"count": 3, "timeframe_seconds": 60, "distinct_field": "destination_port"})
    engine = DetectionEngine([rule])
    for port in [80, 80, 443, 22]:
        event = make_event(event_category="network", source_ip="10.0.0.8", destination_port=port)
        db.add(event)
        db.flush()
        engine.evaluate(db, event)
    db.commit()
    assert db.query(Alert).count() == 1


def test_sequence_rule_requires_order(db):
    rule = Rule(id="TST-003", title="Compromise", description="Failures then success", severity="critical", group_by=["source_ip", "username"], sequence={"timeframe_seconds": 600, "stages": [{"event_type": "authentication_failure"}, {"event_type": "authentication_success"}]})
    engine = DetectionEngine([rule])
    for event_type in ["authentication_failure", "authentication_success"]:
        event = make_event(event_type=event_type, source_ip="10.0.0.5", username="alice")
        db.add(event)
        db.flush()
        engine.evaluate(db, event)
    db.commit()
    assert db.query(Alert).count() == 1


def test_correlation_requires_failures_success_and_process(db):
    for event_type in ["authentication_failure"] * 3 + ["authentication_success"]:
        db.add(make_event(event_type=event_type, hostname="lab01", username="alice"))
    db.flush()
    process = make_event(event_type="process_creation", hostname="lab01", username="alice", command_line="powershell -EncodedCommand SAFEDEMO")
    db.add(process)
    db.flush()
    alert = correlate_auth_process(db, process)
    db.commit()
    assert alert is not None
    assert alert.rule_id == "CORR-001"
    assert alert.severity == "critical"
