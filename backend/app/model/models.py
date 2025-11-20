from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, Float, UniqueConstraint, Computed
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import text
from app.db.database import Base

class CSVUpload(Base):
    __tablename__ = "csv_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # profile_tamu, reservasi, etc
    uploaded_by = Column(String(36), ForeignKey("users.user_id"))
    status = Column(String(20), default="processing")  # processing, completed, failed
    rows_processed = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("User")
    
    # Cascade delete relationships
    profile_tamu = relationship("ProfileTamu", back_populates="csv_upload", cascade="all, delete-orphan")
    reservasi = relationship("Reservasi", back_populates="csv_upload", cascade="all, delete-orphan")
    chat_whatsapp = relationship("ChatWhatsapp", back_populates="csv_upload", cascade="all, delete-orphan")
    transaksi_resto = relationship("TransaksiResto", back_populates="csv_upload", cascade="all, delete-orphan")


class ProfileTamu(Base):
    __tablename__ = "profile_tamu"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_upload_id = Column(Integer, ForeignKey("csv_uploads.id"))
    guest_id = Column(String(50), index=True)
    name = Column(String(255))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)

    birth_date = Column(String(20))  # YYYY-MM-DD format
    occupation = Column(String(100))
    city = Column(String(100))
    country = Column(String(100))
    segment = Column(String(50))
    type_id = Column(String(50))  # KTP, Passport, etc.
    id_no = Column(String(100))
    sex = Column(String(20))
    zip_code = Column(String(20))
    local_region = Column(String(100))
    telefax = Column(String(20))
    mobile_no = Column(String(20))
    comments = Column(Text)
    credit_limit = Column(String(50))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    csv_upload = relationship("CSVUpload", back_populates="profile_tamu")
    
    # Unique constraint untuk mencegah duplicate
    __table_args__ = (
        # Composite unique key: guest_id + phone
        # Jika ada guest_id + phone yang sama, akan dianggap duplicate
    )


class Reservasi(Base):
    __tablename__ = "reservasi"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_upload_id = Column(Integer, ForeignKey("csv_uploads.id"))
    
    # Basic reservation info
    reservation_id = Column(String(50), index=True)  # Number from CSV
    guest_id = Column(String(50), index=True)       # Guest No from CSV
    guest_name = Column(String(255))                # Combined First Name + Last Name
    room_number = Column(String(50))                # Room Number from CSV
    room_type = Column(String(50))                  # Room Type from CSV
    arrangement = Column(String(50))                # Arrangement from CSV
    
    # Dates and times
    in_house_date = Column(String(20))              # In House Date from CSV
    arrival_date = Column(String(20))               # Arrival from CSV | YYYY-MM-DD format
    depart_date = Column(String(20))                # Depart from CSV | YYYY-MM-DD format
    check_in_time = Column(String(20))              # C/I Time from CSV
    check_out_time = Column(String(20))             # C/O Time from CSV
    created_date = Column(String(20))               # Created from CSV
    
    # Guest details
    birth_date = Column(String(20))                 # Birth Date from CSV | YYYY-MM-DD format
    age = Column(Integer)                           # Age from CSV
    member_no = Column(String(50))                  # Member No from CSV
    member_type = Column(String(50))                # Member Type from CSV
    email = Column(String(100))                     # Email from CSV
    mobile_phone = Column(String(20))               # Mobile Phone from CSV
    vip_status = Column(String(10))                 # VIP from CSV
    
    # Financial info
    room_rate = Column(Float)                       # Room Rate from CSV
    lodging = Column(Float)                         # Lodging from CSV
    breakfast = Column(Float)                       # Breakfast from CSV
    lunch = Column(Float)                           # Lunch from CSV
    dinner = Column(Float)                          # Dinner from CSV
    other_charges = Column(Float)                   # Other from CSV
    total_amount = Column(Float)                    # Calculated total
    
    # Reservation details
    bill_number = Column(String(50))                # Bill Number from CSV
    pay_article = Column(String(50))                # Pay Article from CSV
    rate_code = Column(String(50))                  # Rate Code from CSV
    res_no = Column(String(50))                     # Res No from CSV
    adult_count = Column(Integer)                   # Adult from CSV
    child_count = Column(Integer)                   # Child from CSV
    compliment = Column(String(10))                 # Compliment from CSV
    
    # Additional info
    nationality = Column(String(10))                # Nat from CSV
    local_region = Column(String(100))              # Local Region from CSV
    company_ta = Column(String(100))                # Company / TA from CSV
    sob = Column(String(50))                        # SOB from CSV
    nights = Column(Integer)                        # Night from CSV
    segment = Column(String(50))                    # Segment from CSV
    created_by = Column(String(50))                 # By from CSV
    k_card = Column(String(10))                     # K-Card from CSV
    remarks = Column(Text)                          # remarks from CSV
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    csv_upload = relationship("CSVUpload", back_populates="reservasi")
    
    # Unique constraint untuk mencegah duplicate
    __table_args__ = (
        # Composite unique key: arrival_date + depart_date + room_number
        # Jika ada reservasi dengan arrival + depart + room yang sama, akan dianggap duplicate
    )


class ChatWhatsapp(Base):
    __tablename__ = "chat_whatsapp"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_upload_id = Column(Integer, ForeignKey("csv_uploads.id"))
    phone_number = Column(String(20), index=True)
    message_type = Column(String(50))  # Type from CSV
    message_date = Column(DateTime)    # Date from CSV
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    csv_upload = relationship("CSVUpload", back_populates="chat_whatsapp")
    
    # Unique constraint untuk mencegah duplicate
    __table_args__ = (
        # Composite unique key: phone_number + message_date + message
        # Jika ada chat dengan phone + date + content yang sama, akan dianggap duplicate
    )


class TransaksiResto(Base):
    __tablename__ = "transaksi_resto"
    
    id = Column(Integer, primary_key=True, index=True)
    csv_upload_id = Column(Integer, ForeignKey("csv_uploads.id"))
    transaction_id = Column(String(50), index=True)
    guest_id = Column(String(50), index=True)
    item_name = Column(String(255))
    quantity = Column(Integer)
    price = Column(Integer)  # in cents
    total_amount = Column(Integer)  # in cents
    timestamp = Column(DateTime)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship
    csv_upload = relationship("CSVUpload", back_populates="transaksi_resto")
    
    # Unique constraint untuk mencegah duplicate
    __table_args__ = (
        # Composite unique key: transaction_id + guest_id + timestamp
        # Jika ada transaksi dengan ID + guest + timestamp yang sama, akan dianggap duplicate
    )

# ===== PROCESSED TABLES (untuk single source of truth) =====

class ProfileTamuProcessed(Base):
    __tablename__ = "profile_tamu_processed"
    
    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(String(50), unique=True)
    name = Column(String(255))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    birth_date = Column(String(20))  # YYYY-MM-DD format
    occupation = Column(String(100))
    city = Column(String(100))
    country = Column(String(100))
    segment = Column(String(50))
    type_id = Column(String(50))  # KTP, Passport, etc.
    id_no = Column(String(100))
    sex = Column(String(20))
    zip_code = Column(String(20))
    local_region = Column(String(100))
    telefax = Column(String(20))
    mobile_no = Column(String(20))
    comments = Column(Text)
    credit_limit = Column(String(50))
    last_updated = Column(DateTime(timezone=True), default=func.now())
    last_upload_id = Column(Integer, ForeignKey("csv_uploads.id"))

class ReservasiProcessed(Base):
    __tablename__ = "reservasi_processed"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic reservation info
    reservation_id = Column(String(50), index=True)  # Number from CSV
    guest_id = Column(String(50), index=True)       # Guest No from CSV
    guest_name = Column(String(255))                # Combined First Name + Last Name
    room_number = Column(String(50))                # Room Number from CSV
    room_type = Column(String(50))                  # Room Type from CSV
    room_type_desc = Column(String(50))             # Room Type Description
    arrangement = Column(String(50))                # Arrangement from CSV
    
    # Dates and times
    in_house_date = Column(String(20))              # In House Date from CSV
    arrival_date = Column(String(20))               # Arrival from CSV
    depart_date = Column(String(20))                # Depart from CSV
    check_in_time = Column(String(20))              # C/I Time from CSV
    check_out_time = Column(String(20))             # C/O Time from CSV
    created_date = Column(String(20))               # Created from CSV
    
    # Guest details
    birth_date = Column(String(20))                 # Birth Date from CSV
    age = Column(Integer)                           # Age from CSV
    member_no = Column(String(50))                  # Member No from CSV
    member_type = Column(String(50))                # Member Type from CSV
    email = Column(String(100))                     # Email from CSV
    mobile_phone = Column(String(20))               # Mobile Phone from CSV
    vip_status = Column(String(10))                 # VIP from CSV
    
    # Financial info
    room_rate = Column(Float)                       # Room Rate from CSV
    lodging = Column(Float)                         # Lodging from CSV
    breakfast = Column(Float)                       # Breakfast from CSV
    lunch = Column(Float)                           # Lunch from CSV
    dinner = Column(Float)                          # Dinner from CSV
    other_charges = Column(Float)                   # Other from CSV
    total_amount = Column(Float)                    # Calculated total
    
    # Reservation details
    bill_number = Column(String(50))                # Bill Number from CSV
    pay_article = Column(String(50))                # Pay Article from CSV
    rate_code = Column(String(50))                  # Rate Code from CSV
    res_no = Column(String(50))                     # Res No from CSV
    adult_count = Column(Integer)                   # Adult from CSV
    child_count = Column(Integer)                   # Child from CSV
    compliment = Column(String(10))                 # Compliment from CSV
    
    # Additional info
    nationality = Column(String(10))                # Nat from CSV
    local_region = Column(String(100))              # Local Region from CSV
    company_ta = Column(String(100))                # Company / TA from CSV
    sob = Column(String(50))                        # SOB from CSV
    nights = Column(Integer)                        # Night from CSV
    segment = Column(String(50))                    # Segment from CSV
    created_by = Column(String(50))                 # By from CSV
    k_card = Column(String(10))                     # K-Card from CSV
    remarks = Column(Text)                          # remarks from CSV
    
    last_updated = Column(DateTime(timezone=True), default=func.now())
    last_upload_id = Column(Integer, ForeignKey("csv_uploads.id"))
    
    __table_args__ = (UniqueConstraint('arrival_date', 'depart_date', 'room_number', name='_arrival_depart_room_uc'),)

class ChatWhatsappProcessed(Base):
    __tablename__ = "chat_whatsapp_processed"
    
    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String(20))
    message_type = Column(String(50))  # Type from CSV
    message_date = Column(DateTime)    # Date from CSV
    message = Column(Text)
    # Kolom generated selalu hasil dari md5(message)
    message_hash = Column(
        String(32),
        Computed("md5(message::text)", persisted=True)  # STORED di PostgreSQL
    )
    last_updated = Column(DateTime(timezone=True), default=func.now())
    last_upload_id = Column(Integer, ForeignKey("csv_uploads.id"))
    
    __table_args__ = (UniqueConstraint('phone_number', 'message_date', 'message_hash', name='_phone_date_message_uc'),)

class TransaksiRestoProcessed(Base):
    __tablename__ = "transaksi_resto_processed"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50))
    guest_id = Column(String(50))
    item_name = Column(String(255))
    quantity = Column(Integer)
    price = Column(Integer)  # in cents
    total_amount = Column(Integer)  # in cents
    timestamp = Column(DateTime)
    last_updated = Column(DateTime(timezone=True), default=func.now())
    last_upload_id = Column(Integer, ForeignKey("csv_uploads.id"))
    
    __table_args__ = (UniqueConstraint('transaction_id', 'guest_id', 'timestamp', name='_transaction_guest_time_uc'),)