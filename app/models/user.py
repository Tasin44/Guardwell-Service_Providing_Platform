
"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. High Cohesion & Single Responsibility:
   - User মডেল ব্যবহারকারীর আইডেন্টিটি, রোল ও প্রোফাইল ধারণ করে।
   - OTPVerification মডেল আলাদা রাখা হয়েছে SoC মেনে ওটিপি হ্যান্ডলিংয়ের জন্য।
2. Database Indexing & Query Optimization:
   - email, phone_number এবং referral_code ইউনিক এবং ইনডেক্সড, যা দ্রুত লুকআপ নিশ্চিত করে।
3. Role-Based Access Control (RBAC):
   - Enum-ভিত্তিক রোল (admin, customer) নিশ্চিত করে প্রেজেন্টেশন ও সিকিউরিটি লেয়ারে পরিষ্কার অথরাইজেশন।
================================================================================
"""

import enum
from datetime import datetime,timezone
from sqlalchemy import Column,String,Boolean,Enum,ForeignKey,Integer,DateTime
from sqlalchemy.orm import TimeStampedModel




















