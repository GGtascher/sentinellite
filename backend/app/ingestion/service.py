import csv
import io
import json
from pathlib import PurePath
from typing import Any

from sqlalchemy.orm import Session

from app.config import Settings
from app.correlation import correlate_auth_process
from app.detection.engine import DetectionEngine
from app.models import Event
from app.normalization import normalize
from app.parsers import ParserEngine
from app.schemas import IngestionResult

ALLOWED_EXTENSIONS = {".txt", ".log", ".json", ".jsonl", ".ndjson", ".csv", ".tsv"}


class IngestionError(ValueError):
    pass


def records_from_upload(content: bytes, filename: str, settings: Settings) -> list[str]:
    if len(content) > settings.max_upload_bytes:
        raise IngestionError(f"upload exceeds {settings.max_upload_bytes} byte limit")
    safe_name = PurePath(filename.replace("\\", "/")).name
    extension = PurePath(safe_name).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise IngestionError(f"unsupported file type: {extension or 'no extension'}")
    if b"\x00" in content:
        raise IngestionError("binary files are not supported")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionError("file must be UTF-8 encoded text") from exc
    if extension == ".json":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise IngestionError(f"malformed JSON file at line {exc.lineno}") from exc
        values = parsed if isinstance(parsed, list) else [parsed]
        return [json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value for value in values]
    if extension in {".csv", ".tsv"}:
        delimiter = "\t" if extension == ".tsv" else ","
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames:
            raise IngestionError("delimited file requires a header row")
        return [json.dumps(row, ensure_ascii=False) for row in reader]
    return [line for line in text.splitlines() if line.strip()]


def records_from_text(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, list):
            return [json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value for value in parsed]
    except json.JSONDecodeError:
        pass
    return [line for line in text.splitlines() if line.strip()]


def ingest_records(
    db: Session,
    records: list[str | dict[str, Any]],
    source_type: str,
    parser: ParserEngine,
    detector: DetectionEngine,
    settings: Settings,
) -> IngestionResult:
    if len(records) > settings.max_batch_events:
        raise IngestionError(f"batch exceeds {settings.max_batch_events} event limit")
    counts = {"parsed": 0, "partial": 0, "raw": 0, "rejected": 0}
    ids: list[str] = []
    messages: list[str] = []
    for index, record in enumerate(records):
        raw = json.dumps(record, ensure_ascii=False, separators=(",", ":")) if isinstance(record, dict) else record
        if not raw.strip():
            counts["rejected"] += 1
            messages.append(f"Record {index + 1}: empty event rejected")
            continue
        if len(raw) > settings.max_event_chars:
            counts["rejected"] += 1
            messages.append(f"Record {index + 1}: exceeds {settings.max_event_chars} character limit")
            continue
        try:
            result = parser.parse(raw)
            event = Event(**normalize(result, raw, source_type))
            db.add(event)
            db.flush()
            detector.evaluate(db, event)
            correlate_auth_process(db, event)
            counts[result.status] += 1
            ids.append(event.id)
        except Exception:
            db.rollback()
            raise
    db.commit()
    if counts["raw"]:
        messages.append("Unknown formats were safely stored using raw fallback.")
    return IngestionResult(
        total_submitted=len(records), successfully_parsed=counts["parsed"], partially_parsed=counts["partial"],
        raw_fallback=counts["raw"], rejected=counts["rejected"], event_ids=ids, messages=messages,
    )
