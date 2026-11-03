

"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Instant Publishing:
   - পোস্ট তৈরি হওয়ামাত্রই সরাসরি লাইভ হবে।
2. Community Reporting Service:
   - যে কেউ অন্য ইউজারের পোস্টে রিপোর্ট করতে পারবে।
   - পূর্বে রিপোর্ট করা থাকলে Fail-Fast নীতি অনুযায়ী কনফ্লিক্ট এরর দেবে।
3. Admin Decision Moderation:
   - অ্যাডমিন রিপোর্টকৃত পোস্ট দেখে তা রিমুভ (Delete) করতে পারবে অথবা রিপোর্ট ডিসমিস করতে পারবে।
================================================================================
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.user import User
from app.models.feed import FeedPost, PostReport, Comment, CommentReaction
from app.repositories.feed_repository import (
    feed_post_repository,
    post_report_repository,
    comment_repository,
    reaction_repository,
)
from app.services.file_service import file_service
from app.schemas.feed import (
    PostResponse,
    CommentResponse,
    ReactionToggleResponse,
    ReactionUserDetail,
    ReportPostResponse,
    ReportedPostDetail,
)
from app.core.exceptions import (
    http_400_bad_request,
    http_403_forbidden,
    http_404_not_found,
    http_409_conflict,
)


class FeedService:
    @staticmethod
    def _assert_user_not_banned(user: User) -> None:
        """Fail fast if the user is banned by admin from feed interactions."""
        if user.is_feed_banned:
            raise http_403_forbidden("Your account is restricted from posting or interacting on the community feed.")

    async def create_post(
        self,
        db: Session,
        *,
        user: User,
        post_description: str,
        image_file: Optional[UploadFile] = None,
        video_file: Optional[UploadFile] = None
    ) -> PostResponse:
        """
        Creates a new community post. Directly published and visible on the feed.
        """
        self._assert_user_not_banned(user)

        image_url = None
        video_url = None
        if image_file:
            image_url = await file_service.save_upload_file(image_file, subfolder="posts")
        if video_file:
            video_url = await file_service.save_upload_file(video_file, subfolder="posts")

        post = FeedPost(
            user_id=user.id,
            post_description=post_description.strip(),
            image_url=image_url,
            video_url=video_url
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        return PostResponse(
            id=post.id,
            user_id=user.id,
            user_name=user.name,
            user_image=user.image_url,
            post_description=post.post_description,
            image_url=post.image_url,
            video_url=post.video_url,
            comment_count=0,
            created_at=post.created_at
        )

    def get_public_feed(self, db: Session, *, skip: int = 0, limit: int = 20) -> List[PostResponse]:
        """
        Fetches all public feed posts with author metadata and comment counts.
        """
        posts = feed_post_repository.get_all_posts(db, skip=skip, limit=limit)
        results: List[PostResponse] = []

        for p in posts:
            comment_count = feed_post_repository.count_comments(db, p.id)
            results.append(
                PostResponse(
                    id=p.id,
                    user_id=p.user_id,
                    user_name=p.user.name if p.user else "Guardwell Customer",
                    user_image=p.user.image_url if p.user else None,
                    post_description=p.post_description,
                    image_url=p.image_url,
                    video_url=p.video_url,
                    comment_count=comment_count,
                    created_at=p.created_at
                )
            )
        return results

    def report_post(self, db: Session, *, post_id: int, user: User, reason: str) -> ReportPostResponse:
        """
        Allows any user to report an inappropriate post to the admin.
        """
        self._assert_user_not_banned(user)

        post = feed_post_repository.get(db, post_id)
        if not post:
            raise http_404_not_found(f"Post with ID {post_id} not found.")

        if post.user_id == user.id:
            raise http_400_bad_request("You cannot report your own post.")

        existing = post_report_repository.get_by_user_and_post(db, post_id=post_id, user_id=user.id)
        if existing:
            raise http_409_conflict("You have already reported this post.")

        report = PostReport(
            post_id=post_id,
            reporter_id=user.id,
            reason=reason.strip()
        )
        db.add(report)
        db.commit()
        db.refresh(report)

        return ReportPostResponse(
            report_id=report.id,
            post_id=post.id,
            message="Post reported successfully. Admin will review and take action."
        )

    def add_comment(self, db: Session, *, post_id: int, user: User, comment_text: str) -> CommentResponse:
        """
        Adds a comment to a feed post.
        """
        self._assert_user_not_banned(user)

        post = feed_post_repository.get(db, post_id)
        if not post:
            raise http_404_not_found("Post not found.")

        comment = Comment(
            post_id=post.id,
            user_id=user.id,
            comment_text=comment_text.strip()
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)

        return CommentResponse(
            id=comment.id,
            post_id=comment.post_id,
            user_id=user.id,
            name=user.name,
            image=user.image_url,
            comment_time=comment.created_at,
            comment_text=comment.comment_text,
            reaction_count=0,
            user_has_reacted=False
        )

    def get_comments_for_post(self, db: Session, *, post_id: int, current_user_id: Optional[int] = None) -> List[CommentResponse]:
        """
        Returns all comments for a post formatted with:
        Name, Image, comment_time, comment_text, reaction_count, user_has_reacted.
        """
        post = feed_post_repository.get(db, post_id)
        if not post:
            raise http_404_not_found(f"Post with ID {post_id} not found.")

        comments = comment_repository.get_comments_for_post(db, post_id)
        results: List[CommentResponse] = []

        for c in comments:
            reaction_count = len(c.reactions)
            user_has_reacted = False
            if current_user_id:
                user_has_reacted = any(r.user_id == current_user_id for r in c.reactions)

            results.append(
                CommentResponse(
                    id=c.id,
                    post_id=c.post_id,
                    user_id=c.user_id,
                    name=c.user.name if c.user else "Anonymous",
                    image=c.user.image_url if c.user else None,
                    comment_time=c.created_at,
                    comment_text=c.comment_text,
                    reaction_count=reaction_count,
                    user_has_reacted=user_has_reacted
                )
            )
        return results

    def toggle_comment_reaction(self, db: Session, *, post_id: int, comment_id: int, user: User) -> ReactionToggleResponse:
        """
        Love React or Un-react to a specific comment.
        """
        self._assert_user_not_banned(user)

        comment = comment_repository.get(db, comment_id)
        if not comment or comment.post_id != post_id:
            raise http_404_not_found("Comment not found on this post.")

        reacted, total_reactions = reaction_repository.toggle_reaction(db, comment_id=comment_id, user_id=user.id)
        message = "Reaction added." if reacted else "Reaction removed."

        return ReactionToggleResponse(
            comment_id=comment_id,
            has_reacted=reacted,
            total_reactions=total_reactions,
            message=message
        )

    def get_comment_reactions(self, db: Session, *, post_id: int, comment_id: int) -> List[ReactionUserDetail]:
        """
        Returns all users who reacted to a specific comment.
        """
        comment = comment_repository.get(db, comment_id)
        if not comment or comment.post_id != post_id:
            raise http_404_not_found("Comment not found.")

        reactions = reaction_repository.get_reactions_by_comment(db, comment_id)
        return [
            ReactionUserDetail(
                user_id=r.user_id,
                name=r.user.name if r.user else "Customer",
                image=r.user.image_url if r.user else None,
                reacted_at=r.created_at
            )
            for r in reactions
        ]

    # ==========================================
    # ADMIN MODERATION METHODS
    # ==========================================

    def admin_get_reports(self, db: Session, *, skip: int = 0, limit: int = 50) -> List[ReportedPostDetail]:
        """Admin fetches all reported posts for review."""
        reports = post_report_repository.get_all_reports(db, skip=skip, limit=limit)
        return [
            ReportedPostDetail(
                report_id=r.id,
                post_id=r.post_id,
                post_description=r.post.post_description if r.post else "[Deleted Post]",
                post_author_name=r.post.user.name if (r.post and r.post.user) else "Unknown",
                reporter_id=r.reporter_id,
                reporter_name=r.reporter.name if r.reporter else "Unknown",
                reason=r.reason,
                reported_at=r.created_at
            )
            for r in reports
        ]

    def admin_delete_post(self, db: Session, post_id: int) -> dict:
        """Admin decision: Remove the reported post permanently."""
        post = feed_post_repository.get(db, post_id)
        if not post:
            raise http_404_not_found("Post not found.")

        db.delete(post)
        db.commit()
        return {"message": f"Post #{post_id} and all related comments/reports have been permanently removed."}

    def admin_dismiss_report(self, db: Session, report_id: int) -> dict:
        """Admin decision: Dismiss a report if the post is harmless."""
        report = post_report_repository.get(db, report_id)
        if not report:
            raise http_404_not_found("Report not found.")

        db.delete(report)
        db.commit()
        return {"message": f"Report #{report_id} has been dismissed."}

    def admin_delete_comment(self, db: Session, comment_id: int) -> dict:
        """Admin removes inappropriate comments."""
        comment = comment_repository.get(db, comment_id)
        if not comment:
            raise http_404_not_found("Comment not found.")

        db.delete(comment)
        db.commit()
        return {"message": "Comment removed successfully by admin."}


feed_service = FeedService()

