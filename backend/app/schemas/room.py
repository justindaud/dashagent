# app/schemas/room.py
from pydantic import Field, ConfigDict
from datetime import date
from typing import Optional
from app.utils.trim import TrimmedModel

class RoomBuildCreate(TrimmedModel):
    built_date: date
    room_count: int
    room_type_desc: str

class RoomBuildUpdate(TrimmedModel):
    built_date: Optional[date] = None
    room_count: Optional[int] = Field(None, ge=1)
    room_type_desc: Optional[str] = None

class RoomBuildOut(TrimmedModel):
    room_build_id: int
    built_date: date
    room_count: int
    room_type_desc: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class RoomBuildBulkCreate(TrimmedModel):
    rooms: list[RoomBuildCreate]

class RoomCountPerTypeOut(TrimmedModel):
    room_type_desc: str
    room_count: int
    model_config = ConfigDict(from_attributes=True)