"""
================================================================================
FASTAPI ROUTER VS DRF APIVIEWS (PROFILE MANAGEMENT):
1. Multipart Form Data Handling:
   - DRF-এ আমরা MultiPartParser ব্যবহার করতাম; FastAPI-তে File() এবং Form() প্যারামিটার
     দিয়ে খুব স্বচ্ছভাবে ফাইল আপলোড ও ফর্ম ডাটা একসাথে হ্যান্ডল করা যায়।
2. Authentication Guard:
   - current_user: User = Depends(get_current_user) নিশ্চিত করে শুধুমাত্র লগইন করা ইউজার
     তার নিজের প্রোফাইল রিড ও আপডেট করতে পারে।
================================================================================
"""

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserProfileResponse, UserProfileUpdateForm
from app.services.user_service import user_service

router = APIRouter()


@router.get(
    "/",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Current User Profile"
)
def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Returns authenticated user's profile details including Name, Email, Phone,
    Referral code, verification status, and e-transfer payout information.
    """
    return UserProfileResponse.model_validate(current_user)


@router.patch(
    "/",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update User Profile (Multipart Form Data)"
)
async def update_user_profile(
    name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    payout_email: Optional[str] = Form(None),
    payout_phone: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates profile details via multipart/form-data.
    Accepts Name, Phone, Avatar image file, and E-transfer payout credentials.
    """
    payload = UserProfileUpdateForm(
        name=name,
        phone_number=phone_number,
        payout_email=payout_email,
        payout_phone=payout_phone
    )
    return await user_service.update_profile(
        db,
        user=current_user,
        payload=payload,
        image_file=image
    )
