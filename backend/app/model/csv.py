# app/model/csv.py
from sqlalchemy.sql import func
from sqlalchemy import BigInteger, Column, Date, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from sqlalchemy.dialects import postgresql

DT_TZ_MS = postgresql.TIMESTAMP(timezone=True, precision=3)
JKT = ZoneInfo("Asia/Jakarta")

def now_jkt():
    return datetime.now(JKT)

def now_utc():
    return datetime.now(timezone.utc)

class CSVUpload(Base):
    __tablename__ = "csv_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_hash = Column(String(64), nullable=False, index=True) 
    status = Column(String(50), default="PROCESSING", nullable=False)
    rows_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    uploaded_by = Column(String(36), ForeignKey("users.user_id"), nullable=False, index=True)
    deleted_by = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    created_at = Column(DT_TZ_MS, default=now_jkt)
    deleted_at = Column(DT_TZ_MS, nullable=True, onupdate=now_jkt)
    uploader = relationship("User", foreign_keys=[uploaded_by])
    deleter  = relationship("User", foreign_keys=[deleted_by])
    
    reservation_raw_data = relationship("ReservationRaw", back_populates="csv_upload", cascade="all, delete-orphan")
    profile_guest_raw_data = relationship("ProfileGuestRaw", back_populates="csv_upload", cascade="all, delete-orphan")
    chat_whatsapp_raw_data = relationship("ChatWhatsappRaw", back_populates="csv_upload", cascade="all, delete-orphan")
    transaction_resto_raw_data = relationship("TransactionRestoRaw", back_populates="csv_upload", cascade="all, delete-orphan")

    __table_args__ = (
        Index(
            'uq_file_hash_completed_or_processing',
            'file_hash',
            unique=True,
            postgresql_where=(Column('status').in_(['COMPLETED', 'PROCESSING']))
        ),
    )

class ReservationRaw(Base):
    __tablename__ = "reservation_raw"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_upload_id = Column(Integer, ForeignKey("csv_uploads.id", ondelete="CASCADE"), nullable=False, index=True)

    reservation_id = Column(Integer, index=True)
    guest_id = Column(String(50), index=True)
    first_name = Column(String(255))
    last_name = Column(String(255))
    room_number = Column(String(50))
    room_type = Column(String(50))
    arrangement = Column(String(50))
    in_house_date = Column(String(50))
    arrival_date = Column(DT_TZ_MS, default=now_jkt)
    depart_date = Column(DT_TZ_MS, default=now_jkt)
    check_in_time = Column(String(50))
    check_out_time = Column(String(50))
    created_date = Column(String(50))
    birth_date = Column(String(50))
    age = Column(Integer)
    member_no = Column(String(50))
    member_type = Column(String(50))
    email = Column(String(100))
    mobile_phone = Column(String(50))
    vip_status = Column(String(50))
    room_rate = Column(Float)
    lodging = Column(Float)
    breakfast = Column(Float)
    lunch = Column(Float)
    dinner = Column(Float)
    other_charges = Column(Float)
    bill_number = Column(String(50))
    pay_article = Column(String(50))
    rate_code = Column(String(50))
    adult_count = Column(Integer)
    child_count = Column(Integer)
    compliment = Column(String(50))
    nationality = Column(String(50))
    local_region = Column(String(100))
    company_ta = Column(String(100))
    sob = Column(String(50))
    nights = Column(Integer)
    segment = Column(String(50))
    created_by = Column(String(50))
    k_card = Column(String(50))
    remarks = Column(Text)

    created_at = Column(DT_TZ_MS, default=now_jkt)
    deleted_at = Column(DT_TZ_MS, onupdate=now_jkt)
    csv_upload = relationship("CSVUpload", back_populates="reservation_raw_data")

class ProfileGuestRaw(Base):
    __tablename__ = "profile_guest_raw"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_upload_id = Column(Integer, ForeignKey("csv_uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    guest_id = Column(String(50), index=True)
    name = Column(String(255))
    email = Column(String(100))
    phone = Column(String(100))
    address = Column(Text)
    birth_date = Column(String(50))
    occupation = Column(String(100))
    city = Column(String(100))
    country = Column(String(100))
    segment = Column(String(100))
    type_id = Column(String(100))
    id_no = Column(String(100))
    sex = Column(String(100))
    zip_code = Column(String(100))
    local_region = Column(String(100))
    telefax = Column(String(100))
    mobile_no = Column(String(100))
    comments = Column(Text)
    credit_limit = Column(String(50))

    created_at = Column(DT_TZ_MS, default=now_jkt)
    deleted_at = Column(DT_TZ_MS, onupdate=now_jkt)
    csv_upload = relationship("CSVUpload", back_populates="profile_guest_raw_data")

class ChatWhatsappRaw(Base):
    __tablename__ = "chat_whatsapp_raw"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_upload_id = Column(Integer, ForeignKey("csv_uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    phone_number = Column(String(100), index=True)
    message_type = Column(String(100))
    message_date = Column(DT_TZ_MS)
    message = Column(Text)

    created_at = Column(DT_TZ_MS, default=now_jkt)
    deleted_at = Column(DT_TZ_MS, onupdate=now_jkt)
    csv_upload = relationship("CSVUpload", back_populates="chat_whatsapp_raw_data")

class TransactionRestoRaw(Base):
    __tablename__ = "transaction_resto_raw"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_upload_id = Column(Integer, ForeignKey("csv_uploads.id", ondelete="CASCADE"), nullable=False, index=True)
    bill_number = Column(String(50), index=True)
    article_number = Column(String(50))
    guest_name = Column(String(255), index=True)
    item_name = Column(String(255)) 
    quantity = Column(Integer)
    sales = Column(Integer)
    payment = Column(Integer)
    article_category = Column(String(100))
    article_subcategory = Column(String(100))
    outlet = Column(String(50))
    table_number = Column(Integer)
    posting_id = Column(String(50))
    reservation_number = Column(String(50))
    travel_agent_name = Column(String(255))
    prev_bill_number = Column(String(50))
    transaction_date = Column(DT_TZ_MS)
    start_time = Column(String(20))
    close_time = Column(String(20))
    time = Column(String(20))
    bill_discount = Column(Float)
    bill_compliment = Column(Float)
    total_deduction = Column(Float)

    created_at = Column(DT_TZ_MS, default=now_jkt)
    deleted_at = Column(DT_TZ_MS, onupdate=now_jkt)
    csv_upload = relationship("CSVUpload", back_populates="transaction_resto_raw_data")