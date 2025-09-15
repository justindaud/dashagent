from typing import Optional, List
from datetime import datetime
from pydantic import Field, ConfigDict
from app.utils.trim import TrimmedModel

class SessionCreate(TrimmedModel):
    title: Optional[str] = Field(default=None, max_length=255)

class SessionOut(TrimmedModel):
    id: str
    title: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class SessionsOut(TrimmedModel):
    items: List[SessionOut]
