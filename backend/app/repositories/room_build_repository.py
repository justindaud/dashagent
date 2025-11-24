# app/repositories/room_build_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List, Tuple
from datetime import date

from app.model.room import RoomBuild

def get_room_by_id(db: Session, room_build_id: int) -> Optional[RoomBuild]:
    return db.query(RoomBuild).filter(RoomBuild.room_build_id == room_build_id).first()

def list_room_builds(db: Session) -> List[RoomBuild]:
    return db.query(RoomBuild).order_by(RoomBuild.built_date.desc()).all()

def get_room_count_per_type_until_date(
    db: Session,
    target_date: date,
    room_type_descs: Optional[List[str]] = None
) -> List[Tuple[str, int]]:
    subquery = (
        db.query(
            RoomBuild.room_type_desc.label("room_type_desc"),
            func.max(RoomBuild.built_date).label("latest_date"),
        )
        .filter(RoomBuild.built_date <= target_date)
    )

    if room_type_descs:
        subquery = subquery.filter(RoomBuild.room_type_desc.in_(room_type_descs))

    subquery = subquery.group_by(RoomBuild.room_type_desc).subquery()

    rows = (
        db.query(
            RoomBuild.room_type_desc.label("room_type_desc"),
            func.max(RoomBuild.room_count).label("room_count"),
        )
        .join(
            subquery,
            and_(
                RoomBuild.room_type_desc == subquery.c.room_type_desc,
                RoomBuild.built_date == subquery.c.latest_date,
            ),
        )
        .group_by(RoomBuild.room_type_desc)
        .all()
    )

    return [(r.room_type_desc, r.room_count) for r in rows]

def get_room_count_until_date(
    db: Session,
    target_date: date,
    room_type_descs: Optional[List[str]] = None
) -> int:
    per_type_rows = get_room_count_per_type_until_date(db, target_date, room_type_descs)
    total_rooms = sum((room_count or 0) for (_type, room_count) in per_type_rows)
    return total_rooms or 0

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