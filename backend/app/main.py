import sys
import os
import logging
import threading
import webbrowser
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
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

    # Auto-open browser after server is ready
    if os.environ.get("IELTS_OPEN_BROWSER", "1") == "1":
        def _open():
            import time; time.sleep(1.5)
            webbrowser.open("http://localhost:8000")
        threading.Thread(target=_open, daemon=True).start()

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

# ── Serve React SPA in production ──
_frontend_dir = None
if getattr(sys, 'frozen', False):
    _frontend_dir = Path(sys._MEIPASS) / "app" / "static"
else:
    _dev_static = Path(__file__).resolve().parent / "static"
    _dev_dist = settings.base_dir / "frontend" / "dist"
    _frontend_dir = _dev_static if _dev_static.exists() else _dev_dist

if _frontend_dir and _frontend_dir.exists() and (_frontend_dir / "index.html").exists():
    logger.info("✓ Serving React frontend from %s", _frontend_dir)
    _assets_dir = _frontend_dir / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(_assets_dir)), name="assets")
    _index_html = (_frontend_dir / "index.html").read_text()

    @app.get("/{full_path:path}")
    async def catch_all_spa(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("uploads/"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        return HTMLResponse(content=_index_html)

    @app.get("/")
    async def root():
        return HTMLResponse(content=_index_html)


# ── Entry point for double-click / PyInstaller ──
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, log_level="info")
