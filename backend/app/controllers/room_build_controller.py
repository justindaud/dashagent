# backend/app/controllers/room_build_controller.py
from typing import Optional, List
from datetime import date
from fastapi import HTTPException
from sqlalchemy.orm import Session

import app.repositories.room_build_repository as repo
from app.model.room import RoomBuild

def register_room_build_controller(
    db: Session,
    built_date: date,
    room_count: int,
    room_type_desc: str
):
    room_build = RoomBuild(
        built_date=built_date,
        room_count=room_count,
        room_type_desc=room_type_desc,
    )
    return repo.add_room_build(db, room_build)

def get_room_by_id_controller(db: Session, room_build_id: int):
    room_build = repo.get_room_by_id(db, room_build_id)
    if not room_build:
        raise HTTPException(status_code=404, detail="Room build not found")
    return room_build


def list_room_builds_controller(db: Session) -> List[RoomBuild]:
    return repo.list_room_builds(db)


def get_room_count_until_date_controller(
    db: Session,
    target_date: date,
    room_type_descs: Optional[List[str]] = None,
) -> int:
    return repo.get_room_count_until_date(db, target_date, room_type_descs)


def get_room_count_per_type_until_date_controller(
    db: Session,
    target_date: date
) -> List[dict]:
    rows = repo.get_room_count_per_type_until_date(db, target_date)
    return [
        {
            "room_type_desc": room_type_desc,
            "room_count": room_count or 0,
        }
        for (room_type_desc, room_count) in rows
    ]


def update_room_build_controller(
    db: Session,
    room_build_id: int,
    built_date: Optional[date],
    room_count: Optional[int],
    room_type_desc: Optional[str],
):
    room_build = repo.get_room_by_id(db, room_build_id)

    if not room_build:
        raise HTTPException(status_code=404, detail="Room build not found")

    if built_date is None and room_count is None and room_type_desc is None:
        raise HTTPException(status_code=400, detail="At least one field to update is required")

    if built_date is not None:
        room_build.built_date = built_date

    if room_count is not None:
        room_build.room_count = room_count

    if room_type_desc is not None:
        room_build.room_type_desc = room_type_desc.strip()

    return repo.update_room_build(db, room_build)


def register_bulk_room_build_controller(db: Session, rooms_data: list[dict]):
    room_builds = []
    for room_data in rooms_data:
        room_build = RoomBuild(
            built_date=room_data["built_date"],
            room_count=room_data["room_count"],
            room_type_desc=room_data["room_type_desc"],
        )
        room_builds.append(room_build)

    return repo.add_bulk_room_build(db, room_builds)
