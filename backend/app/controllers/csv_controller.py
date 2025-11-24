# app/controllers/csv_controller.py
import logging
import hashlib
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.model.user import User
from app.repositories import csv_repository as repo
from app.controllers.reservation_controller import parse_reservation_csv
from app.schemas.response import ApiResponse
from app.schemas.uploadcsv import UploadOut
from app.controllers.profile_guest_controller import parse_profile_guest_csv
from app.controllers.chat_whatsapp_controller import parse_chat_whatsapp_csv
from app.controllers.transaction_resto_controller import parse_transaction_resto_csv

logger = logging.getLogger(__name__)

async def upload_csv_file(db: Session, file: UploadFile, file_type: str, current_user: User) -> ApiResponse[UploadOut]:
    if not file_type:
        logger.info("file_type is missing")
        raise HTTPException(status_code=400, detail="file_type is required")

    supported_types = ["profile_guest", "reservation", "chat_whatsapp", "transaction_resto"]
    if file_type not in supported_types:
        logger.info(f"Handler not found for type: {file_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file_type. Supported types are: {supported_types}",
        )

    if not file.filename.lower().endswith(".csv"):
        logger.info(f"Invalid file extension: {file.filename}")
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")

    logger.info(f"Reading file: {file.filename}")
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="File is empty.")

    try:
        content_str = contents.decode("utf-8-sig")
        logger.info("Successfully decoded file content as UTF-8.")
    except UnicodeDecodeError as e:
        logger.info(f"File decoding failed for {file.filename}. Encoding is not UTF-8: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file encoding. Only UTF-8 encoded files are accepted. Error detail: {e}"
        )

    file_hash = hashlib.sha256(contents).hexdigest()
    logger.info(f"File hash calculated: {file_hash[:10]}...")

    new_upload = None
    try:
        new_upload = repo.create_upload_record(
            db=db,
            file_name=file.filename,
            file_type=file_type,
            user_id=current_user.user_id,
            file_hash=file_hash
        )
        logger.info(f"CSVUpload record created with ID: {new_upload.id}, status: PROCESSING")
    except IntegrityError as e:
        db.rollback()
        logger.info(f"Database IntegrityError on hash insert, likely race condition: {e}")
        raise HTTPException(
            status_code=409,
            detail="File content has just been uploaded by another process. Please try again."
        )
    except Exception as e:
         db.rollback()
         logger.info(f"Failed to create initial upload record: {e}")
         raise HTTPException(status_code=500, detail="Failed to create upload record in database.")

    try:
        if file_type == 'reservation':
            rows_to_add, count = await parse_reservation_csv(
                content_str,
                new_upload.id
            )

            if rows_to_add:
                repo.bulk_save_reservation_rows(db=db, rows=rows_to_add)

            repo.update_upload_status_success(
                db=db,
                upload=new_upload,
                row_count=count
            )
            db.commit()

        elif file_type == 'profile_guest':
            rows_to_add, count = await parse_profile_guest_csv(
                content_str,
                new_upload.id
            )
            if rows_to_add:
                repo.bulk_save_profile_guest_rows(db=db, rows=rows_to_add)

            repo.update_upload_status_success(
                db=db,
                upload=new_upload,
                row_count=count
            )
            db.commit()

        elif file_type == 'chat_whatsapp':
            rows_to_add, count = await parse_chat_whatsapp_csv(
                content_str,
                new_upload.id
            )
            if rows_to_add:
                repo.bulk_save_chat_whatsapp_rows(db=db, rows=rows_to_add)

            repo.update_upload_status_success(
                db=db,
                upload=new_upload,
                row_count=count
            )
            db.commit()

        elif file_type == 'transaction_resto':
            rows_to_add, count = await parse_transaction_resto_csv(
                content_str,
                new_upload.id
            )
            if rows_to_add:
                repo.bulk_save_transaction_resto_rows(db=db, rows=rows_to_add)
            
            repo.update_upload_status_success(
                db=db,
                upload=new_upload,
                row_count=count
            )
            db.commit()

        db.refresh(new_upload)
        new_upload.uploader = current_user

        return ApiResponse(
            code=201,
            messages="CSV uploaded and processed successfully",
            data=[new_upload]
        )

    except Exception as e:
        db.rollback()
        error_msg = str(e)
        logger.info(f"Error processing file for upload ID {new_upload.id}: {error_msg}")

        repo.update_upload_status_failure(
            db=db,
            upload=new_upload,
            error_message=error_msg
        )

        if isinstance(e, NotImplementedError):
            raise HTTPException(status_code=400, detail=error_msg)

        if isinstance(e, (HTTPException, ValueError)):
             status_code = e.status_code if isinstance(e, HTTPException) else 400
             raise HTTPException(status_code=status_code, detail=error_msg)

        raise HTTPException(status_code=500, detail=f"Internal server error: {error_msg}")

async def get_all_uploads(db: Session, current_user: User) -> ApiResponse[UploadOut]:
    uploads = repo.get_uploads_by_user(db=db, user_id=current_user.user_id)
    return ApiResponse(
        code=200,
        messages="CSV File Fetched Successfully",
        data=uploads
    )

async def get_upload_details(db: Session, upload_id: int, current_user: User) -> ApiResponse[UploadOut]:
    upload = repo.get_upload_by_id_and_user(
        db=db,
        upload_id=upload_id,
        user_id=current_user.user_id
    )
    if not upload:
        raise HTTPException(
            status_code=404,
            detail="CSV upload not found or you do not have permission to view it"
        )
    return ApiResponse(
        code=200,
        messages="CSV Upload Detail Fetched Successfully",
        data=[upload]
    )

async def delete_upload_file(db: Session, upload_id: int, current_user: User) -> ApiResponse[UploadOut]:
    upload = repo.get_upload_by_id_and_user(db=db, upload_id=upload_id, user_id=current_user.user_id)
    if not upload:
        raise HTTPException(status_code=404, detail="CSV upload not found or you do not have permission to delete it")

    if upload.status == "DELETED":
        return ApiResponse(code=200, messages="Upload already in DELETED status.", data=[upload])

    try:
        repo.mark_upload_deleted(db=db, upload=upload, deleted_by_user_id=current_user.user_id)

        counts = repo.soft_delete_all_children_by_upload(db=db, upload_id=upload.id)

        db.commit()
        db.refresh(upload)

        return ApiResponse(
            code=200,
            messages=(
                "File deleted (soft delete). "
                f"{counts['reservation_raw']} reservation, "
                f"{counts['profile_guest_raw']} profile guest, "
                f"{counts['chat_whatsapp_raw']} chat WA, "
                f"{counts['transaction_resto_raw']} transaction resto "
                f"deleted (total {counts['total']})."
            ),
            data=[upload]
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete upload: {e}")
