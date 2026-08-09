from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth, dashboard, evidence, goals, growth, phase3, profile, tasks, timer
from app.core.config import get_settings
from app.db.session import engine
from sqlalchemy import text

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(profile.router, prefix=settings.api_prefix)
app.include_router(goals.router, prefix=settings.api_prefix)
app.include_router(tasks.router, prefix=settings.api_prefix)
app.include_router(timer.router, prefix=settings.api_prefix)
app.include_router(evidence.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)
app.include_router(growth.router, prefix=settings.api_prefix)
app.include_router(phase3.router, prefix=settings.api_prefix)
