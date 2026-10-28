"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Polymorphic Service Categories & Type Discrimination:
   - QuoteType (Get a Free Quote vs Request a Service) এবং 9টি Service Categories কে
     স্ট্রিং এনাম হিসেবে মডেল করা হয়েছে যা ফর্মে এবং এপিআইতে টাইপ-সেফটি নিশ্চিত করে।
2. Notification Recipient Configuration (Observer Pattern Support):
   - নোটিফিকেশন রিসিভ করার ইমেইল তালিকা ডেটাবেজে ডাইনামিক করা হয়েছে, যেন অ্যাডমিন
     টিম কোড পরিবর্তন ছাড়াই প্রাপকদের যুক্ত/মুছে ফেলতে পারে (OCP - Open/Closed Principle)।
3. Relationship with Coupons:
   - কুপন সরাসরি কোটের সাথে লিংকড থাকে যা ট্র্যাক করে কোন ডিসকাউন্টটি প্রয়োগ করা হয়েছে।
================================================================================
"""

import enum
from sqlalchemy import Column, String, Text, Enum, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedModel


class QuoteType(str, enum.Enum):
    GET_A_FREE_QUOTE = "get_a_free_quote"
    REQUEST_A_SERVICE = "request_a_service"


class ServiceCategory(str, enum.Enum):
    GUTTER_REPLACEMENT = "gutter_replacement"
    GUTTER_GUARD = "gutter_guard"
    SOFFIT = "soffit"
    FASCIA = "fascia"
    ROOFING = "roofing"
    FENCING = "fencing"
    SIDING = "siding"
    SOFT_WASH = "soft_wash"
    GUTTER_CLEAN = "gutter_clean"


class QuoteStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Quote(TimeStampedModel):
    __tablename__ = "quotes"

    # Associated user (if authenticated customer)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    type = Column(Enum(QuoteType), nullable=False, index=True)
    service_category = Column(Enum(ServiceCategory), nullable=False, index=True)

    # Contact & Property Information
    name = Column(String(120), nullable=False)
    phone_number = Column(String(50), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    postcode = Column(String(20), nullable=False)
    full_address = Column(Text, nullable=False)
    description = Column(Text, nullable=False)

    # Media attachments (Photos/Videos of the house or issue)
    image_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)

    # Optional Coupon applied for $100 discount
    #coupon_id = Column(Integer, ForeignKey("coupons.id", ondelete="SET NULL"), nullable=True, index=True)

    # Ticket Lifecycle Management
    status = Column(Enum(QuoteStatus), default=QuoteStatus.SUBMITTED, nullable=False, index=True)
    assigned_rep = Column(String(120), nullable=True)

    # Relationships
    user = relationship("User", back_populates="quotes")
    coupon = relationship("Coupon", back_populates="quotes")


class NotificationRecipient(TimeStampedModel):
    """
    Team members who automatically receive email notifications when forms are submitted.
    """
    __tablename__ = "notification_recipients"

    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
