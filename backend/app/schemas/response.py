# app/schemas/response.py
from typing import Generic, TypeVar, List
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    code: int
    messages: str
    data: List[T] = []
    model_config = ConfigDict(from_attributes=True)

class ErrorResponse(BaseModel):
    code: int
    messages: str
