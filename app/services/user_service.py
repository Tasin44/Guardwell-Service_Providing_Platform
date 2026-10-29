"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Separation of Concerns:
   - ইউজার প্রোফাইল ও এডমিন মডারেশন সার্ভিস এখানে সংগঠিত।
2. Security & Role Verification:
   - গ্রাহকের নিজের প্রোফাইল এডিট এবং এডমিনের ভেরিফিকেশন/ব্যান সম্পূর্ণ পৃথক মেথডে বিভক্ত।
================================================================================
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.models.user import User
from app.repositories.user_repository import user_repository
from app.services.file_service import file_service
from app.schemas.user import UserProfileResponse, UserProfileUpdateForm
from app.core.exceptions import http_404_not_found, http_409_conflict


class UserService:
    async def update_profile(
        self,
        db: Session,
        user: User,
        payload: UserProfileUpdateForm,
        image_file: Optional[UploadFile] = None
    ) -> UserProfileResponse:
        """
        Updates user personal profile and uploads profile image if provided.
        """
        if payload.name:
            user.name = payload.name.strip()

        if payload.phone_number and payload.phone_number.strip() != user.phone_number:
            existing = user_repository.get_by_phone(db, payload.phone_number.strip())
            if existing and existing.id != user.id:
                raise http_409_conflict("This phone number is already registered to another account.")
            user.phone_number = payload.phone_number.strip()

        if payload.payout_email:
            user.payout_email = str(payload.payout_email).strip().lower()

        if payload.payout_phone:
            user.payout_phone = payload.payout_phone.strip()

        if image_file:
            image_url = await file_service.save_upload_file(image_file, subfolder="avatars")
            if image_url:
                user.image_url = image_url

        db.add(user)
        db.commit()
        db.refresh(user)

        return UserProfileResponse.model_validate(user)

    def set_customer_verification(self, db: Session, user_id: int, is_verified: bool) -> UserProfileResponse:
        """Admin marks customer as verified/existing Guardwell customer."""
        user = user_repository.get(db, user_id)
        if not user:
            raise http_404_not_found(f"User with ID {user_id} not found.")

        user.is_verified_customer = is_verified
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserProfileResponse.model_validate(user)

    def toggle_feed_ban(self, db: Session, user_id: int, is_banned: bool) -> UserProfileResponse:
        """Admin bans/restricts or unbans a user from the social community feed."""
        user = user_repository.get(db, user_id)
        if not user:
            raise http_404_not_found(f"User with ID {user_id} not found.")

        user.is_feed_banned = is_banned
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserProfileResponse.model_validate(user)


user_service = UserService()
