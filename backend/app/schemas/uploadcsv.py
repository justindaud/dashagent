# schemas/user.py
from pydantic import Field, ConfigDict
from typing import Optional
from app.utils.trim import TrimmedModel
from app.model.user import UserRole
from typing import List, Optional
from datetime import datetime

class UserOut(TrimmedModel):
    user_id: str
    username: str
    full_name: Optional[str] = None
    role: UserRole
    is_active: bool
    model_config = ConfigDict(from_attributes=True)

class UploadOut(TrimmedModel):
    id: int
    filename: str
    file_type: str
    status: str
    rows_processed: int
    error_message: Optional[str] = None
    created_at: datetime
    uploader: Optional[UserOut] = None
    deleter: Optional[UserOut] = None
    model_config = ConfigDict(from_attributes=True)