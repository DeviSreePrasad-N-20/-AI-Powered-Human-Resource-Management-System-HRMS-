from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
ROOT_DIR = BACKEND_DIR.parent


def _load_env_files() -> None:
    # Support either a repo-root `.env` or a backend-local `.env`.
    for env_path in (ROOT_DIR / ".env", BACKEND_DIR / ".env"):
        if env_path.exists():
            load_dotenv(env_path, override=False)


_load_env_files()


def _resolve_path(raw_value: str, *, default: Path) -> Path:
    candidate = raw_value.strip()
    if not candidate:
        return default

    path = Path(candidate).expanduser()
    if not path.is_absolute():
        path = (ROOT_DIR / path).resolve()
    return path


def _parse_csv(raw_value: str, *, default: list[str]) -> tuple[str, ...]:
    values = [item.strip().rstrip("/") for item in raw_value.split(",") if item.strip()]
    if not values:
        values = default
    return tuple(values)


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    openai_reasoning_effort: str
    openai_timeout_seconds: float
    hr_contact_email: str
    data_dir: Path
    uploads_dir: Path
    database_url: str
    backend_cors_origins: tuple[str, ...]

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    reasoning_effort = os.getenv("OPENAI_REASONING_EFFORT", "low").strip().lower() or "low"
    if reasoning_effort not in {"none", "low", "medium", "high", "xhigh"}:
        reasoning_effort = "low"

    data_dir = _resolve_path(os.getenv("DATA_DIR", ""), default=BACKEND_DIR / "data")
    uploads_dir = _resolve_path(os.getenv("UPLOADS_DIR", ""), default=BACKEND_DIR / "uploads")
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        database_url = f"sqlite:///{(data_dir / 'hrms.db').as_posix()}"

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip() or "gpt-5.4-mini",
        openai_reasoning_effort=reasoning_effort,
        openai_timeout_seconds=float(os.getenv("OPENAI_TIMEOUT_SECONDS", "45").strip() or "45"),
        hr_contact_email=os.getenv("HR_CONTACT_EMAIL", "hr@company.local").strip() or "hr@company.local",
        data_dir=data_dir,
        uploads_dir=uploads_dir,
        database_url=database_url,
        backend_cors_origins=_parse_csv(
            os.getenv("BACKEND_CORS_ORIGINS", ""),
            default=["http://localhost:5173", "http://127.0.0.1:5173"],
        ),
    )
