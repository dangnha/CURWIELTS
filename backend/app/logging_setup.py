import logging
import sys
from pathlib import Path

LOG_FORMAT = "%(asctime)s [%(levelname)-7s] %(name)-20s | %(message)s"
LOG_DATE_FORMAT = "%H:%M:%S"


def setup_logging(debug: bool = True, log_dir: Path | None = None) -> logging.Logger:
    """Configure logging for the entire application. Call once at startup."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Remove any existing handlers (uvicorn adds some)
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)

    # Console handler — always active
    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG if debug else logging.INFO)
    console.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
    root_logger.addHandler(console)

    # File handler — persistent log
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_dir / "server.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT))
        root_logger.addHandler(file_handler)

    # Quiet down noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "chromadb", "httpcore", "httpx", "openai",
                  "grpc", "google.api_core", "google.auth", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logger = logging.getLogger("app")
    logger.info("=" * 60)
    logger.info("IELTS Multi-Agent Scoring System — starting up")
    logger.info("=" * 60)
    return logger
