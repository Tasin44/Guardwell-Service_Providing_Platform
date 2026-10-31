"""
================================================================================
FASTAPI SCHEMAS VS DRF SERIALIZERS (QUOTES & INSPECTION TICKETS):
1. Comprehensive Form Validation:
   - Postal code, phone number, email, and service category are validated strictly.
2. Service Categories:
   - 9টি সুনির্দিষ্ট সার্ভিস ক্যাটাগরি এবং 2টি টাইপ (Get a free quote / Request a service)
     টাইপ-সেফ এনোটেশনে আবদ্ধ।
3. DRF Serializer Method Field Equivalence:
   - Pydantic-এ @computed_field বা মেথড দিয়ে অতিরিক্ত ক্যালকুলেটেড ফিল্ড তৈরি করা যায়।
================================================================================
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from app.models.quote import QuoteType, ServiceCategory, QuoteStatus


class QuoteCreateRequest(BaseModel):
    """
    Validation schema for submitting a quote or service ticket.
    """
    type: QuoteType = Field(..., description="Get_a_free_quote or request_a_service")
    service_category: ServiceCategory = Field(..., description="Service category required")
    name: str = Field(..., min_length=2, max_length=120)
    phone_number: str = Field(..., min_length=7, max_length=30)
    email: EmailStr
    postcode: str = Field(..., min_length=2, max_length=20)
    full_address: str = Field(..., min_length=5)
    description: str = Field(..., min_length=5)
    coupon_code: Optional[str] = Field(None, description="Optional $100 referral coupon code")


class QuoteResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    type: QuoteType
    service_category: ServiceCategory
    name: str
    phone_number: str
    email: EmailStr
    postcode: str
    full_address: str
    description: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    coupon_id: Optional[int] = None
    status: QuoteStatus
    assigned_rep: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QuoteStatusUpdateRequest(BaseModel):
    status: QuoteStatus
    assigned_rep: Optional[str] = None


class NotificationRecipientCreate(BaseModel):
    name: str
    email: EmailStr


class NotificationRecipientResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
