"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. High Cohesion & Single Responsibility:
   - UserRepository শুধুমাত্র User এবং OTPVerification টেবিল সংক্রান্ত কুয়েরির দায়িত্বে থাকবে।
2. Optimization:
   - Query Filter এ indexed columns (email, phone_number, referral_code) ব্যবহার করা হয়েছে।
================================================================================
"""

from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.user import User, OTPVerification, OTPPurpose


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """Fetch user by unique email address."""
        return db.query(User).filter(User.email == email.strip().lower()).first()

    def get_by_phone(self, db: Session, phone_number: str) -> Optional[User]:
        """Fetch user by contact phone number."""
        return db.query(User).filter(User.phone_number == phone_number.strip()).first()

    def get_by_referral_code(self, db: Session, referral_code: str) -> Optional[User]:
        """Fetch user by their unique referral code."""
        return db.query(User).filter(User.referral_code == referral_code.strip().upper()).first()

    def create_otp(
        self,
        db: Session,
        *,
        email: str,
        otp_code: str,
        purpose: OTPPurpose,
        expires_at: datetime,
        user_id: Optional[int] = None,
        payload: Optional[str] = None
    ) -> OTPVerification:
        """Stores a new OTP record."""
        otp_record = OTPVerification(
            user_id=user_id,
            email=email.strip().lower(),
            otp_code=otp_code,
            purpose=purpose,
            payload=payload,
            expires_at=expires_at,
            is_used=False
        )
        db.add(otp_record)
        db.commit()
        db.refresh(otp_record)
        return otp_record

    def get_valid_otp(
        self,
        db: Session,
        *,
        email: str,
        otp_code: str,
        purpose: OTPPurpose
    ) -> Optional[OTPVerification]:
        """
        Retrieves an unused, unexpired OTP for the specified email and purpose.
        """
        now = datetime.now(timezone.utc)
        return (
            db.query(OTPVerification)
            .filter(
                OTPVerification.email == email.strip().lower(),
                OTPVerification.otp_code == otp_code,
                OTPVerification.purpose == purpose,
                OTPVerification.is_used == False,
                OTPVerification.expires_at > now
            )
            .order_by(OTPVerification.created_at.desc())
            .first()
        )

    def mark_otp_used(self, db: Session, otp_record: OTPVerification) -> None:
        """Marks an OTP record as consumed."""
        otp_record.is_used = True
        db.add(otp_record)
        db.commit()


# Singleton Repository Instance
user_repository = UserRepository()
