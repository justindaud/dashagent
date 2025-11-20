# app/jobs/cleanup_clickhouse.py
import logging

import requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config.settings import settings

logger = logging.getLogger(__name__)
_ch_scheduler: AsyncIOScheduler | None = None

CLICKHOUSE_TABLES = [
    "reservations_transformed",
    "profile_guest_transformed",
    "chat_whatsapp_transformed",
    "transaction_resto_transformed",
]

def _clickhouse_sql(sql: str) -> str:
    base_url = settings.clickhouse_base_url
    params = settings.clickhouse_default_params

    auth = None
    if settings.CLICKHOUSE_USER:
        auth = (settings.CLICKHOUSE_USER, settings.CLICKHOUSE_PASSWORD or "")

    logger.info("[clickhouse_cleanup] Executing SQL: %s", sql)
    resp = requests.post(
        base_url,
        params=params,
        data=sql.encode("utf-8"),
        auth=auth,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.text

async def _cleanup_clickhouse_once():
    logger.info(
        "[clickhouse_cleanup] running once (interval=%s hours, tables=%s)",
        settings.CLICKHOUSE_CLEANUP_INTERVAL_HOURS,
        ", ".join(CLICKHOUSE_TABLES),
    )

    for table in CLICKHOUSE_TABLES:
        sql = (
            f"ALTER TABLE {settings.CLICKHOUSE_DB}.{table} "
            f"DELETE WHERE deleted_at IS NOT NULL"
        )
        try:
            _clickhouse_sql(sql)
            logger.info(
                "[clickhouse_cleanup] ALTER DELETE scheduled for table %s", table
            )
        except Exception as e:
            logger.error(
                "[clickhouse_cleanup] error cleaning table %s: %s", table, e
            )

def start_clickhouse_cleanup_scheduler():
    global _ch_scheduler
    if _ch_scheduler and _ch_scheduler.running:
        logger.info("[clickhouse_cleanup] scheduler already running")
        return

    interval_hours = settings.CLICKHOUSE_CLEANUP_INTERVAL_HOURS

    _ch_scheduler = AsyncIOScheduler(timezone="UTC")
    _ch_scheduler.add_job(
        _cleanup_clickhouse_once,
        trigger=IntervalTrigger(hours=interval_hours),
        id="clickhouse_cleanup_job",
        max_instances=1,
        coalesce=True,
        replace_existing=True,
    )
    _ch_scheduler.start()
    logger.info(
        "[clickhouse_cleanup] scheduler started (interval=%s hours)",
        interval_hours,
    )

def stop_clickhouse_cleanup_scheduler():
    global _ch_scheduler
    if not _ch_scheduler:
        return
    try:
        _ch_scheduler.shutdown(wait=False)
        logger.info("[clickhouse_cleanup] scheduler stopped")
    finally:
        _ch_scheduler = None