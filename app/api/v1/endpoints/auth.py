"""
================================================================================
FASTAPI ROUTER VS DRF APIVIEWS (AUTHENTICATION):
1. DRF Equivalence:
   - DRF-এ আমরা যেমন APIView বা ViewSet-এর মধ্যে def post(self, request) লিখতাম,
     FastAPI-তে @router.post() ডেকরেশনের মাধ্যমে খুব সহজে এবং ক্লিন উপায়ে রাউট তৈরি হয়।
2. Automatic Documentation (Swagger / OpenAPI):
   - FastAPI স্বয়ংক্রিয়ভাবে /docs পেজে রিকোয়েস্ট বডি ও রেসপন্স স্কিমার ইন্টারেক্টিভ UI তৈরি করে।
3. Dependency Injection:
   - db: Session = Depends(get_db) এর মাধ্যমে প্রতিটি রিকোয়েস্টে নিরাপদে ডাটাবেজ সেশন ইনজেক্ট হয়।
================================================================================
"""

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.auth_service import auth_service
from app.schemas.auth import (
    UserSignupRequest,
    LoginRequest,
    VerifyOTPRequest,
    ForgotPasswordRequest,
    VerifyForgotOTPRequest,
    ResetPasswordRequest,
    TokenResponse,
    ForgotPasswordOTPResponse,
    PasswordResetSuccessResponse,
)

router = APIRouter()


@router.post(
    "/signup",
    status_code=status.HTTP_201_CREATED,
    summary="User Registration with Optional Referral Code"
)
def signup(payload: UserSignupRequest, db: Session = Depends(get_db)):
    """
    Registers customer account and sends 6-digit OTP verification code.
    If a valid referral code is provided, links the customer to the referrer.
    """
    return auth_service.signup(db, payload)


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify 6-Digit OTP After Signup"
)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verifies 6-digit OTP after registration.
    Returns Access and Refresh tokens along with full profile details.
    Automatically provisions the $100 referral coupon if user was invited.
    """
    return auth_service.verify_otp(db, payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User Login"
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates user and returns JWT token pair.
    """
    return auth_service.login(db, payload)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Request 6-Digit Password Reset OTP"
)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Sends a 6-digit verification code to the registered email address.
    """
    return auth_service.forgot_password(db, payload)


@router.post(
    "/verify-forgot-otp",
    status_code=status.HTTP_200_OK,
    summary="Verify OTP for Password Reset"
)
def verify_forgot_otp(payload: VerifyForgotOTPRequest, db: Session = Depends(get_db)):
    """
    Verifies the OTP and issues a short-lived password reset token.
    """
    return auth_service.verify_forgot_otp(db, payload)


@router.post(
    "/reset-password",
    response_model=PasswordResetSuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset Account Password"
)
def reset_password(
    payload: ResetPasswordRequest,
    authorization: str = Header(..., description="Reset Token formatted as 'Bearer <reset_token>' or plain token"),
    db: Session = Depends(get_db)
):
    """
    Sets a new password using the verified reset token.
    """
    token = authorization.replace("Bearer ", "").strip()
    return auth_service.reset_password(db, reset_token=token, payload=payload)
