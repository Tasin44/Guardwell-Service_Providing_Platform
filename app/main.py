"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Application Factory & Lifecycle Management (Lifespan Context):
   - lifespan context manager ব্যবহার করে অ্যাপ স্টার্টআপে স্বয়ংক্রিয়ভাবে
     ডেটাবেজ টেবিল তৈরি ও ইনিশিয়াল সুপারইউজার/এডমিন সিড করা হয়।
2. CORS & Security Middleware:
   - মোবাইল অ্যাপ (Flutter/React Native) এবং ওয়েব ক্লায়েন্ট উভয়ের জন্য
     নিরাপদ Cross-Origin Resource Sharing (CORS) কনফিগারেশন।
3. Static File Serving:
   - uploads ডিরেক্টরি মাউন্ট করা হয়েছে যাতে আপলোডকৃত ফটো ও ভিডিও সরাসরি
     URL-এর মাধ্যমে ব্রাউজার ও অ্যাপে লোড হতে পারে।
4. Global Exception Handlers:
   - অপ্রত্যাশিত কোনো এরর ঘটলেও সার্ভার ক্র্যাশ না করে ক্লিনার JSON এরর রেসপন্স প্রদান করে।
================================================================================
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.quote import NotificationRecipient
# from app.api.v1.api import api_router


def seed_initial_data():
    """
    Seeds initial default admin and email alert recipients on first startup.
    """
    db = SessionLocal()
    try:
        # 1. Seed Superuser Admin
        admin_user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER_EMAIL.lower()).first()
        if not admin_user:
            admin_user = User(
                name="Guardwell Admin",
                email=settings.FIRST_SUPERUSER_EMAIL.lower(),
                phone_number="+1-800-555-0199",
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
                role=UserRole.ADMIN,
                referral_code="GWADMIN1",
                is_active=True,
                is_verified_otp=True,
                is_verified_customer=True,
                is_feed_banned=False,
            )
            db.add(admin_user)
            db.commit()
            print(f"\n[INIT SEED] Created Initial Admin: {settings.FIRST_SUPERUSER_EMAIL}")
            print(f"[INIT SEED] Password: {settings.FIRST_SUPERUSER_PASSWORD}\n")

        # 2. Seed Default Notification Recipient for Service Tickets
        existing_recipient = db.query(NotificationRecipient).first()
        if not existing_recipient:
            recipient = NotificationRecipient(
                name="Guardwell Dispatch Team",
                email="dispatch@guardwell.com",
                is_active=True
            )
            db.add(recipient)
            db.commit()
            print(f"[INIT SEED] Configured Default Dispatch Alert Recipient: dispatch@guardwell.com")

    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events: Startup and Shutdown."""
    # Create DB tables
    Base.metadata.create_all(bind=engine)
    # Seed initial data
    seed_initial_data()
    yield
    # Cleanup operations on shutdown if any


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for Guardwell Home Protection, Gutter Services, Viral Referral System, and Community Social Feed.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Uploads Directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include master API router
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router)  # Also mount directly for root compatibility


@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "version": "1.0.0"
    }


@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok"}
