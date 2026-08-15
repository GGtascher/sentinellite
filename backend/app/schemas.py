from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class IngestEventRequest(BaseModel):
    event: str | dict[str, Any]
    source_type: str = Field(default="api", max_length=64)

    @field_validator("event")
    @classmethod
    def event_not_empty(cls, value: str | dict[str, Any]) -> str | dict[str, Any]:
        if isinstance(value, str) and not value.strip():
            raise ValueError("event must not be empty")
        if isinstance(value, dict) and not value:
            raise ValueError("event object must not be empty")
        return value


class IngestBatchRequest(BaseModel):
    events: list[str | dict[str, Any]] = Field(min_length=1, max_length=5_000)
    source_type: str = Field(default="api", max_length=64)


class IngestionResult(BaseModel):
    total_submitted: int
    successfully_parsed: int
    partially_parsed: int
    raw_fallback: int
    rejected: int
    event_ids: list[str]
    messages: list[str] = []


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    event_timestamp: datetime | None
    timestamp_original: str | None
    ingested_at: datetime
    source_type: str
    parser_name: str
    parser_confidence: float
    parse_status: str
    hostname: str | None
    source_ip: str | None
    source_port: int | None
    destination_ip: str | None
    destination_port: int | None
    username: str | None
    event_category: str | None
    event_type: str | None
    event_action: str | None
    event_outcome: str | None
    severity: str | None
    process_name: str | None
    process_id: int | None
    parent_process_name: str | None
    command_line: str | None
    protocol: str | None
    url: str | None
    http_method: str | None
    http_status: int | None
    file_path: str | None
    file_hash: str | None
    message: str | None
    raw_event: str
    event_metadata: dict[str, Any]


class EventSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    event_timestamp: datetime | None
    ingested_at: datetime
    source_type: str
    parse_status: str
    hostname: str | None
    source_ip: str | None
    username: str | None
    event_category: str | None
    event_type: str | None
    event_outcome: str | None
    severity: str | None
    parser_name: str
    message: str | None


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    description: str
    severity: str
    status: str
    rule_id: str
    timestamp: datetime
    first_seen: datetime
    last_seen: datetime
    event_count: int
    affected_host: str | None
    source_ip: str | None
    username: str | None
    mitre: dict[str, Any]
    evidence: dict[str, Any]
    analyst_notes: str


class AlertDetail(AlertRead):
    events: list[EventSummary]


class AlertUpdate(BaseModel):
    status: Literal["new", "investigating", "resolved", "false_positive"] | None = None
    analyst_notes: str | None = Field(default=None, max_length=10_000)


class Page(BaseModel):
    items: list[Any]
    total: int
    page: int
    page_size: int


class RuleRead(BaseModel):
    id: str
    title: str
    description: str
    severity: str
    enabled: bool
    match: dict[str, Any]
    group_by: list[str]
    threshold: dict[str, Any] | None
    sequence: dict[str, Any] | None = None
    mitre: dict[str, str]


class Statistics(BaseModel):
    total_events: int
    events_today: int
    active_alerts: int
    critical_alerts: int
    high_alerts: int
    monitored_hosts: int
    alerts_by_severity: dict[str, int]
    categories: list[dict[str, Any]]
    top_source_ips: list[dict[str, Any]]
    event_volume: list[dict[str, Any]]
