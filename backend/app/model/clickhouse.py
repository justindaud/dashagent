# app/model/clickhouse.py
from sqlalchemy.orm import declarative_base
from sqlalchemy import (
    Column,
    String,
    Integer,
    BigInteger,
    DateTime,
    Numeric,
    Boolean,
)

ClickHouseBase = declarative_base()

class DatamartChatWhatsapp(ClickHouseBase):
    __tablename__ = "datamart_chat_whatsapp"
    __table_args__ = {"schema": "default"}

    phone_number = Column(String, primary_key=True, nullable=True)
    message_type = Column(String, primary_key=True, nullable=True)
    message_date = Column(DateTime, primary_key=True, nullable=True)
    message = Column(String, primary_key=True, nullable=True)
    csv_upload_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False)
    ingested_at = Column(DateTime, nullable=False)
    version = Column(Integer, nullable=False)

class DatamartProfileGuest(ClickHouseBase):
    __tablename__ = "datamart_profile_guest"
    __table_args__ = {"schema": "default"}

    name = Column(String, primary_key=True)
    csv_upload_id = Column(Integer, primary_key=True)
    guest_id = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    occupation = Column(String, nullable=True)
    city = Column(String, nullable=True)
    country = Column(String, nullable=True)
    segment = Column(String, nullable=True)
    type_id = Column(String, nullable=True)
    id_no = Column(String, nullable=True)
    sex = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    local_region = Column(String, nullable=True)
    telefax = Column(String, nullable=True)
    comments = Column(String, nullable=True)
    credit_limit = Column(String, nullable=True)
    mobile_no = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False)
    ingested_at = Column(DateTime, nullable=False)
    version = Column(Integer, nullable=False)

class DatamartReservation(ClickHouseBase):
    __tablename__ = "datamart_reservations"
    __table_args__ = {"schema": "default"}

    guest_name = Column(String, nullable=True)
    arrival_date = Column(DateTime, primary_key=True)
    depart_date = Column(DateTime, primary_key=True)
    room_number = Column(String, primary_key=True)
    csv_upload_id = Column(Integer, primary_key=True)
    reservation_id = Column(Integer, nullable=True)
    guest_id = Column(String, nullable=True)
    room_type = Column(String, nullable=True)
    room_type_desc = Column(String, nullable=False)
    arrangement = Column(String, nullable=True)
    in_house_date = Column(String, nullable=True)
    room_rate = Column(Numeric(18, 2), nullable=False)
    lodging = Column(Numeric(18, 2), nullable=False)
    breakfast = Column(Numeric(18, 2), nullable=False)
    lunch = Column(Numeric(18, 2), nullable=False)
    dinner = Column(Numeric(18, 2), nullable=False)
    other_charges = Column(Numeric(18, 2), nullable=False)
    total_amount = Column(Numeric(18, 2), nullable=False)
    check_in_time = Column(String, nullable=True)
    check_out_time = Column(String, nullable=True)
    created_date = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    member_no = Column(String, nullable=True)
    member_type = Column(String, nullable=True)
    email = Column(String, nullable=True)
    mobile_phone = Column(String, nullable=True)
    vip_status = Column(String, nullable=True)
    bill_number = Column(String, nullable=True)
    pay_article = Column(String, nullable=True)
    rate_code = Column(String, nullable=True)
    adult_count = Column(Integer, nullable=True)
    child_count = Column(Integer, nullable=True)
    compliment = Column(String, nullable=True)
    nationality = Column(String, nullable=True)
    local_region = Column(String, nullable=True)
    company_ta = Column(String, nullable=True)
    sob = Column(String, nullable=True)
    nights = Column(Integer, nullable=True)
    segment = Column(String, nullable=True)
    created_by = Column(String, nullable=True)
    k_card = Column(String, nullable=True)
    remarks = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False)
    ingested_at = Column(DateTime, nullable=False)
    version = Column(Integer, nullable=False)

class DatamartTransactionResto(ClickHouseBase):
    __tablename__ = "datamart_transaction_resto"
    __table_args__ = {"schema": "default"}

    bill_number = Column(String, primary_key=True, nullable=True)
    article_number = Column(String, primary_key=True, nullable=True)
    guest_name = Column(String, nullable=True)
    item_name = Column(String, nullable=True)
    quantity = Column(BigInteger, nullable=True)
    sales = Column(BigInteger, nullable=True)
    payment = Column(BigInteger, nullable=True)
    article_category = Column(String, nullable=True)
    article_subcategory = Column(String, nullable=True)
    outlet = Column(String, nullable=True)
    table_number = Column(BigInteger, nullable=True)
    posting_id = Column(String, nullable=True)
    reservation_number = Column(String, nullable=True)
    travel_agent_name = Column(String, nullable=True)
    prev_bill_number = Column(String, nullable=True)
    transaction_date = Column(DateTime, primary_key=True, nullable=True)
    start_time = Column(String, nullable=True)
    close_time = Column(String, nullable=True)
    time = Column(String, nullable=True)
    bill_discount = Column(Numeric(18, 2), nullable=True)
    bill_compliment = Column(Numeric(18, 2), nullable=True)
    total_deduction = Column(Numeric(18, 2), nullable=True)
    csv_upload_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=True)
    deleted_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, nullable=False)
    ingested_at = Column(DateTime, nullable=False)
    version = Column(Integer, nullable=False)
