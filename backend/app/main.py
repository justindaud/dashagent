# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.db.database import Base, engine
from app.db.clickhouse import clickhouse_engine
from app.config.settings import settings
from app.routers.auth_routes import router as auth_router
from app.routers.user_routes import router as user_router
from app.routers.profile_routes import router as profile_router
from app.routers.session_routes import router as session_router
from app.routers.agent_routes import router as agent_router
from app.routers.csv_routes import router as csv_router
from app.routers.dashboard_routes import router as dashboard_router
from app.routers.analytic_routes import router as analytic_router
from app.routers.room_build_routes import router as room_build_router
from app.utils.response import setup_exception_handlers
from app.routers.chatkit_routes import router as chatkit_router

from app.jobs.cleanup_session import (
    start_prealloc_cleanup_scheduler,
    stop_prealloc_cleanup_scheduler,
)

from app.jobs.cleanup_csv import (
    start_csv_cleanup_scheduler,
    stop_csv_cleanup_scheduler,
)

from app.jobs.cleanup_clickhouse import (
    start_clickhouse_cleanup_scheduler,
    stop_clickhouse_cleanup_scheduler,
)

logging.basicConfig(level=logging.INFO)

try:
    logging.info("Step 1: Creating database extensions (vector, postgis)...")
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
    logging.info("Extensions created successfully.")
except Exception as e:
    logging.error(f"Failed to create extensions: {e}")
    raise

try:
    logging.info("Step 2: Running Base.metadata.create_all()...")
    Base.metadata.create_all(bind=engine)
    logging.info("SQLAlchemy models created/checked successfully.")
except Exception as e:
    logging.error(f"Failed to run create_all: {e}")
    raise

async def lifespan(app: FastAPI):
    try:
        with clickhouse_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logging.info("Successfully connected to ClickHouse via SQLAlchemy")
    except Exception as e:
        logging.error("Failed to connect to ClickHouse: %s", e, exc_info=True)

    start_prealloc_cleanup_scheduler()
    start_csv_cleanup_scheduler()
    start_clickhouse_cleanup_scheduler()
    yield
    stop_prealloc_cleanup_scheduler()
    stop_csv_cleanup_scheduler()
    stop_clickhouse_cleanup_scheduler()

# Fast API
app = FastAPI(title="DashAgent API", version="1.0.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://194.233.69.219:3001", "https://dashagent.pulangkeuttara.co.id"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(csv_router)
app.include_router(dashboard_router)
app.include_router(analytic_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(profile_router)
app.include_router(session_router)
app.include_router(agent_router)
app.include_router(room_build_router)
app.include_router(chatkit_router)

setup_exception_handlers(app)

@app.get("/")
def read_root():
    return {"message": "DashAgent API is running!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=False)
