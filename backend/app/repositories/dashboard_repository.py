# app/repositories/dashboard_repository.py
import logging
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.model.csv import (
    CSVUpload,
    ProfileGuestRaw,
    ReservationRaw,
    ChatWhatsappRaw,
    TransactionRestoRaw,
)

logger = logging.getLogger(__name__)

def execute_clickhouse_query(db: Session, sql: str) -> Dict[str, Any] | str:
    clean_sql = sql.strip().rstrip(";")
    upper = clean_sql.upper()

    is_select = upper.startswith("SELECT") or upper.startswith("WITH")

    logger.info("[clickhouse_query] Executing SQL: %s", clean_sql)

    try:
        result = db.execute(text(clean_sql))

        if is_select:
            rows = result.mappings().all()
            data = [dict(row) for row in rows]
            return {"data": data}

        return "OK"

    except Exception as e:
        logger.error("[clickhouse_query] Error executing query '%s': %s", clean_sql, e, exc_info=True)
        raise


def _parse_ch_count(result: dict) -> int:
    try:
        if isinstance(result, dict) and "data" in result and len(result["data"]) > 0:
            data_row = result["data"][0]
            count_key = next(iter(data_row))
            return int(data_row[count_key])

        logger.warning("[dashboard_stats] Result of count query: %s", result)
        return 0
    except Exception as e:
        logger.error("[dashboard_stats] Failed to parse ClickHouse count result: %s", e, exc_info=True)
        return 0


def _parse_ch_max_date(result: dict, column_name: str) -> Optional[str]:
    try:
        if isinstance(result, dict) and "data" in result and len(result["data"]) > 0:
            date_str = result["data"][0].get(column_name)

            if date_str:
                return str(date_str).split(" ")[0]

        logger.warning("[dashboard_stats] Result of max_date query: %s", result)
        return None
    except Exception as e:
        logger.error("[dashboard_stats] Failed to parse ClickHouse max_date result: %s", e, exc_info=True)
        return None


def _parse_ch_max_timestamp(result: dict, column_name: str) -> Optional[str]:
    try:
        if isinstance(result, dict) and "data" in result and len(result["data"]) > 0:
            ts_str = result["data"][0].get(column_name)

            if ts_str:
                return str(ts_str)

        logger.warning("[dashboard_stats] Result of max_timestamp query: %s", result)
        return None
    except Exception as e:
        logger.error("[dashboard_stats] Failed to parse ClickHouse max_timestamp result: %s", e, exc_info=True)
        return None


def get_dashboard_stats_repo(db: Session) -> Dict[str, Any]:
    ch_guest_res = execute_clickhouse_query(
        db,
        "SELECT count(*) FROM default.datamart_profile_guest",
    )
    ch_reserv_res = execute_clickhouse_query(
        db,
        "SELECT count(*) FROM default.datamart_reservations",
    )
    ch_chat_res = execute_clickhouse_query(
        db,
        "SELECT count(*) FROM default.datamart_chat_whatsapp",
    )
    ch_trans_res = execute_clickhouse_query(
        db,
        "SELECT count(*) FROM default.datamart_transaction_resto",
    )
    ch_max_depart_res = execute_clickhouse_query(
        db,
        "SELECT max(depart_date) as max_date FROM default.datamart_reservations",
    )
    ch_last_updated_res = execute_clickhouse_query(
        db,
        "SELECT toTimeZone(MAX(ingested_at), 'Asia/Jakarta') as max_ingested_at "
        "FROM default.datamart_reservations",
    )

    total_guests = _parse_ch_count(ch_guest_res)
    total_reservations = _parse_ch_count(ch_reserv_res)
    total_chats = _parse_ch_count(ch_chat_res)
    total_transactions = _parse_ch_count(ch_trans_res)

    latest_depart_str = _parse_ch_max_date(ch_max_depart_res, "max_date")
    last_updated_str = _parse_ch_max_timestamp(ch_last_updated_res, "max_ingested_at")

    return {
        "total_guests": total_guests,
        "total_reservations": total_reservations,
        "total_chats": total_chats,
        "total_transactions": total_transactions,
        "latest_depart_date": latest_depart_str,
        "last_updated": last_updated_str,
    }

def get_recent_uploads_repo(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    recent_uploads = (
        db.query(CSVUpload)
        .order_by(CSVUpload.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": upload.id,
            "filename": upload.filename,
            "file_type": upload.file_type,
            "status": upload.status,
            "rows_processed": upload.rows_processed,
            "created_at": upload.created_at,
        }
        for upload in recent_uploads
    ]


def get_data_preview_repo(
    db: Session,
    data_type: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:
    if data_type == "profile_guest":
        data = db.query(ProfileGuestRaw).limit(limit).all()
        return [
            {
                "id": item.id,
                "name": item.name,
                "email": item.email,
            }
            for item in data
        ]

    if data_type == "reservation":
        data = db.query(ReservationRaw).limit(limit).all()
        return [
            {
                "id": item.id,
                "guest_name": item.first_name + " " + item.last_name,
                "room_number": item.room_number,
            }
            for item in data
        ]

    if data_type == "chat_whatsapp":
        data = db.query(ChatWhatsappRaw).limit(limit).all()
        return [
            {
                "id": item.id,
                "phone_number": item.phone_number,
                "message": (item.message or "")[:50],
            }
            for item in data
        ]

    if data_type == "transaction_resto":
        data = db.query(TransactionRestoRaw).limit(limit).all()
        return [
            {
                "id": item.id,
                "bill_number": item.bill_number,
                "guest_name": item.guest_name,
                "sales": item.sales,
            }
            for item in data
        ]

    raise ValueError("Invalid data type")