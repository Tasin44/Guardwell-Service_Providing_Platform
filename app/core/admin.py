"""
================================================================================
SQLADMIN DASHBOARD CONFIGURATION (ANALOGOUS TO DJANGO ADMIN):
1. AuthenticationBackend:
   - Django Admin-এর মতো ইমেইল ও পাসওয়ার্ড দিয়ে সুপারইউজার লগইন ভেরিফাই করে।
2. ModelView:
   - ডেটাবেজ টেবিলগুলোর কলাম প্রদর্শন, ফিল্টারিং, সার্চ এবং CRUD অপারেশন নিশ্চিত করে।
================================================================================
"""

from sqladmin import ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request

from app.core.config import settings
from app.core.security import verify_password
from app.core.database import SessionLocal
from app.models.user import User, OTPVerification
from app.models.quote import Quote, NotificationRecipient


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.email == str(username).strip().lower()).first()
            if user and user.role.value == "admin" and verify_password(str(password), user.hashed_password):
                request.session.update({"admin_user": user.email})
                return True
            return False
        finally:
            db.close()

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        admin_user = request.session.get("admin_user")
        return bool(admin_user)


class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    column_list = [
        User.id,
        User.name,
        User.email,
        User.phone_number,
        User.role,
        User.referral_code,
        User.is_active,
        User.is_verified_otp,
        User.created_at,
    ]
    column_searchable_list = [User.name, User.email, User.phone_number, User.referral_code]
    column_sortable_list = [User.id, User.created_at]


class OTPVerificationAdmin(ModelView, model=OTPVerification):
    name = "OTP Verification"
    name_plural = "OTP Verifications"
    icon = "fa-solid fa-key"
    column_list = [
        OTPVerification.id,
        OTPVerification.email,
        OTPVerification.otp_code,
        OTPVerification.purpose,
        OTPVerification.is_used,
        OTPVerification.expires_at,
        OTPVerification.created_at,
    ]
    column_searchable_list = [OTPVerification.email, OTPVerification.otp_code]
    column_sortable_list = [OTPVerification.id, OTPVerification.created_at]


class QuoteAdmin(ModelView, model=Quote):
    name = "Quote / Service"
    name_plural = "Quotes & Service Tickets"
    icon = "fa-solid fa-file-invoice"
    column_list = [
        Quote.id,
        Quote.name,
        Quote.email,
        Quote.phone_number,
        Quote.type,
        Quote.service_category,
        Quote.status,
        Quote.created_at,
    ]
    column_searchable_list = [Quote.name, Quote.email, Quote.phone_number, Quote.postcode]
    column_sortable_list = [Quote.id, Quote.created_at]


class NotificationRecipientAdmin(ModelView, model=NotificationRecipient):
    name = "Notification Recipient"
    name_plural = "Notification Recipients"
    icon = "fa-solid fa-bell"
    column_list = [
        NotificationRecipient.id,
        NotificationRecipient.name,
        NotificationRecipient.email,
        NotificationRecipient.is_active,
        NotificationRecipient.created_at,
    ]
    column_searchable_list = [NotificationRecipient.name, NotificationRecipient.email]


authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
