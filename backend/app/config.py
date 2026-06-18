from pydantic_settings import BaseSettings
from pathlib import Path

# Resolve relative to this file, not the process's current working
# directory -- the app is normally launched with cwd=backend/ (per the
# README), so a bare ".env" never actually pointed at the real .env file
# in the project root and was silently ignored by pydantic-settings.
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = {"extra": "ignore", "env_file": str(BASE_DIR / ".env"), "env_file_encoding": "utf-8"}

    app_name: str = "IELTS Multi-Agent Scorer"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    kb_source_dir: Path = BASE_DIR / "information-prompts"
    chroma_persist_dir: Path = BASE_DIR / "knowledge-base" / "chroma"
    uploads_dir: Path = BASE_DIR / "data" / "uploads"

    temperature: float = 0.3
    max_tokens: int = 8192
    max_concurrent_llm_calls: int = 3


settings = Settings()
