"""
================================================================================
REFERRAL & COUPON SYSTEM MODELS:
1. Referral:
   - Tracks referrer and referred customer.
   - qualified_at tracks the date the referred user completed registration.
   - status: SIGNED_UP, BOOKED, COMPLETED
   - bonus_status: PENDING, PAID
2. SystemSetting:
   - Dynamic key-value pairs (e.g. coupon_amount) editable by Admin.
================================================================================
"""

import enum
from datetime import datetime
from sqlalchemy import Column, String, Float, Enum, ForeignKey, Integer, DateTime
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedModel


class ReferralStatus(str, enum.Enum):
    SIGNED_UP = "signed_up"
    BOOKED = "booked"
    COMPLETED = "completed"


class BonusStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"


class Referral(TimeStampedModel):
    __tablename__ = "referrals"

    referrer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referral_code = Column(String(30), nullable=False, index=True)
    bonus_amount = Column(Float, default=100.0, nullable=False)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.SIGNED_UP, nullable=False, index=True)
    bonus_status = Column(Enum(BonusStatus), default=BonusStatus.PENDING, nullable=False, index=True)
    qualified_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], backref="referrals_given")
    referred_user = relationship("User", foreign_keys=[referred_user_id], backref="referrals_received")


class SystemSetting(TimeStampedModel):
    __tablename__ = "system_settings"

    key = Column(String(100), unique=True, index=True, nullable=False)
    value = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)

