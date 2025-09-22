from sqlalchemy import Column, Integer, Date
from app.db.database import Base

class RoomBuild(Base):
    __tablename__ = "room_builds"

    room_build_id = Column(Integer, primary_key=True, index=True)
    built_date = Column(Date, nullable=False)
    room_count = Column(Integer, nullable=False)
