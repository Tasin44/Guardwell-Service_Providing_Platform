"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Open Social Feed Pattern:
   - পোস্ট তৈরি হওয়ামাত্রই সরাসরি লাইভ হবে (Instant Publishing)।
2. Community Reporting Pattern:
   - কোনো ব্যবহারকারী অনুপযুক্ত পোস্ট দেখলে রিপোর্ট করতে পারবে।
   - UniqueConstraint("post_id", "user_id") নিশ্চিত করে একজন ইউজার একটি পোস্টে
     একবারের বেশি ডুপ্লিকেট রিপোর্ট করতে পারবে না (Spam Protection & Idempotency)।
================================================================================
"""

from sqlalchemy import Column, String, Text, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import TimeStampedModel


class FeedPost(TimeStampedModel):
    __tablename__ = "feed_posts"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    post_description = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    video_url = Column(String(500), nullable=True)

    # Relationships
    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    reports = relationship("PostReport", back_populates="post", cascade="all, delete-orphan")


class PostReport(TimeStampedModel):
    """
    Tracks community reports against feed posts for admin moderation.
    """
    __tablename__ = "post_reports"

    post_id = Column(Integer, ForeignKey("feed_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Text, nullable=False)

    # Relationships
    post = relationship("FeedPost", back_populates="reports")
    reporter = relationship("User")

    # Enforce one report per user per post
    __table_args__ = (
        UniqueConstraint("post_id", "reporter_id", name="uq_user_post_report"),
    )


class Comment(TimeStampedModel):
    __tablename__ = "comments"

    post_id = Column(Integer, ForeignKey("feed_posts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    comment_text = Column(Text, nullable=False)

    # Relationships
    post = relationship("FeedPost", back_populates="comments")
    user = relationship("User", back_populates="comments")
    reactions = relationship("CommentReaction", back_populates="comment", cascade="all, delete-orphan")


class CommentReaction(TimeStampedModel):
    __tablename__ = "comment_reactions"

    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationships
    comment = relationship("Comment", back_populates="reactions")
    user = relationship("User", back_populates="reactions")

    # Enforce one reaction per user per comment
    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="uq_user_comment_reaction"),
    )
