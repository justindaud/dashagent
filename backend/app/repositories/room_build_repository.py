from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import date
from app.model.room import RoomBuild

def get_room_by_id(db: Session, room_build_id: str) -> Optional[RoomBuild]:
    return db.query(RoomBuild).filter(RoomBuild.room_build_id == room_build_id).first()

def list_room_builds(db: Session) -> List[RoomBuild]:
    return db.query(RoomBuild).order_by(RoomBuild.built_date.desc()).all()

def get_room_count_until_date(db: Session, target_date: date) -> int:
    total_rooms = (
        db.query(func.sum(RoomBuild.room_count))
        .filter(RoomBuild.built_date <= target_date)
        .scalar()
    )
    return total_rooms or 0  # return 0 if None

def add_room_build(db: Session, room: RoomBuild) -> RoomBuild:
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

def update_room_build(db: Session, room: RoomBuild) -> RoomBuild:
    db.commit()
    db.refresh(room)
    return room

def add_bulk_room_build(db: Session, rooms: List[RoomBuild]) -> List[RoomBuild]:
    db.add_all(rooms)
    db.commit()
    for room in rooms:
        db.refresh(room)
    return rooms