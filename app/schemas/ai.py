from typing import Optional
from pydantic import BaseModel


class AskAIResponse(BaseModel):
    prompt: str
    room_type: Optional[str] = None
    original_image_url: str
    generated_image_url: str
    ai_suggestions: Optional[str] = None

