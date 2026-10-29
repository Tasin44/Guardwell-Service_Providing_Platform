"""
================================================================================
FASTAPI SCHEMAS VS DRF SERIALIZERS (তুলনামূলক বিশ্লেষণ):
1. DRF-এ আমরা যেমন serializers.ModelSerializer বা serializers.Serializer লিখতাম,
   FastAPI-তে ঠিক সেই কাজটি করে Pydantic BaseModel।
2. Input Validation (Fail Fast):
   - EmailStr স্বয়ংক্রিয়ভাবে RFC মানদণ্ডে ইমেইল ভ্যালিডেট করে।
   - Field(..., min_length=6) ফিল্ড লেভেলে ভ্যালিডেশন নিশ্চিত করে।
3. Output Serialization:
   - from_attributes = True (পূর্বে orm_mode=True) দেওয়ায় SQLAlchemy ORM অবজেক্ট সরাসরি
     JSON রেসপন্সে সিরিয়ালাইজ হয়।
================================================================================
"""
from os import access
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ==========================================
# AUTH REQUEST SCHEMAS (Input Deserializers)
# ==========================================

class UserSignupRequest(BaseModel):
    """
    Analogous to DRF SignupSerializer.
    Validates user registration payload.
    """
    name: str = Field(..., min_length=2, max_length=120, description="Full Name of the user")
    email: EmailStr = Field(..., description="Valid Email address")
    phone_number: str = Field(..., min_length=7, max_length=30, description="Contact phone number")
    password: str = Field(..., min_length=6, max_length=100, description="Password with minimum 6 characters")
    referral_code: Optional[str] = Field(None, max_length=30, description="Optional referral code of the inviter")


class LoginRequest(BaseModel):
    """
    Analogous to DRF LoginSerializer.
    """
    email: EmailStr = Field(..., description="Registered Email")
    password: str = Field(..., description="Account Password")


class VerifyOTPRequest(BaseModel):
    """
    6-digit OTP verification schema for signup confirmation.
    """
    email: EmailStr = Field(...)
    otp_code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")


class ForgotPasswordRequest(BaseModel):
    """
    Requests a 6-digit OTP sent to registered email.
    """
    email: EmailStr = Field(...)


class VerifyForgotOTPRequest(BaseModel):
    """
    Verifies the 6-digit OTP for password recovery and issues a reset token.
    """
    email: EmailStr = Field(...)
    otp_code: str = Field(..., min_length=6, max_length=6)


class ResetPasswordRequest(BaseModel):
    """
    Sets a new password using the verified reset token.
    """
    new_password: str = Field(..., min_length=6, max_length=100)





# ==========================================
# AUTH RESPONSE SCHEMAS (Output Serializers)
# ==========================================

class TokenResponse(BaseModel):
    """
    OAuth2 / JWT access & refresh token pair returned upon successful authentication.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserProfileResponse"  # Forward reference to profile schema


class PasswordResetSuccessResponse(BaseModel):
    message: str = "Password reset successful"


class ForgotPasswordOTPResponse(BaseModel):
    message: str = "6-digit OTP has been sent to your email"
    email: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


#❓what is the purpose of uisng this two lines here 
from app.schemas.user import UserProfileResponse  # Avoid circular import
TokenResponse.model_rebuild()
