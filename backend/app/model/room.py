# app/model/room.py
from sqlalchemy import Column, Integer, Date, String
from app.db.database import Base

class RoomBuild(Base):
    __tablename__ = "room_builds"

    room_build_id = Column(Integer, primary_key=True, index=True)
    built_date = Column(Date, nullable=False)
    room_count = Column(Integer, nullable=False)
    room_type_desc = Column(String(30), nullable=False)