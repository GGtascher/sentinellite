"""Initial event and alert schema."""
import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("event_timestamp", sa.DateTime(timezone=True)),
        sa.Column("timestamp_original", sa.String(255)), sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False), sa.Column("parser_name", sa.String(64), nullable=False),
        sa.Column("parser_confidence", sa.Float(), nullable=False), sa.Column("parse_status", sa.String(24), nullable=False),
        sa.Column("hostname", sa.String(255)), sa.Column("source_ip", sa.String(45)), sa.Column("source_port", sa.Integer()),
        sa.Column("destination_ip", sa.String(45)), sa.Column("destination_port", sa.Integer()), sa.Column("username", sa.String(255)),
        sa.Column("event_category", sa.String(100)), sa.Column("event_type", sa.String(100)), sa.Column("event_action", sa.String(100)),
        sa.Column("event_outcome", sa.String(50)), sa.Column("severity", sa.String(20)), sa.Column("process_name", sa.String(512)),
        sa.Column("process_id", sa.Integer()), sa.Column("parent_process_name", sa.String(512)), sa.Column("command_line", sa.Text()),
        sa.Column("protocol", sa.String(50)), sa.Column("url", sa.Text()), sa.Column("http_method", sa.String(16)),
        sa.Column("http_status", sa.Integer()), sa.Column("file_path", sa.Text()), sa.Column("file_hash", sa.String(128)),
        sa.Column("message", sa.Text()), sa.Column("raw_event", sa.Text(), nullable=False), sa.Column("metadata", sa.JSON(), nullable=False),
    )
    for name, column in (("timestamp", "event_timestamp"), ("source_ip", "source_ip"), ("hostname", "hostname"), ("username", "username"), ("type", "event_type")):
        op.create_index(f"ix_events_{name}", "events", [column])
    op.create_table(
        "alerts", sa.Column("id", sa.String(36), primary_key=True), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False), sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("status", sa.String(24), nullable=False), sa.Column("rule_id", sa.String(64), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False), sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False), sa.Column("event_count", sa.Integer(), nullable=False),
        sa.Column("affected_host", sa.String(255)), sa.Column("source_ip", sa.String(45)), sa.Column("username", sa.String(255)),
        sa.Column("mitre", sa.JSON(), nullable=False), sa.Column("evidence", sa.JSON(), nullable=False), sa.Column("analyst_notes", sa.Text(), nullable=False),
    )
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_rule_id", "alerts", ["rule_id"])
    op.create_table(
        "alert_events", sa.Column("alert_id", sa.String(36), sa.ForeignKey("alerts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_id", sa.String(36), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
    )


def downgrade() -> None:
    op.drop_table("alert_events")
    op.drop_table("alerts")
    op.drop_table("events")
