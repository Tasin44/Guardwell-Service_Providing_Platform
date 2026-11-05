"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Direct Public Feed:
   - স্ট্যাটাস ফিল্টারিং ছাড়া সব পোস্ট সরাসরি ক্রিয়েট টাইম অনুযায়ী প্রদর্শিত হয়।
2. Report Repository:
   - পোস্ট রিপোর্ট হ্যান্ডলিং ও অ্যাডমিনের রিভিউ কুয়েরি।
3. Optimization & N+1 Prevention:
   - joinedload(Comment.user), joinedload(FeedPost.user) ব্যবহার।
================================================================================
"""

from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.repositories.base import BaseRepository
from app.models.feed import FeedPost, PostReport, Comment, CommentReaction


class FeedPostRepository(BaseRepository[FeedPost]):
    def __init__(self):
        super().__init__(FeedPost)

    def get_all_posts(self, db: Session, *, skip: int = 0, limit: int = 20) -> List[FeedPost]:
        """Fetch all public feed posts with user relationships."""
        return (
            db.query(FeedPost)
            .options(joinedload(FeedPost.user))
            .order_by(FeedPost.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_comments(self, db: Session, post_id: int) -> int:
        """Returns total comments count for a post."""
        return db.query(func.count(Comment.id)).filter(Comment.post_id == post_id).scalar() or 0

    def count_likes(self, db: Session, post_id: int) -> int:
        """Returns total likes/reactions count for a post."""
        return (
            db.query(func.count(CommentReaction.id))
            .join(Comment, CommentReaction.comment_id == Comment.id)
            .filter(Comment.post_id == post_id)
            .scalar()
            or 0
        )


class PostReportRepository(BaseRepository[PostReport]):
    def __init__(self):
        super().__init__(PostReport)

    def get_by_user_and_post(self, db: Session, *, post_id: int, user_id: int) -> Optional[PostReport]:
        """Check if user has already reported this post."""
        return (
            db.query(PostReport)
            .filter(PostReport.post_id == post_id, PostReport.reporter_id == user_id)
            .first()
        )

    def get_all_reports(self, db: Session, *, skip: int = 0, limit: int = 50) -> List[PostReport]:
        """Fetch reported posts for admin review with post and reporter info."""
        return (
            db.query(PostReport)
            .options(
                joinedload(PostReport.post).joinedload(FeedPost.user),
                joinedload(PostReport.reporter)
            )
            .order_by(PostReport.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


class CommentRepository(BaseRepository[Comment]):
    def __init__(self):
        super().__init__(Comment)

    def get_comments_for_post(self, db: Session, post_id: int) -> List[Comment]:
        """Fetch all comments for a post, eagerly loading user details."""
        return (
            db.query(Comment)
            .options(joinedload(Comment.user), joinedload(Comment.reactions))
            .filter(Comment.post_id == post_id)
            .order_by(Comment.created_at.asc())
            .all()
        )


class ReactionRepository(BaseRepository[CommentReaction]):
    def __init__(self):
        super().__init__(CommentReaction)

    def get_reaction(self, db: Session, *, comment_id: int, user_id: int) -> Optional[CommentReaction]:
        """Check if user has already reacted to this comment."""
        return (
            db.query(CommentReaction)
            .filter(CommentReaction.comment_id == comment_id, CommentReaction.user_id == user_id)
            .first()
        )

    def get_reactions_by_comment(self, db: Session, comment_id: int) -> List[CommentReaction]:
        """Fetch all user reactions on a comment."""
        return (
            db.query(CommentReaction)
            .options(joinedload(CommentReaction.user))
            .filter(CommentReaction.comment_id == comment_id)
            .order_by(CommentReaction.created_at.desc())
            .all()
        )

    def count_by_comment(self, db: Session, comment_id: int) -> int:
        """Count total reactions on a comment."""
        return db.query(func.count(CommentReaction.id)).filter(CommentReaction.comment_id == comment_id).scalar() or 0

    def toggle_reaction(self, db: Session, *, comment_id: int, user_id: int) -> Tuple[bool, int]:
        """
        Toggles Love Reaction:
        - If reaction exists -> Deletes it (Un-react) -> Returns (False, new_count)
        - If reaction doesn't exist -> Creates it (Love react) -> Returns (True, new_count)
        """
        existing = self.get_reaction(db, comment_id=comment_id, user_id=user_id)
        if existing:
            db.delete(existing)
            db.commit()
            reacted = False
        else:
            new_reaction = CommentReaction(comment_id=comment_id, user_id=user_id)
            db.add(new_reaction)
            db.commit()
            reacted = True

        total_reactions = self.count_by_comment(db, comment_id=comment_id)
        return reacted, total_reactions


# Singleton Repository Instances
feed_post_repository = FeedPostRepository()
post_report_repository = PostReportRepository()
comment_repository = CommentRepository()
reaction_repository = ReactionRepository()
