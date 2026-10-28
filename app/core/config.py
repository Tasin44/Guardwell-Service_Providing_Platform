"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Singleton Pattern:
   - Settings অবজেক্টটি পুরো অ্যাপ্লিকেশনে একবারই ইনিশিয়ালাইজ হয় (Single Source of Truth)।
2. 12-Factor App Configuration:
   - হার্ডকোড না করে সব কনফিগারেশন .env ফাইল বা Environment Variables থেকে লোড করা হয়।
3. Fail-Fast Principle:
   - কোনো আবশ্যক কনফিগারেশন টাইপ ভুল হলে অ্যাপ স্টার্টাপেই তৎক্ষণাৎ Validation Error দিয়ে বন্ধ হবে।
================================================================================
"""
import os 
from typing import List,Union
from pydantic import AnyHttpUrl,field_validator #❓explain all the imports
from pydantic_settings import BaseSettings,SettingsConfigDict


'''
import os: অপারেটিং সিস্টেম রিলেটেড কাজ করার জন্য (যেমন: ফোল্ডার আছে কিনা চেক করা, নতুন ডিরেক্টরি বানানো os.makedirs())।
from typing import List, Union: পাইথনের টাইপ হিন্টিং। যেমন CORS_ORIGINS: List[str] মানে এটি স্ট্রিং-এর একটি লিস্ট হবে।
from pydantic import AnyHttpUrl, field_validator:
AnyHttpUrl: কোনো ভেরিয়েবল ভ্যালিড URL কিনা (যেমন http:// বা https://) তা চেক করার জন্য।
field_validator: কোনো ফিল্ডে কাস্টম ভ্যালিডেশন লজিক লেখার জন্য।
from pydantic_settings import BaseSettings, SettingsConfigDict:
BaseSettings: এর মাধ্যমে ক্লাস বানালে এটি স্বয়ংক্রিয়ভাবে পরিবেশ ভেরিয়েবল বা .env ফাইল থেকে মানগুলো রিড করতে পারে।
SettingsConfigDict: .env ফাইলের নাম, এনকোডিং (utf-8) ইত্যাদি কনফিগারেশন সেট করার ডিকশনারি।
'''



class Settings(BaseSettings):
    # Base Configuration
    PROJECT_NAME: str = "Guardwell API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database: SQLite for zero-config local run, easily swappable for Postgres
    DATABASE_URL: str = "sqlite:///./guardwell.db"

    # Security & JWT Tokens
    SECRET_KEY: str = "guardwell-super-secure-production-ready-jwt-secret-key-change-me"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Business Logic Defaults
    DEFAULT_COUPON_AMOUNT: float = 100.00
    OTP_EXPIRE_MINUTES: int = 10

    # Media Uploads (Photos & Videos)
    UPLOAD_DIR: str = "./uploads"

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]

    # Initial Admin Credentials (for seed script)
    FIRST_SUPERUSER_EMAIL: str = "admin@guardwell.com"
    FIRST_SUPERUSER_PASSWORD: str = "AdminSecretPassword123!"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


# Singleton Instance
settings = Settings()

# Ensure uploads directory exists at startup
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)










