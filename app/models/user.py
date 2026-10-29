
"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. High Cohesion & Single Responsibility:
   - User মডেল ব্যবহারকারীর আইডেন্টিটি, রোল ও প্রোফাইল ধারণ করে।
   - OTPVerification মডেল আলাদা রাখা হয়েছে SoC মেনে ওটিপি হ্যান্ডলিংয়ের জন্য।
2. Database Indexing & Query Optimization:
   - email, phone_number এবং referral_code ইউনিক এবং ইনডেক্সড, যা দ্রুত লুকআপ নিশ্চিত করে।
3. Role-Based Access Control (RBAC):
   - Enum-ভিত্তিক রোল (admin, customer) নিশ্চিত করে প্রেজেন্টেশন ও সিকিউরিটি লেয়ারে পরিষ্কার অথরাইজেশন।
================================================================================
"""

# from sys.__jit import is_active
# from sqlalchemy import null
# from _winapi import TerminateProcess
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Enum, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedModel


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    CUSTOMER = "customer"


class OTPPurpose(str, enum.Enum):
    SIGNUP = "signup"
    FORGOT_PASSWORD = "forgot_password"

class User(TimeStampedModel):
    __tablename__ = "users"

    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone_number = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)

    # Unique 8-character referral code generated for each user
    referral_code = Column(String(20), unique=True, index=True, nullable=False)

    # Profile & Status fields
    image_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified_otp = Column(Boolean, default=False, nullable=False)

    # Relationships (Composition & Association)
    # referrals_given = relationship("Referral", foreign_keys="Referral.referrer_id", back_populates="referrer", cascade="all, delete-orphan")
    # referrals_received = relationship("Referral", foreign_keys="Referral.referred_user_id", back_populates="referred_user")

    quotes = relationship("Quote", back_populates="user")#❓what does backpulates means here
    posts = relationship("FeedPost", back_populates="user", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    reactions = relationship("CommentReaction", back_populates="user", cascade="all, delete-orphan")
    otps = relationship("OTPVerification", back_populates="user", cascade="all, delete-orphan")




class OTPVerification(TimeStampedModel):
    __tablename__ = "otp_verifications"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    otp_code = Column(String(6), nullable=False)
    purpose = Column(Enum(OTPPurpose), nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="otps")

    @property
    def is_expired(self) -> bool:
        """Helper to quickly evaluate OTP expiration."""
        return datetime.now(timezone.utc) > self.expires_at.replace(tzinfo=timezone.utc)























