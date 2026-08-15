import ipaddress
from datetime import UTC, datetime
from pathlib import PurePath
from typing import Any

from dateutil import parser as date_parser

from app.parsers.base import ParseResult

ALIASES = {
    "timestamp": "event_timestamp",
    "time": "event_timestamp",
    "@timestamp": "event_timestamp",
    "datetime": "event_timestamp",
    "host": "hostname",
    "computer": "hostname",
    "computername": "hostname",
    "src": "source_ip",
    "source": "source_ip",
    "src_ip": "source_ip",
    "sourceip": "source_ip",
    "client_ip": "source_ip",
    "ip": "source_ip",
    "dst": "destination_ip",
    "destination": "destination_ip",
    "dst_ip": "destination_ip",
    "destinationip": "destination_ip",
    "dest_ip": "destination_ip",
    "sport": "source_port",
    "src_port": "source_port",
    "sourceport": "source_port",
    "dport": "destination_port",
    "dst_port": "destination_port",
    "destinationport": "destination_port",
    "user": "username",
    "account": "username",
    "accountname": "username",
    "category": "event_category",
    "type": "event_type",
    "action": "event_action",
    "result": "event_outcome",
    "outcome": "event_outcome",
    "level": "severity",
    "process": "process_name",
    "image": "process_name",
    "newprocessname": "process_name",
    "pid": "process_id",
    "processid": "process_id",
    "parentimage": "parent_process_name",
    "parentprocessname": "parent_process_name",
    "commandline": "command_line",
    "cmdline": "command_line",
    "uri": "url",
    "request": "url",
    "method": "http_method",
    "status": "http_status",
    "path": "file_path",
    "filename": "file_path",
    "hash": "file_hash",
    "hashes": "file_hash",
    "msg": "message",
    "eventid": "event_id",
}

MODEL_FIELDS = {
    "event_timestamp", "hostname", "source_ip", "source_port", "destination_ip",
    "destination_port", "username", "event_category", "event_type", "event_action",
    "event_outcome", "severity", "process_name", "process_id", "parent_process_name",
    "command_line", "protocol", "url", "http_method", "http_status", "file_path",
    "file_hash", "message",
}


def _safe_scalar(value: Any, limit: int = 16_384) -> Any:
    if isinstance(value, str):
        return value.replace("\x00", "")[:limit]
    return value


def _canonical_key(key: str) -> str:
    compact = key.replace(".", "_").replace("-", "_")
    lowered = compact.lower()
    return ALIASES.get(lowered, lowered)


def parse_timestamp(value: Any, now: datetime | None = None) -> tuple[datetime | None, str | None]:
    if value is None or value == "":
        return None, None
    original = str(value)[:255]
    try:
        if isinstance(value, (int, float)) or original.isdigit() and len(original) >= 10:
            number = float(value)
            if number > 10_000_000_000:
                number /= 1000
            parsed = datetime.fromtimestamp(number, tz=UTC)
        else:
            reference = now or datetime.now(UTC)
            parsed = date_parser.parse(original, default=reference.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            parsed = parsed.astimezone(UTC)
        return parsed, original
    except (ValueError, TypeError, OverflowError, OSError):
        return None, original


def valid_ip(value: Any) -> str | None:
    if value is None:
        return None
    try:
        return str(ipaddress.ip_address(str(value).strip("[]")))
    except ValueError:
        return None


def valid_port(value: Any) -> int | None:
    try:
        port = int(str(value))
    except (TypeError, ValueError):
        return None
    return port if 0 <= port <= 65535 else None


def normalize(result: ParseResult, raw_event: str, source_type: str = "api") -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    for original_key, original_value in result.fields.items():
        key = _canonical_key(str(original_key))
        value = _safe_scalar(original_value)
        if key in MODEL_FIELDS and key not in normalized:
            normalized[key] = value
        else:
            metadata[str(original_key)[:128]] = value

    timestamp, timestamp_original = parse_timestamp(normalized.get("event_timestamp"))
    normalized["event_timestamp"] = timestamp
    normalized["timestamp_original"] = timestamp_original
    normalized["source_ip"] = valid_ip(normalized.get("source_ip"))
    normalized["destination_ip"] = valid_ip(normalized.get("destination_ip"))
    normalized["source_port"] = valid_port(normalized.get("source_port"))
    normalized["destination_port"] = valid_port(normalized.get("destination_port"))
    for field in ("process_id", "http_status"):
        try:
            normalized[field] = int(normalized[field]) if normalized.get(field) is not None else None
        except (TypeError, ValueError):
            normalized[field] = None
    process = normalized.get("process_name")
    if process:
        normalized["process_name"] = PurePath(str(process).replace("\\", "/")).name
    outcome = str(normalized.get("event_outcome") or "").lower()
    normalized["event_outcome"] = {
        "failed": "failure", "fail": "failure", "denied": "failure", "blocked": "failure",
        "ok": "success", "succeeded": "success", "successful": "success", "allowed": "success",
    }.get(outcome, outcome or None)
    normalized.update(
        source_type=source_type[:64],
        parser_name=result.parser_name,
        parser_confidence=round(result.confidence, 3),
        parse_status=result.status,
        raw_event=raw_event,
        event_metadata=metadata,
    )
    return normalized
