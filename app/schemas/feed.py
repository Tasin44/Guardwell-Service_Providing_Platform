"""
================================================================================
FASTAPI SCHEMAS VS DRF SERIALIZERS (COMMUNITY FEED & REPORT SYSTEM):
1. PostResponse:
   - স্ট্যাটাস ফিল্ডের ঝামেলা ছাড়া সরাসরি পোস্টের ডাটা সিরিয়ালাইজ করে।
2. Report Post Schemas:
   - রিপোর্ট করার কারণ (reason) এবং সফল রিপোর্টের রেসপন্স ডিটিও।
3. Comment & Reaction Schemas:
   - Name, Image, comment_time, comment_text, reaction_count এবং user_has_reacted।
================================================================================
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class PostResponse(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_image: Optional[str] = None
    post_description: str
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    comment_count: int = 0
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentCreateRequest(BaseModel):
    comment_text: str = Field(..., min_length=1, description="Text content of the comment")


class CommentResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    name: str
    image: Optional[str] = None
    comment_time: datetime
    comment_text: str
    reaction_count: int = 0
    user_has_reacted: bool = False

    model_config = ConfigDict(from_attributes=True)


class ReactionToggleResponse(BaseModel):
    comment_id: int
    has_reacted: bool
    total_reactions: int
    message: str


class ReactionUserDetail(BaseModel):
    user_id: int
    name: str
    image: Optional[str] = None
    reacted_at: datetime


class ReportPostRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500, description="Reason for reporting this post")


class ReportPostResponse(BaseModel):
    report_id: int
    post_id: int
    message: str = "Post has been reported to admin for review."


class ReportedPostDetail(BaseModel):
    report_id: int
    post_id: int
    post_description: str
    post_author_name: str
    reporter_id: int
    reporter_name: str
    reason: str
    reported_at: datetime
