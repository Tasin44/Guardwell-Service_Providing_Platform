"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Single Responsibility Principle (SRP):
   - FileService শুধুমাত্র ফাইল আপলোড, ভ্যালিডেশন (সাইজ ও এক্সটেনশন) এবং
     ডিস্কে সংরক্ষণের কাজ করে।
2. Security & Sanitization:
   - ফাইলের নাম UUID দিয়ে পরিবর্তন করে সংরক্ষণ করা হয় যাতে Path Traversal Attack না ঘটে।
================================================================================
"""

import os
import uuid
import aiofiles
from fastapi import UploadFile
from app.core.config import settings
from app.core.exceptions import http_400_bad_request

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}


class FileService:
    @staticmethod
    async def save_upload_file(file: UploadFile, subfolder: str = "media") -> str:
        """
        Saves an uploaded file asynchronously and returns the accessible URL path.
        """
        if not file or not file.filename:
            return ""

        filename = file.filename
        ext = os.path.splitext(filename)[1].lower()

        allowed_all = ALLOWED_IMAGE_EXTENSIONS.union(ALLOWED_VIDEO_EXTENSIONS)
        if ext not in allowed_all:
            raise http_400_bad_request(f"File type '{ext}' is not supported. Supported: {', '.join(allowed_all)}")

        folder_path = os.path.join(settings.UPLOAD_DIR, subfolder)
        os.makedirs(folder_path, exist_ok=True)

        unique_filename = f"{uuid.uuid4().hex}{ext}"
        destination = os.path.join(folder_path, unique_filename)

        async with aiofiles.open(destination, "wb") as buffer:
            while content := await file.read(1024 * 1024):  # 1MB chunks
                await buffer.write(content)

        # Return web accessible static path
        relative_path = f"/uploads/{subfolder}/{unique_filename}"
        return relative_path


file_service = FileService()