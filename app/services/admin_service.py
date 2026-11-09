"""
================================================================================
ADMIN SERVICE:
Encapsulates all business logic for:
1. Customer Management (List, Detail, Verify, Ban)
2. Service Ticket Management (List all, Filter, Update status, Rep assignment)
3. Referral & Coupon Management (List bonuses, Mark Paid/Pending, Dynamic Coupon Value)
4. User Reports Moderation (Review reports, Delete post, Dismiss report)
5. Dashboard Overview Metrics (Total customers, Open tickets, Referral rewards, Graphs)
================================================================================
"""

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.core.config import settings
from app.core.exceptions import http_400_bad_request, http_404_not_found
from app.models.user import User, UserRole
from app.models.quote import Quote, QuoteStatus
from app.models.feed import FeedPost, PostReport, Comment
from app.models.referral import Referral, ReferralStatus, BonusStatus, SystemSetting
from app.services.file_service import file_service
from app.schemas.admin import (
    AdminCustomerListItem,
    AdminCustomerDetail,
    ReferralBonusItem,
    AdminReportListItem,
    DashboardOverviewResponse,
)


class AdminService:
    # ==========================================
    # 1. CUSTOMER MANAGEMENT
    # ==========================================

    def get_all_customers(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50,
        search: Optional[str] = None
    ) -> List[AdminCustomerListItem]:
        """
        Lists all customer users with bookings count and status (Verified / New).
        """
        query = db.query(User).filter(User.role == UserRole.CUSTOMER)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (User.name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.phone_number.ilike(search_term))
            )

        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        results: List[AdminCustomerListItem] = []

        for u in users:
            bookings_count = db.query(func.count(Quote.id)).filter(Quote.user_id == u.id).scalar() or 0
            status_label = "Verified" if u.is_verified_customer else "New"

            results.append(
                AdminCustomerListItem(
                    id=u.id,
                    name=u.name,
                    email=u.email,
                    phone_number=u.phone_number,
                    joined_date=u.created_at,
                    bookings_count=bookings_count,
                    status=status_label,
                    is_verified_customer=u.is_verified_customer,
                    is_feed_banned=u.is_feed_banned,
                    image_url=file_service.get_full_url(u.image_url),
                    referral_code=u.referral_code,
                    payout_email=u.payout_email,
                    payout_phone=u.payout_phone,
                )
            )
        return results

    def get_customer_detail(self, db: Session, user_id: int) -> AdminCustomerDetail:
        """
        Retrieves detailed profile of a single customer, including all tickets submitted.
        """
        user = db.query(User).filter(User.id == user_id, User.role == UserRole.CUSTOMER).first()
        if not user:
            raise http_404_not_found(f"Customer with ID {user_id} not found.")

        quotes = db.query(Quote).filter(Quote.user_id == user_id).order_by(Quote.created_at.desc()).all()
        quotes_list = [
            {
                "id": q.id,
                "type": q.type.value if hasattr(q.type, "value") else str(q.type),
                "service_category": q.service_category.value if hasattr(q.service_category, "value") else str(q.service_category),
                "name": q.name,
                "phone_number": q.phone_number,
                "email": q.email,
                "postcode": q.postcode,
                "full_address": q.full_address,
                "description": q.description,
                "image_url": file_service.get_full_url(q.image_url),
                "video_url": file_service.get_full_url(q.video_url),
                "status": q.status.value if hasattr(q.status, "value") else str(q.status),
                "assigned_rep": q.assigned_rep,
                "created_at": q.created_at.isoformat() if q.created_at else None,
            }
            for q in quotes
        ]

        return AdminCustomerDetail(
            id=user.id,
            name=user.name,
            email=user.email,
            phone_number=user.phone_number,
            role=user.role.value if hasattr(user.role, "value") else str(user.role),
            referral_code=user.referral_code,
            image_url=file_service.get_full_url(user.image_url),
            is_verified_otp=user.is_verified_otp,
            is_verified_customer=user.is_verified_customer,
            is_feed_banned=user.is_feed_banned,
            payout_email=user.payout_email,
            payout_phone=user.payout_phone,
            created_at=user.created_at,
            bookings_count=len(quotes_list),
            quotes=quotes_list,
        )

    def update_customer_status(
        self,
        db: Session,
        user_id: int,
        *,
        is_verified_customer: Optional[bool] = None,
        is_feed_banned: Optional[bool] = None
    ) -> AdminCustomerDetail:
        """
        Updates customer verification badge or bans/unbans from social feed.
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise http_404_not_found(f"Customer with ID {user_id} not found.")

        if is_verified_customer is not None:
            user.is_verified_customer = is_verified_customer
        if is_feed_banned is not None:
            user.is_feed_banned = is_feed_banned

        db.add(user)
        db.commit()
        db.refresh(user)
        return self.get_customer_detail(db, user_id)

    # ==========================================
    # 2. SERVICE TICKET MANAGEMENT
    # ==========================================

    def get_all_tickets(
        self,
        db: Session,
        *,
        status: Optional[str] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[dict]:
        """
        Fetches all submitted service tickets with individual customer details,
        media attachments (photos/videos), and status.
        """
        query = db.query(Quote).options(joinedload(Quote.user))

        if status:
            status_clean = status.strip().lower()
            if status_clean in [s.value for s in QuoteStatus]:
                query = query.filter(Quote.status == QuoteStatus(status_clean))

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                (Quote.name.ilike(search_term)) |
                (Quote.email.ilike(search_term)) |
                (Quote.phone_number.ilike(search_term)) |
                (Quote.description.ilike(search_term)) |
                (Quote.postcode.ilike(search_term))
            )

        quotes = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()

        results = []
        for q in quotes:
            results.append({
                "id": q.id,
                "request_code": f"REQ-{q.id + 2450}",
                "user_id": q.user_id,
                "customer_name": q.name,
                "customer_email": q.email,
                "customer_phone": q.phone_number,
                "type": q.type.value if hasattr(q.type, "value") else str(q.type),
                "service_category": q.service_category.value if hasattr(q.service_category, "value") else str(q.service_category),
                "postcode": q.postcode,
                "full_address": q.full_address,
                "description": q.description,
                "image_url": file_service.get_full_url(q.image_url),
                "video_url": file_service.get_full_url(q.video_url),
                "status": q.status.value if hasattr(q.status, "value") else str(q.status),
                "assigned_rep": q.assigned_rep,
                "created_at": q.created_at.isoformat() if q.created_at else None,
            })
        return results

    def update_ticket_status(
        self,
        db: Session,
        ticket_id: int,
        status_value: str,
        assigned_rep: Optional[str] = None
    ) -> dict:
        """
        Updates quote/ticket lifecycle status (e.g. In progress -> completed).
        """
        quote = db.query(Quote).filter(Quote.id == ticket_id).first()
        if not quote:
            raise http_404_not_found(f"Ticket with ID {ticket_id} not found.")

        status_clean = status_value.strip().lower()
        try:
            quote.status = QuoteStatus(status_clean)
        except ValueError:
            raise http_400_bad_request(
                f"Invalid status '{status_value}'. Valid: {[s.value for s in QuoteStatus]}"
            )

        if assigned_rep is not None:
            quote.assigned_rep = assigned_rep.strip()

        db.add(quote)
        db.commit()
        db.refresh(quote)

        return {
            "id": quote.id,
            "status": quote.status.value,
            "assigned_rep": quote.assigned_rep,
            "message": f"Ticket #{quote.id} status successfully updated to {quote.status.value}."
        }

    # ==========================================
    # 3. REFERRALS & COUPON MANAGEMENT
    # ==========================================

    def get_all_referrals(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50
    ) -> List[ReferralBonusItem]:
        """
        Retrieves all referrals with Referrer details, Referral code,
        Qualified signup date, Bonus amount, and Payment Status (Pending / Paid).
        """
        referrals = (
            db.query(Referral)
            .options(joinedload(Referral.referrer), joinedload(Referral.referred_user))
            .order_by(Referral.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        results: List[ReferralBonusItem] = []
        for r in referrals:
            referrer_name = r.referrer.name if r.referrer else "Guardwell Customer"
            referrer_email = r.referrer.email if r.referrer else "unknown@guardwell.com"
            status_label = "Paid" if r.bonus_status == BonusStatus.PAID else "Pending"

            results.append(
                ReferralBonusItem(
                    id=r.id,
                    referrer_name=referrer_name,
                    referrer_email=referrer_email,
                    referral_code=r.referral_code,
                    qualified_date=r.qualified_at,
                    bonus=r.bonus_amount,
                    status=status_label,
                    bonus_status=r.bonus_status.value if hasattr(r.bonus_status, "value") else str(r.bonus_status),
                )
            )
        return results

    def update_referral_bonus_status(
        self,
        db: Session,
        referral_id: int,
        bonus_status_value: str
    ) -> dict:
        """
        Marks referral reward as Paid or Pending.
        """
        referral = db.query(Referral).filter(Referral.id == referral_id).first()
        if not referral:
            raise http_404_not_found(f"Referral with ID {referral_id} not found.")

        status_clean = bonus_status_value.strip().lower()
        try:
            referral.bonus_status = BonusStatus(status_clean)
        except ValueError:
            raise http_400_bad_request("Invalid bonus status. Options: 'pending', 'paid'")

        db.add(referral)
        db.commit()
        db.refresh(referral)

        return {
            "id": referral.id,
            "bonus_status": referral.bonus_status.value,
            "status": "Paid" if referral.bonus_status == BonusStatus.PAID else "Pending",
            "message": f"Referral #{referral.id} bonus status marked as {referral.bonus_status.value}."
        }

    def get_coupon_amount(self, db: Session) -> float:
        """
        Gets current referral coupon reward amount (default $100).
        """
        setting = db.query(SystemSetting).filter(SystemSetting.key == "coupon_amount").first()
        if setting:
            try:
                return float(setting.value)
            except ValueError:
                pass
        return float(settings.DEFAULT_COUPON_AMOUNT)

    def set_coupon_amount(self, db: Session, amount: float) -> dict:
        """
        Sets new coupon reward amount visible across the app for all users.
        """
        setting = db.query(SystemSetting).filter(SystemSetting.key == "coupon_amount").first()
        if not setting:
            setting = SystemSetting(
                key="coupon_amount",
                value=str(amount),
                description="Global referral coupon reward value in USD"
            )
            db.add(setting)
        else:
            setting.value = str(amount)
            db.add(setting)

        db.commit()
        db.refresh(setting)

        return {
            "coupon_amount": float(setting.value),
            "message": f"Global coupon reward amount updated to ${float(setting.value):.2f}."
        }

    # ==========================================
    # 4. USER REPORTS (FEED MODERATION)
    # ==========================================

    def get_all_reports(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 50
    ) -> List[AdminReportListItem]:
        """
        Lists all reported posts for moderation.
        """
        reports = (
            db.query(PostReport)
            .options(
                joinedload(PostReport.post).joinedload(FeedPost.user),
                joinedload(PostReport.reporter),
            )
            .order_by(PostReport.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        results: List[AdminReportListItem] = []
        for r in reports:
            reported_text = r.post.post_description if r.post else "[Deleted post]"
            author_name = r.post.user.name if (r.post and r.post.user) else "Unknown User"
            reporter_name = r.reporter.name if r.reporter else "Anonymous User"

            results.append(
                AdminReportListItem(
                    id=r.id,
                    report_id=r.id,
                    reported_text=reported_text,
                    author_name=author_name,
                    reporter_name=reporter_name,
                    reason=r.reason,
                    created_at=r.created_at,
                    post_id=r.post_id,
                    report_code=f"RPT-{r.id + 105}",
                    status="Open"
                )
            )
        return results

    def handle_report_action(
        self,
        db: Session,
        report_id: int,
        action: str
    ) -> dict:
        """
        Takes admin action on a report:
        - 'delete_post': Permanently deletes the offensive post and related reports/comments.
        - 'dismiss_report': Dismisses the report if post is acceptable.
        """
        report = db.query(PostReport).filter(PostReport.id == report_id).first()
        if not report:
            raise http_404_not_found(f"Report #{report_id} not found.")

        action_clean = action.strip().lower()

        if action_clean == "delete_post":
            post = db.query(FeedPost).filter(FeedPost.id == report.post_id).first()
            if post:
                db.delete(post)
                db.commit()
                return {"message": f"Reported post #{report.post_id} and report #{report_id} deleted permanently."}
            else:
                db.delete(report)
                db.commit()
                return {"message": f"Post was already removed. Report #{report_id} cleared."}

        elif action_clean == "dismiss_report":
            db.delete(report)
            db.commit()
            return {"message": f"Report #{report_id} dismissed successfully."}

        else:
            raise http_400_bad_request("Invalid action. Must be 'delete_post' or 'dismiss_report'.")

    # ==========================================
    # 5. DASHBOARD OVERVIEW
    # ==========================================

    def get_dashboard_overview(self, db: Session) -> DashboardOverviewResponse:
        """
        Computes real-time overview stats for Admin Dashboard:
        - Total Customers
        - Open Tickets (submitted + in_progress)
        - Urgent Tickets count
        - Referral Rewards total & pending count
        - Last 7 days service requests graph
        - Latest service tickets
        - Recent activity timeline
        """
        total_customers = db.query(func.count(User.id)).filter(User.role == UserRole.CUSTOMER).scalar() or 0
        open_tickets = db.query(func.count(Quote.id)).filter(Quote.status.in_([QuoteStatus.SUBMITTED, QuoteStatus.IN_PROGRESS])).scalar() or 0

        # Urgent tickets approximation (submitted tickets in last 72 hours)
        urgent_tickets = db.query(func.count(Quote.id)).filter(
            Quote.status == QuoteStatus.SUBMITTED,
            Quote.created_at >= datetime.utcnow() - timedelta(days=3)
        ).scalar() or 0

        # Referral Rewards
        referral_sum = db.query(func.sum(Referral.bonus_amount)).scalar() or 0.0
        pending_rewards = db.query(func.count(Referral.id)).filter(Referral.bonus_status == BonusStatus.PENDING).scalar() or 0

        # Last 7 days service overview graph data
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        service_overview_days = []
        today = datetime.utcnow()
        for i in range(6, -1, -1):
            day_date = today - timedelta(days=i)
            day_name = days[day_date.weekday()]
            count = (
                db.query(func.count(Quote.id))
                .filter(func.date(Quote.created_at) == day_date.strftime("%Y-%m-%d"))
                .scalar()
                or 0
            )
            service_overview_days.append({
                "day": day_name,
                "date": day_date.strftime("%Y-%m-%d"),
                "requests": count
            })

        # Latest service tickets
        latest_quotes = db.query(Quote).order_by(Quote.created_at.desc()).limit(5).all()
        latest_service_tickets = [
            {
                "id": q.id,
                "title": (q.description[:40] + "...") if len(q.description) > 40 else q.description,
                "customer_name": q.name,
                "status": "New" if q.status == QuoteStatus.SUBMITTED else ("In progress" if q.status == QuoteStatus.IN_PROGRESS else "Completed"),
                "raw_status": q.status.value,
                "time": q.created_at.strftime("%I:%M %p") if q.created_at else None,
            }
            for q in latest_quotes
        ]

        # Recent activities dynamically assembled
        recent_activity = [
            {
                "type": "customer_verified",
                "title": "Customer verified",
                "description": f"Verified profile checks active",
                "time": "Recent",
            },
            {
                "type": "ticket_status",
                "title": f"Tickets active: {open_tickets}",
                "description": f"{urgent_tickets} waiting initial triage",
                "time": "Today",
            },
            {
                "type": "bonus_pending",
                "title": f"Referral rewards: ${referral_sum:.0f}",
                "description": f"{pending_rewards} bonuses pending review",
                "time": "Today",
            }
        ]

        return DashboardOverviewResponse(
            total_customers=total_customers,
            open_tickets=open_tickets,
            urgent_tickets=urgent_tickets,
            referral_rewards=float(referral_sum),
            pending_rewards_count=pending_rewards,
            service_overview_days=service_overview_days,
            latest_service_tickets=latest_service_tickets,
            recent_activity=recent_activity,
        )


admin_service = AdminService()

