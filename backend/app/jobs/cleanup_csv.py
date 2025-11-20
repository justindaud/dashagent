# app/jobs/cleanup_csv.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import contextmanager
from typing import Generator
from sqlalchemy.orm import Session
from sqlalchemy import delete
from app.db.database import SessionLocal
from app.model.csv import (
    CSVUpload,
    ReservationRaw,
    ChatWhatsappRaw,
    TransactionRestoRaw,
    ProfileGuestRaw,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)
_csv_scheduler: AsyncIOScheduler | None = None

@contextmanager
def _db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def _cleanup_csv_data_once():
    with _db_session() as db:
        deleted_res = db.execute(
            delete(ReservationRaw).where(ReservationRaw.deleted_at.isnot(None))
        ).rowcount

        deleted_guest = db.execute(
            delete(ProfileGuestRaw).where(ProfileGuestRaw.deleted_at.isnot(None))
        ).rowcount

        deleted_chat = db.execute(
            delete(ChatWhatsappRaw).where(ChatWhatsappRaw.deleted_at.isnot(None))
        ).rowcount

        deleted_resto = db.execute(
            delete(TransactionRestoRaw).where(TransactionRestoRaw.deleted_at.isnot(None))
        ).rowcount

        deleted_uploads = db.execute(
            delete(CSVUpload).where(CSVUpload.status == "DELETED")
        ).rowcount

        db.commit()

        logger.info(
            "[csv_cleanup] deleted %s reservation_raw rows, %s csv_upload records, %s profile_guest rows, %s chat_whatsapp rows, %s transaction_resto rows",
            deleted_res, deleted_uploads, deleted_guest, deleted_chat, deleted_resto
        )

def start_csv_cleanup_scheduler():
    global _csv_scheduler
    if _csv_scheduler and _csv_scheduler.running:
        logger.info("[csv_cleanup] scheduler already running")
        return

    _csv_scheduler = AsyncIOScheduler(timezone="UTC")
    _csv_scheduler.add_job(
        _cleanup_csv_data_once,
        trigger=IntervalTrigger(hours=settings.CSV_CLEANUP_INTERVAL_HOURS),
        id="csv_cleanup_job",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    _csv_scheduler.start()
    logger.info("[csv_cleanup] scheduler started (interval=%s hours)", settings.CSV_CLEANUP_INTERVAL_HOURS)

def stop_csv_cleanup_scheduler():
    global _csv_scheduler
    if not _csv_scheduler:
        return
    try:
        _csv_scheduler.shutdown(wait=False)
        logger.info("[csv_cleanup] scheduler stopped")
    finally:
        _csv_scheduler = None
