from typing import Optional, List
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.repositories.room_build_repository as repo
from app.model.room import RoomBuild


def register_room_build_controller(db: Session, built_date: date, room_count: int):
    room_build = RoomBuild(
        built_date=built_date,
        room_count=room_count,
    )
    return repo.add_room_build(db, room_build)

def get_room_by_id_controller(db: Session, room_build_id: str):
    room_build = repo.get_room_by_id(db, room_build_id)
    if not room_build:
        raise HTTPException(status_code=404, detail="Room build not found")
    return room_build

def list_room_builds_controller(db: Session) -> List[RoomBuild]:
    return repo.list_room_builds(db)


def update_room_build_controller(
    db: Session,
    room_build_id: str,
    built_date: Optional[date], room_count: Optional[int],
):
    room_build = repo.get_room_build_by_id(db, room_build_id)
    if not room_build:
        raise HTTPException(status_code=404, detail="Room build not found")
    
    if (
        built_date is None
        and room_count is None
    ):
        raise HTTPException(status_code=400, detail="At least one field to update is required")


    if built_date is not None:
        room_build.built_date = built_date.strip()

    if room_count is not None:
        room_build.room_count = room_count.strip()

    return repo.update_room_build(db, room_build)
