# app/repositories/csv_repository.py
import logging
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict
from app.model.csv import CSVUpload, ChatWhatsappRaw, ReservationRaw, ProfileGuestRaw, TransactionRestoRaw
from app.model.user import User 

logger = logging.getLogger(__name__)

def create_upload_record(db: Session, file_name: str, file_type: str, user_id: str, file_hash: str) -> CSVUpload:
    logger.info(f"Creating CSVUpload record for {file_name} by user {user_id}")
    new_upload = CSVUpload(
        filename=file_name,
        file_type=file_type,
        status="PROCESSING",
        rows_processed=0,
        uploaded_by=user_id,
        file_hash=file_hash
    )
    db.add(new_upload)
    db.commit() 
    db.refresh(new_upload)
    return new_upload

def bulk_save_reservation_rows(db: Session, rows: List[ReservationRaw]):
    if not rows:
        return
    logger.info(f"Bulk saving {len(rows)} ReservationRaw records...")
    db.bulk_save_objects(rows)

def bulk_save_profile_guest_rows(db: Session, rows: List[ProfileGuestRaw]):
    if not rows:
        return
    logger.info(f"Bulk saving {len(rows)} ProfileGuestRaw records...")
    db.bulk_save_objects(rows)

def bulk_save_chat_whatsapp_rows(db: Session, rows: List[ChatWhatsappRaw]):
    if not rows:
        return
    logger.info(f"Bulk saving {len(rows)} ChatWhatsappRaw records...")
    db.bulk_save_objects(rows)

def bulk_save_transaction_resto_rows(db: Session, rows: List[TransactionRestoRaw]):
    if not rows:
        return
    logger.info(f"Bulk saving {len(rows)} TransactionRestoRaw records...")
    db.bulk_save_objects(rows)

def update_upload_status_success(
    db: Session, 
    upload: CSVUpload, 
    row_count: int
):
    logger.info(f"Updating upload {upload.id} to COMPLETED with {row_count} rows")
    upload.status = "COMPLETED"
    upload.rows_processed = row_count
    upload.error_message = None
    db.commit()

def update_upload_status_failure(
    db: Session, 
    upload: CSVUpload, 
    error_message: str
):
    logger.warning(f"Updating upload {upload.id} to FAILED. Error: {error_message}")
    upload.status = "FAILED"
    upload.error_message = error_message
    db.commit()

def get_uploads_by_user(db: Session, user_id: str) -> List[CSVUpload]:
    logger.debug(f"Fetching all uploads for user {user_id}")
    return (
        db.query(CSVUpload)
        .options(
            joinedload(CSVUpload.uploader),
            joinedload(CSVUpload.deleter),
        )
        .filter(CSVUpload.uploaded_by == user_id)
        .order_by(CSVUpload.created_at.desc())
        .all()
    )

def get_upload_by_id_and_user(db: Session, upload_id: int, user_id: str) -> CSVUpload:
    logger.debug(f"Fetching upload {upload_id} for user {user_id}")
    return (
        db.query(CSVUpload)
        .options(
            joinedload(CSVUpload.uploader),
            joinedload(CSVUpload.deleter),
        )
        .filter(CSVUpload.id == upload_id, CSVUpload.uploaded_by == user_id)
        .first()
    )

def mark_upload_deleted(db: Session, upload: CSVUpload, deleted_by_user_id: str):
    logger.info(f"Marking upload {upload.id} as DELETED by {deleted_by_user_id}")
    upload.status = "DELETED"
    upload.deleted_at = func.now()
    upload.deleted_by = deleted_by_user_id
    db.flush()

def soft_delete_reservations_by_upload(db: Session, upload_id: int) -> int:
    logger.info(f"Soft deleting reservation_raw for upload_id={upload_id}")
    q = db.query(ReservationRaw).filter(ReservationRaw.csv_upload_id == upload_id)
    affected = q.update(
        {ReservationRaw.deleted_at: func.now()},
        synchronize_session=False
    )
    logger.info(f"Affected rows in reservation_raw: {affected}")
    return affected

def soft_delete_profile_guest_by_upload(db: Session, upload_id: int) -> int:
    logger.info(f"Soft deleting profile_guest_raw for upload_id={upload_id}")
    q = db.query(ProfileGuestRaw).filter(
        ProfileGuestRaw.csv_upload_id == upload_id,
        ProfileGuestRaw.deleted_at.is_(None)
    )
    affected = q.update({ProfileGuestRaw.deleted_at: func.now()}, synchronize_session=False)
    logger.info(f"Affected rows in profile_guest_raw: {affected}")
    return affected

def soft_delete_chat_whatsapp_by_upload(db: Session, upload_id: int) -> int:
    logger.info(f"Soft deleting chat_whatsapp_raw for upload_id={upload_id}")
    q = db.query(ChatWhatsappRaw).filter(
        ChatWhatsappRaw.csv_upload_id == upload_id,
        ChatWhatsappRaw.deleted_at.is_(None)
    )
    affected = q.update({ChatWhatsappRaw.deleted_at: func.now()}, synchronize_session=False)
    logger.info(f"Affected rows in chat_whatsapp_raw: {affected}")
    return affected

def soft_delete_transaction_resto_by_upload(db: Session, upload_id: int) -> int:
    logger.info(f"Soft deleting transaction_resto_raw for upload_id={upload_id}")
    q = db.query(TransactionRestoRaw).filter(
        TransactionRestoRaw.csv_upload_id == upload_id,
        TransactionRestoRaw.deleted_at.is_(None)
    )
    affected = q.update({TransactionRestoRaw.deleted_at: func.now()}, synchronize_session=False)
    logger.info(f"Affected rows in transaction_resto_raw: {affected}")
    return affected

def soft_delete_all_children_by_upload(db: Session, upload_id: int) -> Dict[str, int]:
    res_count  = soft_delete_reservations_by_upload(db, upload_id)
    prof_count = soft_delete_profile_guest_by_upload(db, upload_id)
    wa_count   = soft_delete_chat_whatsapp_by_upload(db, upload_id)
    resto_count= soft_delete_transaction_resto_by_upload(db, upload_id)
    return {
        "reservation_raw": res_count,
        "profile_guest_raw": prof_count,
        "chat_whatsapp_raw": wa_count,
        "transaction_resto_raw": resto_count,
        "total": res_count + prof_count + wa_count + resto_count,
    }