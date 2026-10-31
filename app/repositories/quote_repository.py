"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. High Cohesion:
   - কোট ও ইন্সপেকশন টিকিট সংক্রান্ত ডাটাবেজ অপারেশন সেন্ট্রালাইজ করা হয়েছে।
2. Notification Recipients:
   - টিম মেম্বারদের ইমেইল লিস্ট ডাইনামিকভাবে ফেচ করার কুয়েরি।
================================================================================
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.quote import Quote, QuoteStatus, QuoteType, NotificationRecipient


class QuoteRepository(BaseRepository[Quote]):
    def __init__(self):
        super().__init__(Quote)

    def get_by_user(self, db: Session, user_id: int) -> List[Quote]:
        """Fetch all tickets/quotes submitted by a specific user."""
        return (
            db.query(Quote)
            .filter(Quote.user_id == user_id)
            .order_by(Quote.created_at.desc())
            .all()
        )

    def get_all_with_filters(
        self,
        db: Session,
        *,
        status: Optional[QuoteStatus] = None,
        type: Optional[QuoteType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Quote]:
        """Admin query for all submitted quotes with pagination and status filter."""
        query = db.query(Quote)
        if status:
            query = query.filter(Quote.status == status)
        if type:
            query = query.filter(Quote.type == type)
        return query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()


class NotificationRecipientRepository(BaseRepository[NotificationRecipient]):
    def __init__(self):
        super().__init__(NotificationRecipient)

    def get_active_recipients(self, db: Session) -> List[NotificationRecipient]:
        """Fetch all active email notification recipients."""
        return db.query(NotificationRecipient).filter(NotificationRecipient.is_active == True).all()

    def get_by_email(self, db: Session, email: str) -> Optional[NotificationRecipient]:
        return db.query(NotificationRecipient).filter(NotificationRecipient.email == email.strip().lower()).first()


# Singleton Repository Instances
quote_repository = QuoteRepository()
notification_recipient_repository = NotificationRecipientRepository()
