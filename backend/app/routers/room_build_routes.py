from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.room import RoomBuildCreate, RoomBuildUpdate, RoomBuildOut
from app.schemas.response import ApiResponse
from app.controllers import room_build_controller as ctl
from app.middlewares.middleware import require_admin
from app.model.user import User as UserModel
from app.utils.response import success

router = APIRouter(prefix="/api/room-builds", tags=["Room Builds"])


@router.post("/", response_model=ApiResponse[RoomBuildOut])
def create_room_build(
    payload: RoomBuildCreate,
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_admin)
):
    room_build = ctl.register_room_build_controller(
        db,
        built_date=payload.built_date,
        room_count=payload.room_count,
    )
    return success(
        message="RoomBuild created successfully",
        data=RoomBuildOut.model_validate(room_build),
        status_code=201
    )

@router.get("/", response_model=ApiResponse[RoomBuildOut])
def list_rooms(
    payload: RoomBuildCreate,
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_admin)
):
    rooms = ctl.list_rooms.controller(db)
    return success(message="Rooms list fetched successfully", data=[RoomBuildOut.model_validate(r) for r in rooms], status_code=200)


@router.put("/{room_build_id}", response_model=ApiResponse[RoomBuildOut])
def update_room_build(
    room_build_id: int,
    payload: RoomBuildUpdate,
    db: Session = Depends(get_db),
    _: UserModel = Depends(require_admin)
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
