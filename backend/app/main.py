from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, SessionLocal, UPLOADS_DIR, engine
from .routers import analytics, employees, leave, onboarding, performance, recruitment
from .seed import seed_database
from .services.ai import ai_provider_name
from .settings import get_settings


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db, UPLOADS_DIR)
    finally:
        db.close()
    yield


app = FastAPI(
    title="AI-Powered HRMS API",
    version="1.0.0",
    description="Backend for the AI-powered HR management system.",
    lifespan=lifespan,
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.backend_cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

app.include_router(employees.router)
app.include_router(recruitment.router)
app.include_router(leave.router)
app.include_router(performance.router)
app.include_router(onboarding.router)
app.include_router(analytics.router)


@app.get("/health")
def health() -> dict[str, str | None]:
    return {
        "status": "ok",
        "ai_provider": ai_provider_name(),
        "openai_model": settings.openai_model if settings.openai_enabled else None,
    }
