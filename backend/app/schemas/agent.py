# backend/app/schemas/agent.py
from pydantic import Field
from app.utils.trim import TrimmedModel

class PromptIn(TrimmedModel):
    user_input: str = Field(min_length=1)
