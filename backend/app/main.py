import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.config import get_settings
from app.detection import DetectionEngine
from app.parsers import ParserEngine

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.parser = ParserEngine()
    app.state.detector = DetectionEngine.from_path(settings.rules_path)
    logging.getLogger(__name__).info("Loaded %d detection rules", len(app.state.detector.rules))
    yield


app = FastAPI(
    title="SentinelLite API", version=settings.version,
    description="Local-first security log ingestion, normalization, detection, and investigation API.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Accept"],
)
app.include_router(router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
def root_health():
    return {"status": "healthy", "version": settings.version}


@app.get("/", include_in_schema=False)
def root():
    return {"name": "SentinelLite", "version": settings.version, "docs": "/docs"}
