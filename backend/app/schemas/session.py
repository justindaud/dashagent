# backend/app/schemas/session.py
from typing import Optional, List
from pydantic import Field, ConfigDict
from app.utils.trim import TrimmedModel

class SessionCreate(TrimmedModel):
    pass

class SessionOut(TrimmedModel):
    session_id: str
    title: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class SessionsOut(TrimmedModel):
    items: List[SessionOut]

class SessionTitleUpdate(TrimmedModel):
    title: str = Field(min_length=1, max_length=255)
