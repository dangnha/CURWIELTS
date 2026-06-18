import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.router import api_router
from app.logging_setup import setup_logging

# ── Logging ──
log_dir = settings.data_dir / "logs"
logger = setup_logging(debug=settings.debug, log_dir=log_dir)

# Reduce uvicorn noise but keep info
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    logger.info("✓ Server started — data_dir=%s", settings.data_dir)
    logger.info("✓ KB source: %s (exists=%s)", settings.kb_source_dir, settings.kb_source_dir.exists())

    try:
        from app.knowledge_base.vector_store import collection_count
        from app.knowledge_base.ingest import ingest_knowledge_base
        if collection_count() == 0 and settings.kb_source_dir.exists():
            logger.info("Knowledge base is empty — auto-ingesting from %s", settings.kb_source_dir)
            result = ingest_knowledge_base()
            logger.info("✓ KB ingest result: %s", result)
    except Exception:
        logger.exception("KB auto-ingest failed (non-fatal, continuing startup)")

    yield
    logger.info("Server shutting down")


app = FastAPI(title="IELTS Multi-Agent Scorer", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ──
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("→ %s %s", request.method, request.url.path)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("✗ %s %s FAILED", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})
    if response.status_code >= 400:
        logger.warning("← %s %s → %d", request.method, request.url.path, response.status_code)
    else:
        logger.info("← %s %s → %d", request.method, request.url.path, response.status_code)
    return response


app.include_router(api_router, prefix="/api/v1")

settings.uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(settings.uploads_dir)), name="uploads")
