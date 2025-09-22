# backend/app/jobs/cleanup_session.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.config.settings import settings
from app.repositories import session_repository as srepo

logger = logging.getLogger(__name__)
_scheduler: AsyncIOScheduler | None = None

@contextmanager
def _db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def _do_cleanup_once():
    with _db_session() as db:
        stats = srepo.cleanup_preallocs(
            db,
            ttl_unconsumed_minutes=settings.PREALLOC_TTL_MINUTES_UNCONSUMED,
            ttl_consumed_minutes=settings.PREALLOC_TTL_MINUTES_CONSUMED,
        )
    logger.info("[prealloc] cleanup run -> deleted_unconsumed=%s deleted_consumed=%s total=%s", stats["deleted_unconsumed"], stats["deleted_consumed"], stats["deleted_total"])

def start_prealloc_cleanup_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        logger.info("[prealloc] scheduler already running")
        return
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _do_cleanup_once,
        trigger=IntervalTrigger(minutes=settings.PREALLOC_CLEANUP_INTERVAL_MINUTES),
        id="prealloc_cleanup",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("[prealloc] scheduler started")

def stop_prealloc_cleanup_scheduler():
    global _scheduler
    if not _scheduler:
        return
    try:
        _scheduler.shutdown(wait=False)
        logger.info("[prealloc] scheduler stopped")
    finally:
        _scheduler = None
