from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from sqlalchemy import desc, distinct, func, select, text
from sqlalchemy.orm import Session, selectinload

from app.config import Settings, get_settings
from app.database import get_db
from app.detection.rules import load_rules
from app.ingestion.service import (
    IngestionError,
    ingest_records,
    records_from_text,
    records_from_upload,
)
from app.models import Alert, Event
from app.schemas import (
    AlertDetail,
    AlertRead,
    AlertUpdate,
    EventRead,
    EventSummary,
    IngestBatchRequest,
    IngestEventRequest,
    IngestionResult,
    Page,
    RuleRead,
    Statistics,
)

router = APIRouter()
Db = Annotated[Session, Depends(get_db)]


def _engines(request: Request):
    return request.app.state.parser, request.app.state.detector


@router.get("/health", tags=["system"])
def health(db: Db) -> dict:
    try:
        db.execute(text("SELECT 1"))
        database = "available"
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "healthy", "database": database, "version": get_settings().version}


@router.post("/ingest/event", response_model=IngestionResult, tags=["ingestion"])
def ingest_event(payload: IngestEventRequest, request: Request, db: Db) -> IngestionResult:
    parser, detector = _engines(request)
    return ingest_records(db, [payload.event], payload.source_type, parser, detector, get_settings())


@router.post("/ingest/batch", response_model=IngestionResult, tags=["ingestion"])
def ingest_batch(payload: IngestBatchRequest, request: Request, db: Db) -> IngestionResult:
    parser, detector = _engines(request)
    return ingest_records(db, payload.events, payload.source_type, parser, detector, get_settings())


@router.post("/ingest/text", response_model=IngestionResult, tags=["ingestion"])
def ingest_text(payload: IngestEventRequest, request: Request, db: Db) -> IngestionResult:
    if not isinstance(payload.event, str):
        raise HTTPException(422, "text ingestion requires a string")
    records = records_from_text(payload.event)
    parser, detector = _engines(request)
    return ingest_records(db, records, payload.source_type, parser, detector, get_settings())


@router.post("/ingest/upload", response_model=IngestionResult, tags=["ingestion"])
async def ingest_upload(
    request: Request,
    db: Db,
    file: Annotated[UploadFile, File()],
    source_type: str = "file",
) -> IngestionResult:
    settings = get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    try:
        records = records_from_upload(content, file.filename or "upload.txt", settings)
        parser, detector = _engines(request)
        return ingest_records(db, records, source_type, parser, detector, settings)
    except IngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/events", response_model=Page, tags=["events"])
def list_events(
    db: Db, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    severity: str | None = None, source_ip: str | None = None, hostname: str | None = None,
    username: str | None = None, event_type: str | None = None, source_type: str | None = None,
    from_time: datetime | None = None, to_time: datetime | None = None,
) -> Page:
    filters = []
    for column, value in ((Event.severity, severity), (Event.source_ip, source_ip), (Event.hostname, hostname), (Event.username, username), (Event.event_type, event_type), (Event.source_type, source_type)):
        if value:
            filters.append(column == value)
    if from_time:
        filters.append(Event.event_timestamp >= from_time)
    if to_time:
        filters.append(Event.event_timestamp <= to_time)
    total = db.scalar(select(func.count()).select_from(Event).where(*filters)) or 0
    items = list(db.scalars(select(Event).where(*filters).order_by(desc(func.coalesce(Event.event_timestamp, Event.ingested_at))).offset((page - 1) * page_size).limit(page_size)).all())
    return Page(items=[EventSummary.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.get("/events/{event_id}", response_model=EventRead, tags=["events"])
def get_event(event_id: str, db: Db) -> Event:
    event = db.get(Event, event_id)
    if not event:
        raise HTTPException(404, "event not found")
    return event


@router.get("/events/{event_id}/alerts", response_model=list[AlertRead], tags=["events"])
def event_alerts(event_id: str, db: Db) -> list[Alert]:
    event = db.scalar(select(Event).where(Event.id == event_id).options(selectinload(Event.alerts)))
    if not event:
        raise HTTPException(404, "event not found")
    return event.alerts


@router.get("/alerts", response_model=Page, tags=["alerts"])
def list_alerts(
    db: Db, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    severity: str | None = None, status: str | None = None, rule_id: str | None = None,
) -> Page:
    filters = []
    for column, value in ((Alert.severity, severity), (Alert.status, status), (Alert.rule_id, rule_id)):
        if value:
            filters.append(column == value)
    total = db.scalar(select(func.count()).select_from(Alert).where(*filters)) or 0
    items = list(db.scalars(select(Alert).where(*filters).order_by(Alert.last_seen.desc()).offset((page - 1) * page_size).limit(page_size)).all())
    return Page(items=[AlertRead.model_validate(item) for item in items], total=total, page=page, page_size=page_size)


@router.get("/alerts/{alert_id}", response_model=AlertDetail, tags=["alerts"])
def get_alert(alert_id: str, db: Db) -> Alert:
    alert = db.scalar(select(Alert).where(Alert.id == alert_id).options(selectinload(Alert.events)))
    if not alert:
        raise HTTPException(404, "alert not found")
    return alert


@router.patch("/alerts/{alert_id}", response_model=AlertRead, tags=["alerts"])
def update_alert(alert_id: str, payload: AlertUpdate, db: Db) -> Alert:
    alert = db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(404, "alert not found")
    if payload.status is not None:
        alert.status = payload.status
    if payload.analyst_notes is not None:
        alert.analyst_notes = payload.analyst_notes
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/rules", response_model=list[RuleRead], tags=["detections"])
def list_detection_rules(settings: Annotated[Settings, Depends(get_settings)]) -> list[RuleRead]:
    return [RuleRead(**rule.model_dump()) for rule in load_rules(settings.rules_path)]


@router.get("/statistics", response_model=Statistics, tags=["analytics"])
def statistics(db: Db) -> Statistics:
    today = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    severity_rows = db.execute(select(Alert.severity, func.count(Alert.id)).group_by(Alert.severity)).all()
    category_rows = db.execute(select(Event.event_category, func.count(Event.id)).where(Event.event_category.is_not(None)).group_by(Event.event_category).order_by(func.count(Event.id).desc()).limit(8)).all()
    source_rows = db.execute(select(Event.source_ip, func.count(Event.id)).where(Event.source_ip.is_not(None)).group_by(Event.source_ip).order_by(func.count(Event.id).desc()).limit(8)).all()
    volume_rows = db.execute(select(func.date(Event.ingested_at), func.count(Event.id)).where(Event.ingested_at >= today - timedelta(days=6)).group_by(func.date(Event.ingested_at)).order_by(func.date(Event.ingested_at))).all()
    severities = {name: count for name, count in severity_rows}
    active = db.scalar(select(func.count()).select_from(Alert).where(Alert.status.in_(["new", "investigating"]))) or 0
    return Statistics(
        total_events=db.scalar(select(func.count()).select_from(Event)) or 0,
        events_today=db.scalar(select(func.count()).select_from(Event).where(Event.ingested_at >= today)) or 0,
        active_alerts=active, critical_alerts=severities.get("critical", 0), high_alerts=severities.get("high", 0),
        monitored_hosts=db.scalar(select(func.count(distinct(Event.hostname))).where(Event.hostname.is_not(None))) or 0,
        alerts_by_severity=severities,
        categories=[{"name": name, "count": count} for name, count in category_rows],
        top_source_ips=[{"name": name, "count": count} for name, count in source_rows],
        event_volume=[{"date": str(date), "count": count} for date, count in volume_rows],
    )


@router.get("/hosts", tags=["analytics"])
def hosts(db: Db) -> list[dict]:
    rows = db.execute(select(Event.hostname, func.count(Event.id), func.max(Event.ingested_at)).where(Event.hostname.is_not(None)).group_by(Event.hostname).order_by(func.count(Event.id).desc()).limit(200)).all()
    return [{"hostname": hostname, "event_count": count, "last_seen": last_seen} for hostname, count, last_seen in rows]
