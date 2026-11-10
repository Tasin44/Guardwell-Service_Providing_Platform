"""
================================================================================
GEMINI AI HOME DESIGN & VISUALIZATION SERVICE:
- Accepts an uploaded photo of a room (kitchen, bathroom, dining room, etc.)
  plus user preferences (color changes, decor/item ideas, beautification).
- Uses Google Gemini (`google-genai`) multimodal image generation/editing
  to produce a redesigned photo and concise item/design suggestions.
================================================================================
"""

import asyncio
import mimetypes
import os
import uuid
from typing import Optional

import aiofiles
from fastapi import HTTPException, UploadFile, status
from google import genai
from google.genai import types

from app.core.config import settings
from app.core.exceptions import http_400_bad_request
from app.schemas.ai import AskAIResponse
from app.services.file_service import ALLOWED_IMAGE_EXTENSIONS, file_service


class AIService:
    @staticmethod
    def _build_design_prompt(user_prompt: str, room_type: Optional[str] = None) -> str:
        room_context = f"Room / Space Type: {room_type.strip()}\n" if room_type and room_type.strip() else ""
        return (
            "You are an expert interior & home renovation visualizer for Guardwell.\n"
            f"{room_context}"
            f"User Preference / Request: {user_prompt.strip()}\n\n"
            "Instructions:\n"
            "1. Generate a realistic, high-quality edited version of the uploaded photo applying "
            "the user's requested color changes, item additions/replacements, and styling improvements "
            "while preserving the room's core structure, perspective, windows, and layout.\n"
            "2. Also provide a short, helpful text summary of the recommended items, colors, and "
            "improvements shown in the redesigned image."
        )

    @staticmethod
    def _mime_to_extension(mime_type: Optional[str]) -> str:
        if mime_type:
            guessed = mimetypes.guess_extension(mime_type.split(";")[0].strip())
            if guessed:
                return ".jpg" if guessed == ".jpe" else guessed
        return ".png"

    @staticmethod
    async def _save_bytes(data: bytes, subfolder: str, ext: str) -> str:
        folder_path = os.path.join(settings.UPLOAD_DIR, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        destination = os.path.join(folder_path, unique_filename)

        async with aiofiles.open(destination, "wb") as buffer:
            await buffer.write(data)

        relative_path = f"/uploads/{subfolder}/{unique_filename}"
        return file_service.get_full_url(relative_path) or relative_path

    async def generate_room_redesign(
        self,
        *,
        image_file: UploadFile,
        prompt: str,
        room_type: Optional[str] = None,
    ) -> AskAIResponse:
        if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
            raise http_400_bad_request(
                "GEMINI_API_KEY is not configured. Please add your Gemini API key to the .env file."
            )

        if not image_file or not image_file.filename:
            raise http_400_bad_request("An image file is required.")

        ext = os.path.splitext(image_file.filename)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise http_400_bad_request(
                f"Image type '{ext}' is not supported. Supported: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}"
            )

        image_bytes = await image_file.read()
        if not image_bytes:
            raise http_400_bad_request("Uploaded image file is empty.")

        mime_type = image_file.content_type or mimetypes.guess_type(image_file.filename)[0] or "image/jpeg"
        original_image_url = await self._save_bytes(image_bytes, subfolder="ai/inputs", ext=ext)

        full_prompt = self._build_design_prompt(prompt, room_type=room_type)

        def _call_gemini():
            client = genai.Client(api_key=settings.GEMINI_API_KEY.strip())
            return client.models.generate_content(
                model=settings.GEMINI_IMAGE_MODEL,
                contents=[
                    full_prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["TEXT", "IMAGE"],
                ),
            )

        try:
            response = await asyncio.to_thread(_call_gemini)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini AI image generation failed: {str(exc)}",
            )

        generated_image_bytes: Optional[bytes] = None
        generated_mime_type: Optional[str] = None
        text_parts = []

        parts = getattr(response, "parts", None)
        if not parts and getattr(response, "candidates", None):
            candidate = response.candidates[0]
            if getattr(candidate, "content", None):
                parts = candidate.content.parts

        for part in parts or []:
            if getattr(part, "text", None):
                text_parts.append(part.text.strip())
            elif getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                generated_image_bytes = part.inline_data.data
                generated_mime_type = getattr(part.inline_data, "mime_type", None)

        if not generated_image_bytes:
            detail = " ".join(text_parts) if text_parts else "No image was returned by Gemini."
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini AI did not return a generated image. {detail}",
            )

        generated_ext = self._mime_to_extension(generated_mime_type)
        generated_image_url = await self._save_bytes(
            generated_image_bytes,
            subfolder="ai/generated",
            ext=generated_ext,
        )

        return AskAIResponse(
            prompt=prompt.strip(),
            room_type=room_type.strip() if room_type else None,
            original_image_url=original_image_url,
            generated_image_url=generated_image_url,
            ai_suggestions="\n".join(text_parts) if text_parts else None,
        )


ai_service = AIService()
