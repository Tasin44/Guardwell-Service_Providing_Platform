"""
================================================================================
FASTAPI SCHEMAS VS DRF SERIALIZERS (USER PROFILE):
1. DRF-এর UserSerializer-এর মতোই UserProfileResponse আউটপুট ডেটা ফরম্যাট করে।
2. Sensitive Data Exclusion:
   - hashed_password ফিল্ডটি রেসপন্স স্কিমাতে রাখা হয়নি, যাতে ক্লায়েন্টে পাসওয়ার্ড লিক না হয়।
3. from_attributes = True:
   - SQLAlchemy User অবজেক্ট থেকে সরাসরি Pydantic মডেলে কনভার্ট করে।
================================================================================
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole


class UserProfileResponse(BaseModel):
    """
    Serializes complete user profile details for API consumers.
    """
    id: int
    name: str
    email: EmailStr
    phone_number: str
    role: UserRole
    referral_code: str
    image_url: Optional[str] = None
    is_verified_otp: bool
    is_verified_customer: bool
    is_feed_banned: bool
    payout_email: Optional[str] = None
    payout_phone: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)#❓what does this line doing here


class UserProfileUpdateForm(BaseModel):
    """
    Schema for updating personal profile information and payout details.
    """
    name: Optional[str] = None
    phone_number: Optional[str] = None
    payout_email: Optional[EmailStr] = None
    payout_phone: Optional[str] = None


class CustomerAdminUpdate(BaseModel):
    """
    Admin control schema for marking customer verification or feed banning.
    """
    is_verified_customer: Optional[bool] = None
    is_feed_banned: Optional[bool] = None
