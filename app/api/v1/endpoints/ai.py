"""
================================================================================
AI HOME DESIGNER ROUTER:
- POST /ask_ai/ : Upload a room/home photo + preference prompt to generate
  an AI-redesigned image and decor/color recommendations via Gemini AI.
================================================================================
"""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from app.api.deps import get_optional_current_user
from app.models.user import User
from app.schemas.ai import AskAIResponse
from app.services.ai_service import ai_service

router = APIRouter()


@router.post(
    "/ask_ai/",
    response_model=AskAIResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask AI to Redesign & Suggest Improvements for a Room Photo"
)
@router.post(
    "/ask_ai",
    response_model=AskAIResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def ask_ai(
    image: UploadFile = File(..., description="Photo of your kitchen, room, bathroom, dining room, etc."),
    prompt: str = Form(..., min_length=2, description="Your preferences (e.g. color change, decor items, style)"),
    room_type: Optional[str] = Form(None, description="Optional room type (e.g. kitchen, bathroom, dining_room, bedroom)"),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Accepts an uploaded room photo and user preferences, then uses Gemini AI
    to generate a new redesigned image and item/styling recommendations.
    """
    return await ai_service.generate_room_redesign(
        image_file=image,
        prompt=prompt,
        room_type=room_type,
    )

