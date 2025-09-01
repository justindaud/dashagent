from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db

from app.models import ProfileTamu, Reservasi, ChatWhatsapp, TransaksiResto, ProfileTamuProcessed, ReservasiProcessed, ChatWhatsappProcessed, TransaksiRestoProcessed
from sqlalchemy import func, and_
from datetime import datetime, timedelta

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get basic dashboard statistics"""
    try:
        # Count total records from Processed tables (single source of truth)
        total_guests = db.query(ProfileTamuProcessed).count()
        total_reservations = db.query(ReservasiProcessed).count()
        total_chats = db.query(ChatWhatsappProcessed).count()
        total_transactions = db.query(TransaksiRestoProcessed).count()
        
    return {
            "total_guests": total_guests,
            "total_reservations": total_reservations,
            "total_chats": total_chats,
            "total_transactions": total_transactions,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dashboard stats: {str(e)}")

@router.get("/recent-uploads")
async def get_recent_uploads(db: Session = Depends(get_db), limit: int = 10):
    """Get recent CSV uploads"""
    try:
        from app.models import CSVUpload
        
        recent_uploads = db.query(CSVUpload).order_by(CSVUpload.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": upload.id,
                "filename": upload.filename,
                "file_type": upload.file_type,
                "status": upload.status,
                "rows_processed": upload.rows_processed,
                "created_at": upload.created_at.isoformat()
            }
            for upload in recent_uploads
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recent uploads: {str(e)}")

@router.get("/data-preview/{data_type}")
async def get_data_preview(
    data_type: str, 
    db: Session = Depends(get_db), 
    limit: int = 5
):
    """Get preview of data for specific type"""
    try:
        if data_type == "guests":
            data = db.query(ProfileTamuProcessed).limit(limit).all()
            return [{"id": item.id, "name": item.name, "email": item.email} for item in data]
        elif data_type == "reservations":
            data = db.query(ReservasiProcessed).limit(limit).all()
            return [{"id": item.id, "guest_name": item.guest_name, "room_number": item.room_number} for item in data]
        elif data_type == "chats":
            data = db.query(ChatWhatsappProcessed).limit(limit).all()
            return [{"id": item.id, "phone_number": item.phone_number, "message": item.message[:50]} for item in data]
        elif data_type == "transactions":
            data = db.query(TransaksiRestoProcessed).limit(limit).all()
            return [{"id": item.id, "transaction_id": item.transaction_id, "total_amount": item.total_amount} for item in data]
        else:
            raise HTTPException(status_code=400, detail="Invalid data type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data preview: {str(e)}")

@router.delete("/upload/{upload_id}")
async def delete_csv_upload(upload_id: int, db: Session = Depends(get_db)):
    """Delete CSV upload and re-process Processed tables"""
    try:
        from app.models import CSVUpload
        
        # Get the upload record
        upload = db.query(CSVUpload).filter(CSVUpload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Delete the upload record (otomatis hapus semua data Raw karena cascade delete)
        db.delete(upload)
        db.commit()
        
        # Re-process Processed tables from remaining Raw data
        await reprocess_processed_tables(db)
        
        return {"message": f"Upload {upload_id} deleted successfully and Processed tables re-processed"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting upload: {str(e)}")

async def reprocess_processed_tables(db: Session):
    """Re-process Processed tables from remaining Raw data"""
    try:
        # Clear all Processed tables
        db.query(ProfileTamuProcessed).delete()
        db.query(ReservasiProcessed).delete()
        db.query(ChatWhatsappProcessed).delete()
        db.query(TransaksiRestoProcessed).delete()
        
        # Re-process ProfileTamuProcessed - ambil data terbaru per guest_id
        from sqlalchemy import text
        profile_query = text("""
            INSERT INTO profile_tamu_processed (guest_id, name, email, phone, address, birth_date, occupation, city, country, segment, type_id, id_no, sex, zip_code, local_region, telefax, mobile_no, comments, credit_limit, last_updated, last_upload_id)
            SELECT DISTINCT ON (guest_id) guest_id, name, email, phone, address, birth_date, occupation, city, country, segment, type_id, id_no, sex, zip_code, local_region, telefax, mobile_no, comments, credit_limit, NOW(), csv_upload_id
            FROM profile_tamu 
            ORDER BY guest_id, csv_upload_id DESC
        """)
        db.execute(profile_query)
        
        # Re-process ReservasiProcessed - ambil data terbaru per kombinasi arrival+depart+room
        reservasi_query = text("""
            INSERT INTO reservasi_processed (reservation_id, guest_id, guest_name, room_number, room_type, arrangement, in_house_date, arrival_date, depart_date, check_in_time, check_out_time, created_date, birth_date, age, member_no, member_type, email, mobile_phone, vip_status, room_rate, lodging, breakfast, lunch, dinner, other_charges, total_amount, bill_number, pay_article, rate_code, res_no, adult_count, child_count, compliment, nationality, local_region, company_ta, sob, nights, segment, created_by, k_card, remarks, last_updated, last_upload_id)
            SELECT DISTINCT ON (arrival_date, depart_date, room_number) reservation_id, guest_id, guest_name, room_number, room_type, arrangement, in_house_date, arrival_date, depart_date, check_in_time, check_out_time, created_date, birth_date, age, member_no, member_type, email, mobile_phone, vip_status, room_rate, lodging, breakfast, lunch, dinner, other_charges, total_amount, bill_number, pay_article, rate_code, res_no, adult_count, child_count, compliment, nationality, local_region, company_ta, sob, nights, segment, created_by, k_card, remarks, NOW(), csv_upload_id
            FROM reservasi 
            ORDER BY arrival_date, depart_date, room_number, csv_upload_id DESC
        """)
        db.execute(reservasi_query)
        
        # Re-process ChatWhatsappProcessed - ambil data terbaru per kombinasi phone+date+message
        chat_query = text("""
            INSERT INTO chat_whatsapp_processed (phone_number, message_type, message_date, message, last_updated, last_upload_id)
            SELECT DISTINCT ON (phone_number, message_date, message) phone_number, message_type, message_date, message, NOW(), csv_upload_id
            FROM chat_whatsapp 
            ORDER BY phone_number, message_date, message, csv_upload_id DESC
        """)
        db.execute(chat_query)
        
        # Re-process TransaksiRestoProcessed - ambil data terbaru per kombinasi transaction+guest+timestamp
        transaksi_query = text("""
            INSERT INTO transaksi_resto_processed (transaction_id, guest_id, item_name, quantity, price, total_amount, timestamp, last_updated, last_upload_id)
            SELECT DISTINCT ON (transaction_id, guest_id, timestamp) transaction_id, guest_id, item_name, quantity, price, total_amount, timestamp, NOW(), csv_upload_id
            FROM transaksi_resto 
            ORDER BY transaction_id, guest_id, timestamp, csv_upload_id DESC
        """)
        db.execute(transaksi_query)
        
        db.commit()
        print("Processed tables re-processed successfully using DISTINCT ON logic")
        
    except Exception as e:
        db.rollback()
        print(f"Error re-processing Processed tables: {str(e)}")
        raise
