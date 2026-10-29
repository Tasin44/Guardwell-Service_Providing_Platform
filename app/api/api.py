"""
================================================================================
FASTAPI ROUTER AGGREGATION:
1. Analogous to Django's urls.py:
   - এখানে সমস্ত অ্যাপ্লিকেশনের মডিউলার এন্ডপয়েন্টগুলো কেন্দ্রীভূত করা হয়েছে।
2. Dual URL Routing Support:
   - ফ্রন্টএন্ড যেভাবে রিকোয়েস্ট পাঠাবে (যেমন /create_post/, /create_quote, /profile/)
     এবং স্ট্যান্ডার্ড RESTful প্রিফিক্স (/auth, /feed, /quotes) উভয় ফরম্যাটই এখানে সাপোর্ট করে।
================================================================================
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    profile,
    feed,
    quotes,
    referrals,
    coupons,
    admin,
    ai_faq,
)

api_router = APIRouter()

# Modular routes
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(profile.router, prefix="/profile", tags=["User Profile"])
api_router.include_router(feed.router, prefix="/feed", tags=["Social Feed"])
api_router.include_router(quotes.router, prefix="/quotes", tags=["Quotes & Service Tickets"])
api_router.include_router(referrals.router, prefix="/referrals", tags=["Referral System"])
api_router.include_router(coupons.router, prefix="/coupons", tags=["Coupons & Discounts"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Dashboard"])
api_router.include_router(ai_faq.router, prefix="/ai", tags=["AI Home FAQ"])

# Root-level route mounts matching user's exact specification
api_router.include_router(profile.router, tags=["Profile (Direct Routes)"])
api_router.include_router(feed.router, tags=["Feed (Direct Routes)"])
api_router.include_router(quotes.router, tags=["Quotes (Direct Routes)"])
