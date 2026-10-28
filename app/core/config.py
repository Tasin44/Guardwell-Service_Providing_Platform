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