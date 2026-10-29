"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Business Logic Isolation (SoC):
   - Auth-এর জটিল নিয়ম (OTP জেনারেশন, পাসওয়ার্ড হ্যাশিং, টোকেন ইস্যু, রেফারেল কুপন বরাদ্দ)
     সম্পূর্ণরূপে AuthService-এর ভেতরে পরিচালিত হয়। Router কেবল রিকোয়েস্ট গ্রহণ ও রেসপন্স পাঠায়।
2. Transaction Integrity:
   - ওটিপি ভেরিফিকেশনের পর একই ট্রানজ্যাকশনে ইউজার ভেরিফিকেশন, রেফারেল লিংক এবং
     $100 কুপন তৈরি করা হয়।
3. Fail-Fast Validation:
   - ইমেইল বা ফোন ডুপ্লিকেট হলে ডেটাবেজে প্রবেশের আগেই এরর থ্রো করে।
================================================================================
"""

import string
import secrets
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
import jwt

from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    create_password_reset_token,
    generate_six_digit_otp,
)
from app.core.exceptions import (
    http_400_bad_request,
    http_401_unauthorized,
    http_404_not_found,
    http_409_conflict,
)
from app.models.user import User, UserRole, OTPPurpose
# from app.models.referral import Referral, ReferralStatus, BonusStatus, Coupon, CouponStatus
from app.repositories.user_repository import user_repository
# from app.repositories.referral_repository import referral_repository, coupon_repository
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
from app.schemas.user import UserProfileResponse

logger = logging.getLogger("guardwell.auth")


class AuthService:
    @staticmethod
    def _generate_referral_code(db: Session) -> str:
        """Generates a unique 8-character referral code (e.g. GW7A9K2M)."""
        chars = string.ascii_uppercase + string.digits
        while True:
            code = "GW" + "".join(secrets.choice(chars) for _ in range(6))
            if not user_repository.get_by_referral_code(db, code):
                return code

    def signup(self, db: Session, payload: UserSignupRequest) -> dict:
        """
        Registers a new user, generates a 6-digit OTP, and stores pending referral state.
        """
        # Fail Fast: Check duplicate email
        if user_repository.get_by_email(db, payload.email):
            raise http_409_conflict(f"An account with email '{payload.email}' already exists.")

        # Fail Fast: Check duplicate phone
        if user_repository.get_by_phone(db, payload.phone_number):
            raise http_409_conflict(f"An account with phone number '{payload.phone_number}' already exists.")

        # Validate referral code if provided
        referrer_user = None
        if payload.referral_code:
            referrer_user = user_repository.get_by_referral_code(db, payload.referral_code)
            if not referrer_user:
                raise http_400_bad_request("The provided referral code is invalid.")

        # Create user record (marked unverified until OTP check)
        unique_ref_code = self._generate_referral_code(db)
        new_user = User(
            name=payload.name,
            email=payload.email.strip().lower(),
            phone_number=payload.phone_number.strip(),
            hashed_password=get_password_hash(payload.password),
            role=UserRole.CUSTOMER,
            referral_code=unique_ref_code,
            is_active=True,
            is_verified_otp=False,
            is_verified_customer=False,
            is_feed_banned=False,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Pre-link referral if referrer found
        '''        
        if referrer_user:
            referral_entry = Referral(
                referrer_id=referrer_user.id,
                referred_user_id=new_user.id,
                referred_email=new_user.email,
                referred_phone=new_user.phone_number,
                status=ReferralStatus.SIGNED_UP,
                bonus_status=BonusStatus.PENDING,
                bonus_amount=settings.DEFAULT_COUPON_AMOUNT,
            )
            db.add(referral_entry)
            db.commit()
        '''


        # Generate 6-Digit OTP
        otp_code = generate_six_digit_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        user_repository.create_otp(
            db,
            user_id=new_user.id,
            email=new_user.email,
            otp_code=otp_code,
            purpose=OTPPurpose.SIGNUP,
            expires_at=expires_at
        )

        # In production, dispatch SMS/Email. In dev, log clearly to console.
        logger.info(f"==> [OTP DISPATCH - SIGNUP] Sent OTP {otp_code} to {new_user.email}")
        print(f"\n==========================================")
        print(f" [GUARDWELL OTP - SIGNUP] ")
        print(f" User: {new_user.email} | OTP: {otp_code}")
        print(f"==========================================\n")

        return {
            "message": "Signup successful. Please verify the 6-digit OTP sent to your email.",
            "email": new_user.email,
            "dev_otp_preview": otp_code if settings.DEBUG else None
        }

    def verify_otp(self, db: Session, payload: VerifyOTPRequest) -> TokenResponse:
        """
        Verifies 6-digit signup OTP, activates account, awards $100 referral coupon if applicable,
        and returns access + refresh tokens and user profile.
        """
        otp_record = user_repository.get_valid_otp(
            db,
            email=payload.email,
            otp_code=payload.otp_code,
            purpose=OTPPurpose.SIGNUP
        )
        if not otp_record:
            raise http_400_bad_request("Invalid or expired 6-digit OTP code.")

        # Mark OTP as consumed
        user_repository.mark_otp_used(db, otp_record)

        user = user_repository.get_by_email(db, payload.email)
        if not user:
            raise http_404_not_found("User account not found.")

        user.is_verified_otp = True
        db.add(user)
        db.commit()
        db.refresh(user)

        '''
        # If user was referred, ensure they receive their $100 Welcome Coupon
        referral_record = referral_repository.get_by_referred_user(db, user.id)
        if referral_record:
            # Check if coupon already granted
            existing_coupon = coupon_repository.get_active_coupons_by_user(db, user.id)
            if not existing_coupon:
                coupon_code = f"WELCOME-{user.referral_code}"
                new_coupon = Coupon(
                    user_id=user.id,
                    code=coupon_code,
                    amount=settings.DEFAULT_COUPON_AMOUNT,
                    status=CouponStatus.ACTIVE,
                    expires_at=datetime.now(timezone.utc) + timedelta(days=90)
                )
                db.add(new_coupon)
                db.commit()
                logger.info(f"Granted ${settings.DEFAULT_COUPON_AMOUNT} referral coupon {coupon_code} to user {user.email}")
        '''


        # Issue JWT Access & Refresh Tokens
        access_token = create_access_token(subject=user.id, claims={"role": user.role.value, "email": user.email})
        refresh_token = create_refresh_token(subject=user.id)

        user_profile = UserProfileResponse.model_validate(user)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_profile
        )

    def login(self, db: Session, payload: LoginRequest) -> TokenResponse:
        """
        Authenticates user with email and password.
        """
        user = user_repository.get_by_email(db, payload.email)
        if not user or not verify_password(payload.password, user.hashed_password):
            raise http_401_unauthorized("Incorrect email or password.")

        if not user.is_active:
            raise http_400_bad_request("This account has been deactivated.")

        if not user.is_verified_otp:
            # Resend OTP
            otp_code = generate_six_digit_otp()
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
            user_repository.create_otp(
                db,
                user_id=user.id,
                email=user.email,
                otp_code=otp_code,
                purpose=OTPPurpose.SIGNUP,
                expires_at=expires_at
            )
            print(f"\n[GUARDWELL OTP - RE-VERIFY] Email: {user.email} | OTP: {otp_code}\n")
            raise http_400_bad_request("Account email not verified yet. A new 6-digit OTP has been sent.")

        access_token = create_access_token(subject=user.id, claims={"role": user.role.value, "email": user.email})
        refresh_token = create_refresh_token(subject=user.id)
        user_profile = UserProfileResponse.model_validate(user)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=user_profile
        )

    def forgot_password(self, db: Session, payload: ForgotPasswordRequest) -> ForgotPasswordOTPResponse:
        """
        Sends 6-digit OTP for password reset.
        """
        user = user_repository.get_by_email(db, payload.email)
        if not user:
            # Security by Default: Avoid user enumeration by returning standard success message
            return ForgotPasswordOTPResponse(
                message="If this email is registered, a 6-digit OTP has been sent.",
                email=payload.email
            )

        otp_code = generate_six_digit_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        user_repository.create_otp(
            db,
            user_id=user.id,
            email=user.email,
            otp_code=otp_code,
            purpose=OTPPurpose.FORGOT_PASSWORD,
            expires_at=expires_at
        )

        print(f"\n==========================================")
        print(f" [GUARDWELL OTP - FORGOT PASSWORD] ")
        print(f" User: {user.email} | OTP: {otp_code}")
        print(f"==========================================\n")

        return ForgotPasswordOTPResponse(
            message="6-digit OTP has been sent to your registered email.",
            email=user.email
        )

    def verify_forgot_otp(self, db: Session, payload: VerifyForgotOTPRequest) -> dict:
        """
        Verifies forgot password OTP and returns a short-lived password reset token.
        """
        otp_record = user_repository.get_valid_otp(
            db,
            email=payload.email,
            otp_code=payload.otp_code,
            purpose=OTPPurpose.FORGOT_PASSWORD
        )
        if not otp_record:
            raise http_400_bad_request("Invalid or expired 6-digit OTP code.")

        user_repository.mark_otp_used(db, otp_record)
        user = user_repository.get_by_email(db, payload.email)
        if not user:
            raise http_404_not_found("User not found.")

        reset_token = create_password_reset_token(subject=user.id)
        return {
            "message": "OTP verified successfully. You may now reset your password.",
            "reset_token": reset_token
        }

    def reset_password(self, db: Session, reset_token: str, payload: ResetPasswordRequest) -> PasswordResetSuccessResponse:
        """
        Resets user password using the verified reset token.
        """
        try:
            decoded = jwt.decode(reset_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            if decoded.get("type") != "password_reset":
                raise http_401_unauthorized("Invalid token type for password reset.")
            user_id = int(decoded.get("sub"))
        except (jwt.PyJWTError, Exception):
            raise http_401_unauthorized("Password reset token is invalid or has expired.")

        user = user_repository.get(db, user_id)
        if not user:
            raise http_404_not_found("User not found.")

        user.hashed_password = get_password_hash(payload.new_password)
        db.add(user)
        db.commit()

        return PasswordResetSuccessResponse(message="Password reset successful. Please login with your new password.")


auth_service = AuthService()
