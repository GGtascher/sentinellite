import io

from app.models import Event


def test_single_event_round_trip(client, db):
    response = client.post("/api/v1/ingest/event", json={"event": "Aug 15 14:31:11 server01 sshd[1234]: Failed password for root from 10.0.0.5 port 55422 ssh2"})
    assert response.status_code == 200
    result = response.json()
    assert result["total_submitted"] == 1
    event_response = client.get(f"/api/v1/events/{result['event_ids'][0]}")
    assert event_response.status_code == 200
    assert event_response.json()["raw_event"].startswith("Aug 15")
    assert db.query(Event).count() == 1


def test_multiline_text_counts_raw_fallback_as_safe_storage(client):
    response = client.post("/api/v1/ingest/text", json={"event": "mysterious frobnicator\nuser=bob src=10.0.0.1 result=failed"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_submitted"] == 2
    assert body["raw_fallback"] == 1
    assert body["partially_parsed"] == 1


def test_pretty_json_text_is_one_structured_event(client):
    response = client.post(
        "/api/v1/ingest/text",
        json={"event": '{\n  "host": "lab-01",\n  "event_type": "application_health"\n}', "source_type": "workbench"},
    )
    assert response.status_code == 200
    assert response.json()["total_submitted"] == 1
    event = client.get(f"/api/v1/events/{response.json()['event_ids'][0]}").json()
    assert event["hostname"] == "lab-01"
    assert event["source_type"] == "workbench"


def test_empty_and_oversized_payloads_are_rejected(client):
    assert client.post("/api/v1/ingest/event", json={"event": ""}).status_code == 422
    response = client.post("/api/v1/ingest/event", json={"event": "x" * 300_000})
    assert response.status_code == 200
    assert response.json()["rejected"] == 1


def test_upload_rejects_traversal_extension_and_binary(client):
    response = client.post("/api/v1/ingest/upload", files={"file": ("../../payload.exe", b"MZ", "application/octet-stream")})
    assert response.status_code == 422
    response = client.post("/api/v1/ingest/upload", files={"file": ("events.log", b"abc\x00def", "text/plain")})
    assert response.status_code == 422


def test_csv_upload_becomes_structured_events(client):
    content = b"timestamp,user,src_ip,result\n2026-08-15T12:00:00Z,alice,10.1.2.3,failed\n"
    response = client.post("/api/v1/ingest/upload", files={"file": ("events.csv", io.BytesIO(content), "text/csv")})
    assert response.status_code == 200
    assert response.json()["successfully_parsed"] == 1


def test_api_pagination_and_filtering(client):
    client.post("/api/v1/ingest/batch", json={"events": ["src=10.0.0.1 action=blocked", "src=10.0.0.2 action=blocked"], "source_type": "workbench"})
    response = client.get("/api/v1/events?page=1&page_size=1&source_ip=10.0.0.1")
    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["source_type"] == "workbench"
    assert response.json()["items"][0]["parse_status"] == "parsed"
    assert client.get("/api/v1/events?source_type=other").json()["total"] == 0


def test_health_and_missing_resources(client):
    assert client.get("/api/v1/health").json()["database"] == "available"
    rules = client.get("/api/v1/rules")
    assert rules.status_code == 200
    assert len(rules.json()) >= 12
    assert client.get("/api/v1/events/not-real").status_code == 404
    assert client.patch("/api/v1/alerts/not-real", json={"status": "resolved"}).status_code == 404
