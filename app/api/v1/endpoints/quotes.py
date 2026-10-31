"""
================================================================================
FASTAPI ROUTER: QUOTES & SERVICE TICKETS
1. Multi-part Form Submission (with file/video upload support)
2. Dual Routing Support:
   - Authenticated and Guest Users can both submit quotes/tickets.
3. Admin Lifecycle Management:
   - Filter quotes, update status, and assign reps.
================================================================================
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, get_current_admin, get_optional_current_user
from app.models.user import User
from app.models.quote import QuoteType, ServiceCategory, QuoteStatus
from app.schemas.quote import (
    QuoteResponse,
    QuoteStatusUpdateRequest,
    NotificationRecipientCreate,
    NotificationRecipientResponse,
)
from app.services.quote_service import quote_service
from app.repositories.quote_repository import quote_repository, notification_recipient_repository
from app.core.exceptions import http_400_bad_request, http_404_not_found

router = APIRouter()


@router.post(
    "/create",
    response_model=QuoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a Quote or Service Request (Multipart Form with Media Uploads)"
)
async def create_quote(
    type: QuoteType = Form(..., description="get_a_free_quote or request_a_service"),
    service_category: ServiceCategory = Form(..., description="Service category"),
    name: str = Form(..., min_length=2, max_length=120),
    phone_number: str = Form(..., min_length=7, max_length=30),
    email: str = Form(...),
    postcode: str = Form(..., min_length=2, max_length=20),
    full_address: str = Form(..., min_length=5),
    description: str = Form(..., min_length=5),
    coupon_code: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None, description="Optional property photo"),
    video: Optional[UploadFile] = File(None, description="Optional property video"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    """
    Submits a new quote request or service ticket.
    Supports file uploads (photo/video), coupon codes, and notifies the team.
    """
    return await quote_service.create_quote(
        db,
        current_user=current_user,
        type=type,
        service_category=service_category,
        name=name,
        phone_number=phone_number,
        email=email,
        postcode=postcode,
        full_address=full_address,
        description=description,
        coupon_code=coupon_code,
        image_file=image,
        video_file=video,
    )


@router.get(
    "/my-quotes",
    response_model=List[QuoteResponse],
    summary="Get Current User's Submitted Quotes & Tickets"
)
def get_my_quotes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves all quotes/tickets submitted by the logged-in customer.
    """
    return quote_repository.get_by_user(db, user_id=current_user.id)


@router.get(
    "/{quote_id}",
    response_model=QuoteResponse,
    summary="Get Quote Details by ID"
)
def get_quote(
    quote_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetches details of a specific quote. Accessible by the quote owner or admin.
    """
    quote = quote_repository.get(db, quote_id)
    if not quote:
        raise http_404_not_found(f"Quote with ID {quote_id} not found.")

    if quote.user_id != current_user.id and current_user.role.value != "admin":
        raise http_404_not_found(f"Quote with ID {quote_id} not found.")

    return quote


@router.patch(
    "/{quote_id}/status",
    response_model=QuoteResponse,
    summary="[Admin] Update Quote / Service Ticket Status"
)
def update_quote_status(
    quote_id: int,
    payload: QuoteStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Admin-only endpoint to update ticket lifecycle status and assign representative.
    """
    return quote_service.update_quote_status(db, quote_id=quote_id, payload=payload)


@router.get(
    "/admin/all",
    response_model=List[QuoteResponse],
    summary="[Admin] List All Quotes with Status and Type Filters"
)
def get_all_quotes_admin(
    status: Optional[QuoteStatus] = Query(None),
    type: Optional[QuoteType] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Lists all quotes in system with optional filtering and pagination.
    """
    return quote_repository.get_all_with_filters(
        db,
        status=status,
        type=type,
        skip=skip,
        limit=limit
    )


# ==========================================
# Notification Recipients Management
# ==========================================

@router.get(
    "/recipients/all",
    response_model=List[NotificationRecipientResponse],
    summary="[Admin] List All Alert Notification Recipients"
)
def get_notification_recipients(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return notification_recipient_repository.get_active_recipients(db)


@router.post(
    "/recipients/create",
    response_model=NotificationRecipientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="[Admin] Add a Notification Recipient for Service Alerts"
)
def create_notification_recipient(
    payload: NotificationRecipientCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    existing = notification_recipient_repository.get_by_email(db, payload.email)
    if existing:
        raise http_400_bad_request("A notification recipient with this email already exists.")

    recipient = notification_recipient_repository.create(
        db,
        obj_in={
            "name": payload.name,
            "email": payload.email.strip().lower(),
            "is_active": True,
        }
    )
    return recipient
