# backend/app/utils/trim.py
from typing import Any
from pydantic import BaseModel, ConfigDict, model_validator

def _trim_any(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return [_trim_any(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_trim_any(v) for v in value)
    if isinstance(value, dict):
        return {k: _trim_any(v) for k, v in value.items()}
    return value

class TrimmedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _strip_strings(cls, data: Any):
        return _trim_any(data)
