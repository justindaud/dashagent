# from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
# from sqlalchemy.orm import Session
# from app.db.database import get_db
# from app.csv_handlers import get_csv_handler
# from app.model.models import CSVUpload
# from typing import List
# import logging

# from app.middlewares.middleware import get_current_user
# from app.model.user import User

# router = APIRouter(prefix="/csv", tags=["csv"])

# logger = logging.getLogger(__name__)

# @router.get("/")
# async def get_csv_info():
#     """Get CSV upload system information"""
#     return {
#         "message": "CSV Upload System",
#         "endpoints": {
#             "upload": "POST /csv/upload",
#             "list_uploads": "GET /csv/uploads", 
#             "get_upload": "GET /csv/uploads/{upload_id}",
#             "supported_types": "GET /csv/types"
#         },
#         "supported_types": [
#             "profile_tamu",
#             "reservasi", 
#             "chat_whatsapp",
#             "transaksi_resto"
#         ]
#     }

# @router.post("/upload")
# async def upload_csv(
#     file: UploadFile = File(...),
#     file_type: str = Form(None),
#     db: Session = Depends(get_db),
#     current_user: User = Depends(get_current_user)
# ):
#     """
#     Upload CSV file for processing
    
#     file_type options:
#     - profile_tamu: Guest profile data
#     - reservasi: Reservation data  
#     - chat_whatsapp: WhatsApp chat data
#     """
#     try:
#         logger.info(f"Upload request received: filename={file.filename}, file_type={file_type}")
#         logger.info(f"Request headers: {file.headers}")
#         logger.info(f"Request form data: file_type={file_type}")
        
#         # Validate file type
#         if not file_type:
#             logger.error("file_type is missing")
#             raise HTTPException(status_code=400, detail="file_type is required")
        
#         # Validate file extension
#         if not file.filename.lower().endswith('.csv'):
#             logger.error(f"Invalid file extension: {file.filename}")
#             raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
#         # Get appropriate handler
#         try:
#             handler = get_csv_handler(file_type)
#             logger.info(f"Handler found for type: {file_type}")
#         except ValueError as e:
#             logger.error(f"Handler not found for type: {file_type}")
#             raise HTTPException(status_code=400, detail=str(e))
        
#         # Process CSV with handler
#         logger.info(f"Processing CSV with handler: {type(handler).__name__}")
#         result = await handler.process_csv(file, db, user_id=str(current_user.user_id))
#         # result = await handler.process_csv(file, db, uploaded_by=str(current_user.user_id))
        
#         logger.info(f"CSV uploaded successfully: {file.filename}, type: {file_type}, rows: {result['rows_processed']}")
        
#         return {
#             "message": "CSV uploaded and processed successfully",
#             "filename": file.filename,
#             "file_type": file_type,
#             "upload_id": result["upload_id"],
#             "rows_processed": result["rows_processed"]
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error uploading CSV: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# @router.get("/uploads")
# async def get_csv_uploads(db: Session = Depends(get_db)):
#     """Get list of all CSV uploads"""
#     try:
#         uploads = db.query(CSVUpload).order_by(CSVUpload.created_at.desc()).all()
#         return {
#             "uploads": [
#                 {
#                     "id": upload.id,
#                     "filename": upload.filename,
#                     "file_type": upload.file_type,
#                     "status": upload.status,
#                     "rows_processed": upload.rows_processed,
#                     "error_message": upload.error_message,
#                     "created_at": upload.created_at
#                 }
#                 for upload in uploads
#             ]
#         }
#     except Exception as e:
#         logger.error(f"Error fetching CSV uploads: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# @router.get("/uploads/{upload_id}")
# async def get_csv_upload(upload_id: int, db: Session = Depends(get_db)):
#     """Get specific CSV upload details"""
#     try:
#         upload = db.query(CSVUpload).filter(CSVUpload.id == upload_id).first()
#         if not upload:
#             raise HTTPException(status_code=404, detail="CSV upload not found")
        
#         return {
#             "id": upload.id,
#             "filename": upload.filename,
#             "file_type": upload.file_type,
#             "status": upload.status,
#             "rows_processed": upload.rows_processed,
#             "error_message": upload.error_message,
#             "created_at": upload.created_at
#         }
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error fetching CSV upload {upload_id}: {str(e)}")
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# @router.get("/types")
# async def get_supported_types():
#     """Get list of supported CSV file types"""
#     return {
#         "supported_types": [
#             "profile_tamu",
#             "reservasi", 
#             "chat_whatsapp"
#         ],
#         "descriptions": {
#             "profile_tamu": "Guest profile data with names, phones, emails, addresses",
#             "reservasi": "Hotel reservation data with dates, rooms, guests",
#             "chat_whatsapp": "WhatsApp chat data with messages and timestamps"
#         }
#     }