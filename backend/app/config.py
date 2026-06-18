import sys
from pydantic_settings import BaseSettings
from pathlib import Path

# Resolve relative to this file in dev mode, or relative to the EXE
# in PyInstaller mode. PyInstaller extracts bundled files to sys._MEIPASS,
# but runtime data (.env, data/, knowledge-base/) sits next to the EXE.
def _is_frozen() -> bool:
    return getattr(sys, 'frozen', False)

# Dir where the EXE (or this script in dev) lives — runtime data goes here.
_EXE_DIR = Path(sys.executable).parent if _is_frozen() else Path(__file__).resolve().parent.parent.parent

# Dir where bundled files live (app/static, etc.) — sys._MEIPASS in PyInstaller.
_BUNDLE_DIR = Path(sys._MEIPASS) if _is_frozen() else _EXE_DIR

# In dev mode, find repo root; in PyInstaller, bundle dir IS the root.
BASE_DIR = _BUNDLE_DIR if _is_frozen() else _EXE_DIR


class Settings(BaseSettings):
    model_config = {
        "extra": "ignore",
        "env_file": str(_EXE_DIR / ".env"),
        "env_file_encoding": "utf-8",
    }

    app_name: str = "IELTS Multi-Agent Scorer"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    base_dir: Path = _EXE_DIR
    data_dir: Path = _EXE_DIR / "data"
    kb_source_dir: Path = BASE_DIR / "information-prompts"
    chroma_persist_dir: Path = _EXE_DIR / "knowledge-base" / "chroma"
    uploads_dir: Path = _EXE_DIR / "data" / "uploads"

    temperature: float = 0.3
    max_tokens: int = 8192
    max_concurrent_llm_calls: int = 3


settings = Settings()
