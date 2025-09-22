from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from app.model.room import RoomBuild

def get_room_by_id(db: Session, room_build_id: str) -> Optional[RoomBuild]:
    return db.query(RoomBuild).filter(RoomBuild.room_build_id == room_build_id).first()

def list_rooms(db: Session) -> List[RoomBuild]:
    return db.query(RoomBuild).order_by(RoomBuild.built_date.desc()).all()

def add_room_build(db: Session, room: RoomBuild) -> RoomBuild:
    db.add(room)
    db.commit()
    db.refresh(room)
    return room

def update_room_build(db: Session, room: RoomBuild) -> RoomBuild:
    db.commit()
    db.refresh(room)
    return room