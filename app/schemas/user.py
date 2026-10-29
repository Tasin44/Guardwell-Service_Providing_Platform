"""
================================================================================
FASTAPI SCHEMAS VS DRF SERIALIZERS (USER PROFILE):
1. DRF-এর UserSerializer-এর মতোই UserProfileResponse আউটপুট ডেটা ফরম্যাট করে।
2. Sensitive Data Exclusion:
   - hashed_password ফিল্ডটি রেসপন্স স্কিমাতে রাখা হয়নি, যাতে ক্লায়েন্টে পাসওয়ার্ড লিক না হয়।
3. from_attributes = True:
   - SQLAlchemy User অবজেক্ট থেকে সরাসরি Pydantic মডেলে কনভার্ট করে।
================================================================================
"""



