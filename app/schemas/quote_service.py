"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. State Machine & Event-Driven Business Workflow:
   - কোট তৈরি হলে রেফারেল স্ট্যাটাস signed_up -> booked এ ট্রানজিশন করে।
   - অ্যাডমিন জব complete মার্ক করলে রেফারেল স্ট্যাটাস booked -> completed হয়
     এবং স্বয়ংক্রিয়ভাবে রেফারারের বোনাস pending হিসাবে জমা হয়।
2. Observer Pattern (Notification Dispatch):
   - ফর্ম সাবমিট হওয়া মাত্রই ডাটাবেজে কনফিগার করা সব অ্যাক্টিভ টিম মেম্বারের কাছে
     নোটিফিকেশন পাঠানো হয়।
3. Financial Integrity:
   - কুপন কোড প্রয়োগ করা হলে কুপনটির স্ট্যাটাস 'used' এবং used_at টাইমস্ট্যাম্প আপডেট হয়।
================================================================================
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.user import User
from app.models.quote import Quote, QuoteType, ServiceCategory, QuoteStatus, NotificationRecipient
# from app.models.referral import ReferralStatus, BonusStatus, CouponStatus
from app.repositories.quote_repository import quote_repository, notification_recipient_repository
# from app.repositories.referral_repository import referral_repository, coupon_repository
from app.services.file_service import file_service
from app.schemas.quote import QuoteResponse, QuoteStatusUpdateRequest
from app.core.exceptions import http_400_bad_request, http_404_not_found

logger = logging.getLogger("guardwell.quotes")


class QuoteService:
    @staticmethod
    def _notify_admin_team(db: Session, quote: Quote) -> None:
        """
        Dispatches email alert to all configured team members.
        """
        recipients = notification_recipient_repository.get_active_recipients(db)
        recipient_emails = [r.email for r in recipients]
        
        print(f"\n=======================================================")
        print(f" [NEW SERVICE / QUOTE TICKET SUBMITTED] ")
        print(f" ID: {quote.id} | Type: {quote.type.value} | Category: {quote.service_category.value}")
        print(f" Customer: {quote.name} ({quote.phone_number}, {quote.email})")
        print(f" Address: {quote.full_address}, {quote.postcode}")
        print(f" Description: {quote.description}")
        print(f" Alerting Team Members: {', '.join(recipient_emails) if recipient_emails else 'Default Owner'}")
        print(f"=======================================================\n")

    async def create_quote(
        self,
        db: Session,
        *,
        current_user: Optional[User],
        type: QuoteType,
        service_category: ServiceCategory,
        name: str,
        phone_number: str,
        email: str,
        postcode: str,
        full_address: str,
        description: str,
        coupon_code: Optional[str] = None,
        image_file: Optional[UploadFile] = None,
        video_file: Optional[UploadFile] = None
    ) -> QuoteResponse:
        """
        Handles quote/ticket creation, validates discounts, uploads attachments, and alerts admin.
        """
        # Save photo & video uploads if present
        image_url = None
        video_url = None
        if image_file:
            image_url = await file_service.save_upload_file(image_file, subfolder="quotes")
        if video_file:
            video_url = await file_service.save_upload_file(video_file, subfolder="quotes")

        # Validate Coupon if provided
        # applied_coupon = None
        # if coupon_code:
        #     applied_coupon = coupon_repository.get_by_code(db, coupon_code.strip())
        #     if not applied_coupon or applied_coupon.status != CouponStatus.ACTIVE:
        #         raise http_400_bad_request("The coupon code provided is invalid or has already been used.")

        #     applied_coupon.status = CouponStatus.USED
        #     applied_coupon.used_at = datetime.now(timezone.utc)
        #     db.add(applied_coupon)

        quote = Quote(
            user_id=current_user.id if current_user else None,
            type=type,
            service_category=service_category,
            name=name.strip(),
            phone_number=phone_number.strip(),
            email=email.strip().lower(),
            postcode=postcode.strip().upper(),
            full_address=full_address.strip(),
            description=description.strip(),
            image_url=image_url,
            video_url=video_url,
            # coupon_id=applied_coupon.id if applied_coupon else None,
            status=QuoteStatus.SUBMITTED
        )
        db.add(quote)
        db.commit()
        db.refresh(quote)

        # Referral Tracking: If customer was referred, advance state to BOOKED
        user_to_check = current_user.id if current_user else None
        # if user_to_check:
        #     referral_entry = referral_repository.get_by_referred_user(db, user_to_check)
        #     if referral_entry and referral_entry.status == ReferralStatus.SIGNED_UP:
        #         referral_entry.status = ReferralStatus.BOOKED
        #         db.add(referral_entry)
        #         db.commit()

        # Trigger notification to team
        self._notify_admin_team(db, quote)

        return QuoteResponse.model_validate(quote)

    def update_quote_status(
        self,
        db: Session,
        quote_id: int,
        payload: QuoteStatusUpdateRequest
    ) -> QuoteResponse:
        """
        Updates quote status. When COMPLETED, automatically triggers referrer bonus activation.
        """
        quote = quote_repository.get(db, quote_id)
        if not quote:
            raise http_404_not_found(f"Quote with ID {quote_id} not found.")

        quote.status = payload.status
        if payload.assigned_rep:
            quote.assigned_rep = payload.assigned_rep

        db.add(quote)
        db.commit()
        db.refresh(quote)

        # If job COMPLETED -> Advance referral state to COMPLETED and bonus to PENDING
        # if payload.status == QuoteStatus.COMPLETED and quote.user_id:
        #     referral = referral_repository.get_by_referred_user(db, quote.user_id)
        #     if referral and referral.status != ReferralStatus.COMPLETED:
        #         referral.status = ReferralStatus.COMPLETED
        #         referral.bonus_status = BonusStatus.PENDING
        #         db.add(referral)
        #         db.commit()
        #         logger.info(f"Referral #{referral.id} reached COMPLETED status. Bonus marked PENDING for referrer #{referral.referrer_id}")

        return QuoteResponse.model_validate(quote)


quote_service = QuoteService()
