from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db

from app.models import ProfileTamu, Reservasi, ChatWhatsapp, TransaksiResto, ProfileTamuProcessed, ReservasiProcessed, ChatWhatsappProcessed, TransaksiRestoProcessed
from sqlalchemy import func, cast, Date, and_
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
        
        # Get latest depart_date for default date range
        latest_depart = (
                db.query(func.max(cast(ReservasiProcessed.depart_date, Date)))
                .scalar()
            )
        latest_depart_str = latest_depart.strftime('%Y-%m-%d') if latest_depart else None
        
        return {
            "total_guests": total_guests,
            "total_reservations": total_reservations,
            "total_chats": total_chats,
            "total_transactions": total_transactions,
            "latest_depart_date": latest_depart_str,
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
            return [{"id": item.id, "bill_number": item.bill_number, "guest_name": item.guest_name, "sales": item.sales} for item in data]
        else:
            raise HTTPException(status_code=400, detail="Invalid data type")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data preview: {str(e)}")

@router.delete("/upload/{upload_id}")
async def delete_csv_upload(upload_id: int, db: Session = Depends(get_db)):
    """Delete CSV upload and rollback affected Processed data"""
    try:
        from app.models import CSVUpload
        
        # Get the upload record
        upload = db.query(CSVUpload).filter(CSVUpload.id == upload_id).first()
        if not upload:
            raise HTTPException(status_code=404, detail="Upload not found")
        
        # Step 1: Rollback affected ProfileTamuProcessed records
        affected_profiles = db.query(ProfileTamuProcessed).filter(
            ProfileTamuProcessed.last_upload_id == upload_id
        ).all()
        
        profiles_rolled_back = 0
        profiles_deleted = 0
        
        for profile in affected_profiles:
            # Find previous version from Raw data
            previous_profile = db.query(ProfileTamu).filter(
                ProfileTamu.guest_id == profile.guest_id,
                ProfileTamu.csv_upload_id != upload_id
            ).order_by(ProfileTamu.csv_upload_id.desc()).first()
            
            if previous_profile:
                # Rollback to previous state
                profile.name = previous_profile.name
                profile.email = previous_profile.email
                profile.phone = previous_profile.phone
                profile.address = previous_profile.address
                profile.birth_date = previous_profile.birth_date
                profile.occupation = previous_profile.occupation
                profile.city = previous_profile.city
                profile.country = previous_profile.country
                profile.segment = previous_profile.segment
                profile.type_id = previous_profile.type_id
                profile.id_no = previous_profile.id_no
                profile.sex = previous_profile.sex
                profile.zip_code = previous_profile.zip_code
                profile.local_region = previous_profile.local_region
                profile.telefax = previous_profile.telefax
                profile.mobile_no = previous_profile.mobile_no
                profile.comments = previous_profile.comments
                profile.credit_limit = previous_profile.credit_limit
                profile.last_upload_id = previous_profile.csv_upload_id
                profile.last_updated = func.now()
                profiles_rolled_back += 1
                print(f"Rolled back profile: {profile.guest_id} to upload {previous_profile.csv_upload_id}")
            else:
                # No previous data, delete this processed record
                db.delete(profile)
                profiles_deleted += 1
                print(f"Deleted profile: {profile.guest_id} (no previous data)")
        
        # Step 2: Rollback affected ReservasiProcessed records
        affected_reservations = db.query(ReservasiProcessed).filter(
            ReservasiProcessed.last_upload_id == upload_id
        ).all()
        
        reservations_rolled_back = 0
        reservations_deleted = 0
        
        for reservation in affected_reservations:
            # Find previous version from Raw data
            previous_reservation = db.query(Reservasi).filter(
                Reservasi.arrival_date == reservation.arrival_date,
                Reservasi.depart_date == reservation.depart_date,
                Reservasi.room_number == reservation.room_number,
                Reservasi.csv_upload_id != upload_id
            ).order_by(Reservasi.csv_upload_id.desc()).first()
            
            if previous_reservation:
                # Rollback to previous state
                reservation.reservation_id = previous_reservation.reservation_id
                reservation.guest_id = previous_reservation.guest_id
                reservation.guest_name = previous_reservation.guest_name
                reservation.room_number = previous_reservation.room_number
                reservation.room_type = previous_reservation.room_type
                reservation.arrangement = previous_reservation.arrangement
                reservation.in_house_date = previous_reservation.in_house_date
                reservation.arrival_date = previous_reservation.arrival_date
                reservation.depart_date = previous_reservation.depart_date
                reservation.check_in_time = previous_reservation.check_in_time
                reservation.check_out_time = previous_reservation.check_out_time
                reservation.created_date = previous_reservation.created_date
                reservation.birth_date = previous_reservation.birth_date
                reservation.age = previous_reservation.age
                reservation.member_no = previous_reservation.member_no
                reservation.member_type = previous_reservation.member_type
                reservation.email = previous_reservation.email
                reservation.mobile_phone = previous_reservation.mobile_phone
                reservation.vip_status = previous_reservation.vip_status
                reservation.room_rate = previous_reservation.room_rate
                reservation.lodging = previous_reservation.lodging
                reservation.breakfast = previous_reservation.breakfast
                reservation.lunch = previous_reservation.lunch
                reservation.dinner = previous_reservation.dinner
                reservation.other_charges = previous_reservation.other_charges
                reservation.total_amount = previous_reservation.total_amount
                reservation.bill_number = previous_reservation.bill_number
                reservation.pay_article = previous_reservation.pay_article
                reservation.rate_code = previous_reservation.rate_code
                reservation.res_no = previous_reservation.res_no
                reservation.adult_count = previous_reservation.adult_count
                reservation.child_count = previous_reservation.child_count
                reservation.compliment = previous_reservation.compliment
                reservation.nationality = previous_reservation.nationality
                reservation.local_region = previous_reservation.local_region
                reservation.company_ta = previous_reservation.company_ta
                reservation.sob = previous_reservation.sob
                reservation.nights = previous_reservation.nights
                reservation.segment = previous_reservation.segment
                reservation.created_by = previous_reservation.created_by
                reservation.k_card = previous_reservation.k_card
                reservation.remarks = previous_reservation.remarks
                reservation.last_upload_id = previous_reservation.csv_upload_id
                reservation.last_updated = func.now()
                reservations_rolled_back += 1
                print(f"Rolled back reservation: {reservation.arrival_date} - {reservation.depart_date} - Room {reservation.room_number}")
            else:
                # No previous data, delete this processed record
                db.delete(reservation)
                reservations_deleted += 1
                print(f"Deleted reservation: {reservation.arrival_date} - {reservation.depart_date} - Room {reservation.room_number} (no previous data)")
        
        # Step 3: Delete Raw data from this upload
        db.query(ProfileTamu).filter(ProfileTamu.csv_upload_id == upload_id).delete()
        db.query(Reservasi).filter(Reservasi.csv_upload_id == upload_id).delete()
        db.query(ChatWhatsapp).filter(ChatWhatsapp.csv_upload_id == upload_id).delete()
        db.query(TransaksiResto).filter(TransaksiResto.csv_upload_id == upload_id).delete()
        
        # Step 4: Delete the upload record
        db.delete(upload)
        db.commit()
        
        return {
            "message": f"Upload {upload_id} deleted successfully",
            "details": {
                "profiles_rolled_back": profiles_rolled_back,
                "profiles_deleted": profiles_deleted,
                "reservations_rolled_back": reservations_rolled_back,
                "reservations_deleted": reservations_deleted
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting upload: {str(e)}")
