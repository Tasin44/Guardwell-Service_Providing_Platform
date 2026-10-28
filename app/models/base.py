"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. DRY (Don't Repeat Yourself):
   - সমস্ত মডেলের কমন অ্যাট্রিবিউটগুলো (id, created_at, updated_at) একটি Base Model-এ রাখা হয়েছে।
2. Inheritance & Auditing:
   - Declarative base mixin এর মাধ্যমে স্বয়ংক্রিয়ভাবে রেকর্ড তৈরির ও আপডেটের সময় ট্র্যাক হয়।
3. Database Indexing Optimization:
   - created_at ফিল্ডে ইনডেক্সিং দেওয়া হয়েছে যেন টাইমলাইন এবং প্যাজিনেশন দ্রুত কুয়েরি হয়।
================================================================================
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime
from app.core.database import Base


class TimeStampedModel(Base):
    """
    Abstract declarative base class for models that require automatic timestamps.
    """
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

















