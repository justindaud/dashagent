# app/routers/csv_routes.py
import logging
from typing import List

from app.db.database import get_db
from app.model.user import User
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app.middlewares.middleware import get_current_user

from app.schemas.uploadcsv import UploadOut
from app.schemas.response import ApiResponse

from app.controllers import csv_controller as controller

router = APIRouter(prefix="/csv", tags=["csv"])

logger = logging.getLogger(__name__)

@router.get("/")
async def get_csv_info():
    return {
        "message": "CSV Upload System",
        "endpoints": {
            "upload": "POST /csv/upload",
            "list_uploads": "GET /csv/uploads",
            "get_upload": "GET /csv/uploads/{upload_id}",
            "supported_types": "GET /csv/types",
            "delete_upload": "DELETE /csv/uploads/{upload_id}",
        },
        "supported_types": ["profile_guest", "reservation", "chat_whatsapp", "transaction_resto"],
    }

@router.post("/upload", response_model=ApiResponse[UploadOut], status_code=201)
async def upload_csv(file: UploadFile = File(...), file_type: str = Form(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user) ):
    return await controller.upload_csv_file(
        db=db,
        file=file,
        file_type=file_type,
        current_user=current_user
    )

@router.get("/uploads", response_model=ApiResponse[UploadOut])
async def get_csv_uploads(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await controller.get_all_uploads(
        db=db, 
        current_user=current_user
    )

@router.get("/uploads/{upload_id}", response_model=ApiResponse[UploadOut])
async def get_csv_upload(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await controller.get_upload_details(
        db=db,
        upload_id=upload_id,
        current_user=current_user
    )

@router.delete("/uploads/{upload_id}", response_model=ApiResponse[UploadOut])
async def delete_csv_upload(upload_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await controller.delete_upload_file(
        db=db,
        upload_id=upload_id,
        current_user=current_user
    )

@router.get("/types")
async def get_supported_types():
    return {
        "supported_types": ["profile_guest", "reservation", "chat_whatsapp", "transaction_resto"],
        "descriptions": {
            "profile_guest": "Guest profile data with names, phones, emails, addresses",
            "reservation": "Hotel reservation data with dates, rooms, guests",
            "chat_whatsapp": "WhatsApp chat data with messages and timestamps",
            "transaction_resto": "Restaurant transaction data with items, prices, and timestamps"
        },
    }