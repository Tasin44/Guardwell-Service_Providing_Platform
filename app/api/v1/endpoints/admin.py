"""
================================================================================
ADMIN API ROUTER:
Dedicated, clean endpoints matching the Admin Dashboard UI pages:
1. Overview:
   - GET /api/v1/admin/dashboard/overview
2. Customers:
   - GET   /api/v1/admin/customers
   - GET   /api/v1/admin/customers/{user_id}
   - PATCH /api/v1/admin/customers/{user_id}/status
3. Service Tickets:
   - GET   /api/v1/admin/tickets
   - PATCH /api/v1/admin/tickets/{ticket_id}/status
4. Referrals & Coupons:
   - GET   /api/v1/admin/referrals
   - PATCH /api/v1/admin/referrals/{referral_id}/status
   - GET   /api/v1/admin/coupons/amount
   - POST  /api/v1/admin/coupons/amount
5. User Reports (Feed Moderation):
   - GET   /api/v1/admin/reports
   - POST  /api/v1/admin/reports/{report_id}/action
================================================================================
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_admin
from app.models.user import User
from app.services.admin_service import admin_service
from app.schemas.admin import (
    AdminCustomerListItem,
    AdminCustomerDetail,
    CustomerStatusUpdate,
    AdminTicketStatusUpdate,
    ReferralBonusItem,
    ReferralBonusStatusUpdate,
    CouponAmountResponse,
    CouponAmountUpdate,
    AdminReportListItem,
    AdminReportAction,
    DashboardOverviewResponse,
)

router = APIRouter()


# ==========================================
# 1. DASHBOARD OVERVIEW
# ==========================================

@router.get(
    "/dashboard/overview",
    response_model=DashboardOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin] Get Complete Dashboard Overview Stats & Graphs"
)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Returns live counters for Total Customers, Open Tickets,
    Referral Rewards, 7-day request trends, latest tickets, and recent activity.
    """
    return admin_service.get_dashboard_overview(db)


# ==========================================
# 2. CUSTOMER MANAGEMENT
# ==========================================

@router.get(
    "/customers",
    response_model=List[AdminCustomerListItem],
    status_code=status.HTTP_200_OK,
    summary="[Admin] List All Customers with Bookings Count & Status"
)
def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Lists all customers with profile details, joined date, bookings count, and verified/new status.
    """
    return admin_service.get_all_customers(db, skip=skip, limit=limit, search=search)


@router.get(
    "/customers/{user_id}",
    response_model=AdminCustomerDetail,
    status_code=status.HTTP_200_OK,
    summary="[Admin] Get Full Customer Profile & Their Submitted Tickets"
)
def get_customer_detail(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Returns full individual customer profile details and history of tickets submitted.
    """
    return admin_service.get_customer_detail(db, user_id=user_id)


@router.patch(
    "/customers/{user_id}/status",
    response_model=AdminCustomerDetail,
    status_code=status.HTTP_200_OK,
    summary="[Admin] Update Customer Verification Badge or Feed Ban"
)
def update_customer_status(
    user_id: int,
    payload: CustomerStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Allows admin to verify a customer or restrict them from community feed.
    """
    return admin_service.update_customer_status(
        db,
        user_id=user_id,
        is_verified_customer=payload.is_verified_customer,
        is_feed_banned=payload.is_feed_banned
    )


# ==========================================
# 3. SERVICE / TICKET MANAGEMENT
# ==========================================

@router.get(
    "/tickets",
    status_code=status.HTTP_200_OK,
    summary="[Admin] List All Submitted Tickets/Requests with Details & Media"
)
def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter: submitted, in_progress, completed"),
    search: Optional[str] = Query(None, description="Search by customer name, email, phone, postcode, or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Returns all submitted service tickets with customer info, media photos/videos, and status.
    """
    return admin_service.get_all_tickets(
        db,
        status=status_filter,
        search=search,
        skip=skip,
        limit=limit
    )


@router.patch(
    "/tickets/{ticket_id}/status",
    status_code=status.HTTP_200_OK,
    summary="[Admin] Update Ticket Status & Assign Representative"
)
def update_ticket_status(
    ticket_id: int,
    payload: AdminTicketStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Updates ticket status (e.g. submitted -> in_progress -> completed) and representative.
    """
    return admin_service.update_ticket_status(
        db,
        ticket_id=ticket_id,
        status_value=payload.status,
        assigned_rep=payload.assigned_rep
    )


# ==========================================
# 4. REFERRALS & COUPON MANAGEMENT
# ==========================================

@router.get(
    "/referrals",
    response_model=List[ReferralBonusItem],
    status_code=status.HTTP_200_OK,
    summary="[Admin] List All Referrals, Qualified Dates, and Bonus Status"
)
def list_referrals(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Returns all referral records with Referrer, Referral Code, Qualified signup date, Bonus amount, and Status.
    """
    return admin_service.get_all_referrals(db, skip=skip, limit=limit)


@router.patch(
    "/referrals/{referral_id}/status",
    status_code=status.HTTP_200_OK,
    summary="[Admin] Mark Referral Bonus as Paid or Pending"
)
def update_referral_status(
    referral_id: int,
    payload: ReferralBonusStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Marks a pending referral reward as paid once processed.
    """
    return admin_service.update_referral_bonus_status(
        db,
        referral_id=referral_id,
        bonus_status_value=payload.bonus_status
    )


@router.get(
    "/coupons/amount",
    response_model=CouponAmountResponse,
    status_code=status.HTTP_200_OK,
    summary="[Admin/Public] Get Current Global Referral Coupon Reward Amount"
)
def get_coupon_amount(
    db: Session = Depends(get_db)
):
    """
    Returns the current global referral coupon amount (e.g. $100) visible in the app for all users.
    """
    amount = admin_service.get_coupon_amount(db)
    return CouponAmountResponse(coupon_amount=amount)


@router.post(
    "/coupons/amount",
    status_code=status.HTTP_200_OK,
    summary="[Admin] Update Referral Coupon Reward Amount"
)
def set_coupon_amount(
    payload: CouponAmountUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Changes global referral coupon amount. Updated value immediately reflects across the platform.
    """
    return admin_service.set_coupon_amount(db, amount=payload.coupon_amount)


# ==========================================
# 5. USER REPORTS (FEED MODERATION)
# ==========================================

@router.get(
    "/reports",
    response_model=List[AdminReportListItem],
    status_code=status.HTTP_200_OK,
    summary="[Admin] List All Reported Community Posts"
)
def list_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Returns reported posts with reason, original content, author, and reporter for moderation.
    """
    return admin_service.get_all_reports(db, skip=skip, limit=limit)


@router.post(
    "/reports/{report_id}/action",
    status_code=status.HTTP_200_OK,
    summary="[Admin] Take Step on Reported Post (delete_post or dismiss_report)"
)
def handle_report_action(
    report_id: int,
    payload: AdminReportAction,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """
    Applies admin action:
    - action='delete_post': deletes post permanently.
    - action='dismiss_report': marks as resolved and keeps post intact.
    """
    return admin_service.handle_report_action(db, report_id=report_id, action=payload.action)

