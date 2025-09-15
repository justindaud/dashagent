from pydantic import Field
from app.utils.trim import TrimmedModel

class PromptIn(TrimmedModel):
    prompt: str = Field(min_length=1)
