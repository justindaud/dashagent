from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import date
from typing import List

from app.db.database import get_db
from app.schemas.room import RoomBuildCreate, RoomBuildUpdate, RoomBuildOut, RoomBuildBulkCreate
from app.schemas.response import ApiResponse
from app.controllers import room_build_controller as ctl
from app.middlewares.middleware import require_admin
from app.model.user import User as UserModel
from app.utils.response import success

router = APIRouter(prefix="/api/room-builds", tags=["Room Builds"])


@router.post("/", response_model=ApiResponse[RoomBuildOut])
def create_room_build(
    payload: RoomBuildCreate,
    db: Session = Depends(get_db)
):
    room_build = ctl.register_room_build_controller(
        db,
        built_date=payload.built_date,
        room_count=payload.room_count,
    )
    return success(
        message="RoomBuild created successfully",
        status_code=201,
        data=RoomBuildOut.model_validate(room_build)
    )

@router.get("/", response_model=ApiResponse[RoomBuildOut])
def list_rooms(
    payload: RoomBuildCreate,
    db: Session = Depends(get_db),
):
    rooms = ctl.list_room_builds_controller(db)
    return success(message="Rooms list fetched successfully", data=[RoomBuildOut.model_validate(r) for r in rooms], status_code=200)

@router.get("/count", response_model=ApiResponse[int])
def get_total_rooms(
    target_date: date = Query(..., description="Date to count rooms until"),
    db: Session = Depends(get_db),
):
    total = ctl.get_room_count_until_date_controller(db, target_date)
    return success(message="Room count fetched successfully", data=total)

@router.put("/{room_build_id}", response_model=ApiResponse[RoomBuildOut])
def update_room_build(
    room_build_id: int,
    payload: RoomBuildUpdate,
    db: Session = Depends(get_db),
):
    room_build = ctl.update_room_build_controller(
        db,
        target_room_build_id=room_build_id,
        built_date=payload.built_date,
        room_count=payload.room_count,
    )
    return success(
        message="RoomBuild updated successfully",
        data=RoomBuildOut.model_validate(room_build),
        status_code=200
    )

@router.post("/bulk", response_model=ApiResponse[List[RoomBuildOut]])
def create_bulk_room_build(
    payload: RoomBuildBulkCreate,
    db: Session = Depends(get_db)
):
    room_builds = ctl.register_bulk_room_build_controller(
        db,
        [room.model_dump() for room in payload.rooms]
    )
    return success(
        message="Room builds created successfully",
        status_code=201,
        data=[RoomBuildOut.model_validate(r) for r in room_builds]
    )
