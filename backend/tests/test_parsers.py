import json
from pathlib import Path

import pytest
from app.normalization import normalize, parse_timestamp, valid_ip
from app.parsers import ParserEngine


@pytest.mark.parametrize(("raw", "parser_name", "expected"), [
    ("Aug 15 14:31:11 server01 sshd[1234]: Failed password for root from 10.0.0.5 port 55422 ssh2", "linux_auth", {"event_type": "authentication_failure", "source_ip": "10.0.0.5", "username": "root"}),
    ('10.0.0.4 - - [15/Aug/2026:14:12:01 +0200] "GET /login HTTP/1.1" 401 1234', "http_access", {"http_method": "GET", "http_status": 401, "url": "/login"}),
    ('{"timestamp":"2026-08-15T12:20:00Z","user":"alice","ip":"10.1.2.3","result":"failed"}', "json", {"username": "alice", "source_ip": "10.1.2.3", "event_outcome": "failure"}),
    ("src_ip=192.168.1.12 dst_ip=8.8.8.8 action=blocked severity=high", "firewall", {"source_ip": "192.168.1.12", "destination_ip": "8.8.8.8", "event_type": "firewall_denied"}),
])
def test_known_parser_corpus(raw, parser_name, expected):
    result = ParserEngine().parse(raw)
    event = normalize(result, raw)
    assert result.parser_name == parser_name
    for key, value in expected.items():
        assert event[key] == value


def test_heuristic_extracts_ipv4_and_obvious_auth_fields():
    raw = "2026-08-15 14:31:11 failed login user=admin from 10.0.0.5"
    event = normalize(ParserEngine().parse(raw), raw)
    assert event["source_ip"] == "10.0.0.5"
    assert event["username"] == "admin"
    assert event["event_type"] == "authentication_failure"
    assert event["event_timestamp"].isoformat() == "2026-08-15T14:31:11+00:00"


def test_heuristic_extracts_ipv6_without_treating_numbers_as_ip():
    raw = "odd-sensor source 2001:db8::42 destination 12345 pid=811"
    event = normalize(ParserEngine().parse(raw), raw)
    assert event["source_ip"] == "2001:db8::42"
    assert event["process_id"] == 811
    assert event["destination_ip"] is None


def test_raw_fallback_preserves_unknown_event():
    raw = "mysterious frobnicator became chartreuse"
    event = normalize(ParserEngine().parse(raw), raw)
    assert event["parser_name"] == "raw_fallback"
    assert event["parse_status"] == "raw"
    assert event["raw_event"] == raw


@pytest.mark.parametrize("value", ["999.2.3.4", "12345", "1.2.3", "hello", "1:2:3:4:5:6:7:8:9"])
def test_invalid_ip_rejected(value):
    assert valid_ip(value) is None


def test_timestamp_preserves_invalid_original_without_invention():
    parsed, original = parse_timestamp("not-a-time")
    assert parsed is None
    assert original == "not-a-time"


def test_timestamp_converts_offset_to_utc():
    parsed, _ = parse_timestamp("2026-08-15T14:31:11+02:00")
    assert parsed.isoformat() == "2026-08-15T12:31:11+00:00"


def test_malformed_json_is_not_discarded():
    raw = '{"timestamp": nope, "script": "<script>alert(1)</script>"}'
    event = normalize(ParserEngine().parse(raw), raw)
    assert event["raw_event"] == raw
    assert event["parser_name"] in {"key_value", "heuristic", "raw_fallback"}


def test_windows_event_wins_over_generic_json_parser():
    raw = '{"EventID":4625,"Computer":"lab-dc","user":"alice","src_ip":"10.2.3.4"}'
    result = ParserEngine().parse(raw)
    event = normalize(result, raw)
    assert result.parser_name == "windows_event"
    assert event["event_type"] == "authentication_failure"
    assert event["hostname"] == "lab-dc"


def test_key_value_aliases_and_port_validation():
    raw = "client_ip=10.1.1.2 dst=2001:db8::3 sport=443 dport=70000 user=bob"
    event = normalize(ParserEngine().parse(raw), raw)
    assert event["source_ip"] == "10.1.1.2"
    assert event["destination_ip"] == "2001:db8::3"
    assert event["source_port"] == 443
    assert event["destination_port"] is None
    assert event["username"] == "bob"


def test_universal_parser_corpus():
    corpus = json.loads((Path(__file__).parent / "data" / "parser_corpus.json").read_text(encoding="utf-8"))
    for case in corpus:
        result = ParserEngine().parse(case["input"])
        event = normalize(result, case["input"])
        event["parser_name"] = result.parser_name
        for field, expected in case["expected"].items():
            assert event.get(field) == expected, f"{field} mismatch for {case['input']}"
