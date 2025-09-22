from pydantic import Field, ConfigDict
from datetime import date
from typing import Optional
from app.utils.trim import TrimmedModel

class RoomBuildCreate(TrimmedModel):
    built_date: date
    room_count: int

class RoomBuildUpdate(TrimmedModel):
    built_date: Optional[date] = None
    room_count: Optional[int] = Field(None, ge=1)

class RoomBuildOut(TrimmedModel):
    id: int
    built_date: date
    room_count: int

    model_config = ConfigDict(from_attributes=True)