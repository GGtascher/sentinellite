import enum
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def uuid_str() -> str:
    return str(uuid.uuid4())


class AlertStatus(enum.StrEnum):
    new = "new"
    investigating = "investigating"
    resolved = "resolved"
    false_positive = "false_positive"


alert_events = Table(
    "alert_events",
    Base.metadata,
    Column("alert_id", ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True),
    Column("event_id", ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_timestamp", "event_timestamp"),
        Index("ix_events_source_ip", "source_ip"),
        Index("ix_events_hostname", "hostname"),
        Index("ix_events_username", "username"),
        Index("ix_events_type", "event_type"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    event_timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    timestamp_original: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    source_type: Mapped[str] = mapped_column(String(64), default="api")
    parser_name: Mapped[str] = mapped_column(String(64))
    parser_confidence: Mapped[float] = mapped_column(Float)
    parse_status: Mapped[str] = mapped_column(String(24))
    hostname: Mapped[str | None] = mapped_column(String(255))
    source_ip: Mapped[str | None] = mapped_column(String(45))
    source_port: Mapped[int | None] = mapped_column(Integer)
    destination_ip: Mapped[str | None] = mapped_column(String(45))
    destination_port: Mapped[int | None] = mapped_column(Integer)
    username: Mapped[str | None] = mapped_column(String(255))
    event_category: Mapped[str | None] = mapped_column(String(100))
    event_type: Mapped[str | None] = mapped_column(String(100))
    event_action: Mapped[str | None] = mapped_column(String(100))
    event_outcome: Mapped[str | None] = mapped_column(String(50))
    severity: Mapped[str | None] = mapped_column(String(20))
    process_name: Mapped[str | None] = mapped_column(String(512))
    process_id: Mapped[int | None] = mapped_column(Integer)
    parent_process_name: Mapped[str | None] = mapped_column(String(512))
    command_line: Mapped[str | None] = mapped_column(Text)
    protocol: Mapped[str | None] = mapped_column(String(50))
    url: Mapped[str | None] = mapped_column(Text)
    http_method: Mapped[str | None] = mapped_column(String(16))
    http_status: Mapped[int | None] = mapped_column(Integer)
    file_path: Mapped[str | None] = mapped_column(Text)
    file_hash: Mapped[str | None] = mapped_column(String(128))
    message: Mapped[str | None] = mapped_column(Text)
    raw_event: Mapped[str] = mapped_column(Text)
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)
    alerts: Mapped[list["Alert"]] = relationship(secondary=alert_events, back_populates="events")


class Alert(Base):
    __tablename__ = "alerts"
    __table_args__ = (Index("ix_alerts_severity", "severity"), Index("ix_alerts_rule_id", "rule_id"))

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uuid_str)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(24), default=AlertStatus.new.value)
    rule_id: Mapped[str] = mapped_column(String(64))
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    event_count: Mapped[int] = mapped_column(Integer, default=1)
    affected_host: Mapped[str | None] = mapped_column(String(255))
    source_ip: Mapped[str | None] = mapped_column(String(45))
    username: Mapped[str | None] = mapped_column(String(255))
    mitre: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    analyst_notes: Mapped[str] = mapped_column(Text, default="")
    events: Mapped[list[Event]] = relationship(secondary=alert_events, back_populates="alerts")
