from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ==========================================
# CUSTOMER MANAGEMENT SCHEMAS
# ==========================================

class AdminCustomerListItem(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_number: str
    joined_date: datetime
    bookings_count: int
    status: str  # "Verified" or "New"
    is_verified_customer: bool
    is_feed_banned: bool
    image_url: Optional[str] = None
    referral_code: str
    payout_email: Optional[str] = None
    payout_phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdminCustomerDetail(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_number: str
    role: str
    referral_code: str
    image_url: Optional[str] = None
    is_verified_otp: bool
    is_verified_customer: bool
    is_feed_banned: bool
    payout_email: Optional[str] = None
    payout_phone: Optional[str] = None
    created_at: datetime
    bookings_count: int
    quotes: List[dict] = []

    model_config = ConfigDict(from_attributes=True)


class CustomerStatusUpdate(BaseModel):
    is_verified_customer: Optional[bool] = None
    is_feed_banned: Optional[bool] = None


# ==========================================
# SERVICE TICKET UPDATE SCHEMA
# ==========================================

class AdminTicketStatusUpdate(BaseModel):
    status: str = Field(..., description="submitted, in_progress, completed")
    assigned_rep: Optional[str] = None


# ==========================================
# REFERRAL & COUPON SCHEMAS
# ==========================================

class ReferralBonusItem(BaseModel):
    id: int
    referrer_name: str
    referrer_email: str
    referral_code: str
    qualified_date: datetime
    bonus: float
    status: str  # "Paid" or "Pending"
    bonus_status: str

    model_config = ConfigDict(from_attributes=True)


class ReferralBonusStatusUpdate(BaseModel):
    bonus_status: str = Field(..., description="pending or paid")


class CouponAmountResponse(BaseModel):
    coupon_amount: float
    description: Optional[str] = "Current referral coupon reward amount"


class CouponAmountUpdate(BaseModel):
    coupon_amount: float = Field(..., gt=0, description="New coupon reward amount")


# ==========================================
# USER REPORT SCHEMAS
# ==========================================

class AdminReportListItem(BaseModel):
    id: int
    report_id: int
    reported_text: str
    author_name: str
    reporter_name: str
    reason: str
    created_at: datetime
    post_id: int
    report_code: str
    status: str = "Open"

    model_config = ConfigDict(from_attributes=True)


class AdminReportAction(BaseModel):
    action: str = Field(..., description="'delete_post' or 'dismiss_report'")


# ==========================================
# DASHBOARD OVERVIEW SCHEMA
# ==========================================

class DashboardOverviewResponse(BaseModel):
    total_customers: int
    open_tickets: int
    urgent_tickets: int
    referral_rewards: float
    pending_rewards_count: int
    service_overview_days: List[dict]
    latest_service_tickets: List[dict]
    recent_activity: List[dict]

