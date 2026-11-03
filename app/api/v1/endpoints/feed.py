"""
================================================================================
FASTAPI ROUTER VS DRF APIVIEWS (SOCIAL COMMUNITY FEED & POST REPORTING):
1. Instant Publishing:
   - POST /create_post/ & GET /create_post/
2. Community Report a Post:
   - POST /report_post/{post_id} & PATCH /report_post/{post_id}
   - Any user can report another user's post with a reason.
3. Comments & Reactions:
   - POST /create_comment/{post_id} & GET /create_comment/{post_id}
   - PATCH /reaction/{post_id}/{comment_id} & GET /reaction/{post_id}/{comment_id}
================================================================================
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, get_optional_current_user
from app.models.user import User
from app.services.feed_service import feed_service
from app.schemas.feed import (
    PostResponse,
    CommentCreateRequest,
    CommentResponse,
    ReactionToggleResponse,
    ReactionUserDetail,
    ReportPostRequest,
    ReportPostResponse,
)

router = APIRouter()


# ==========================================
# 1. CREATE & GET POSTS
# ==========================================

@router.post(
    "/create_post/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Feed Post (Instant Publishing)"
)
async def create_post(
    post_description: str = Form(..., description="Text content of the post"),
    image: Optional[UploadFile] = File(None, description="Optional photo attachment"),
    video: Optional[UploadFile] = File(None, description="Optional video attachment"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a new post to the community feed. Directly published.
    """
    return await feed_service.create_post(
        db,
        user=current_user,
        post_description=post_description,
        image_file=image,
        video_file=video
    )


@router.get(
    "/create_post/",
    response_model=List[PostResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Public Feed Posts"
)
def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Returns public feed posts with author metadata, photo/video URLs, and comment counts.
    """
    return feed_service.get_public_feed(db, skip=skip, limit=limit)


# ==========================================
# 2. REPORT A POST (POST or PATCH /report_post/{post_id})
# ==========================================

@router.post(
    "/report_post/{post_id}",
    response_model=ReportPostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report an Inappropriate Post (POST)"
)
def report_post_post(
    post_id: int,
    payload: ReportPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows any user to report another user's post to admin with a reason.
    """
    return feed_service.report_post(
        db,
        post_id=post_id,
        user=current_user,
        reason=payload.reason
    )


@router.patch(
    "/report_post/{post_id}",
    response_model=ReportPostResponse,
    status_code=status.HTTP_200_OK,
    summary="Report an Inappropriate Post (PATCH)"
)
def report_post_patch(
    post_id: int,
    payload: ReportPostRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows any user to report another user's post to admin with a reason (PATCH format).
    """
    return feed_service.report_post(
        db,
        post_id=post_id,
        user=current_user,
        reason=payload.reason
    )


# ==========================================
# 3. CREATE & GET COMMENTS
# ==========================================

@router.post(
    "/create_comment/{post_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Comment to Post"
)
def create_comment(
    post_id: int,
    payload: CommentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Adds a comment to a feed post.
    """
    return feed_service.add_comment(
        db,
        post_id=post_id,
        user=current_user,
        comment_text=payload.comment_text
    )


@router.get(
    "/create_comment/{post_id}",
    response_model=List[CommentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get All Comments of a Post"
)
def get_comments(
    post_id: int,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """
    Shows all comments with user Name, Image, comment_time, comment_text,
    reaction_count, and whether the logged-in user has reacted.
    """
    user_id = current_user.id if current_user else None
    return feed_service.get_comments_for_post(db, post_id=post_id, current_user_id=user_id)


# ==========================================
# 4. REACTION ON COMMENT (LOVE REACT / UN-REACT)
# ==========================================

@router.patch(
    "/reaction/{post_id}/{comment_id}",
    response_model=ReactionToggleResponse,
    status_code=status.HTTP_200_OK,
    summary="Love React or Un-react to Comment"
)
def toggle_reaction(
    post_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows user to give just one Love react or un-react to any specific comment.
    """
    return feed_service.toggle_comment_reaction(
        db,
        post_id=post_id,
        comment_id=comment_id,
        user=current_user
    )


@router.get(
    "/reaction/{post_id}/{comment_id}",
    response_model=List[ReactionUserDetail],
    status_code=status.HTTP_200_OK,
    summary="Get All Reactions of a Comment"
)
def get_reactions(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db)
):
    """
    Returns the list of all users who loved/reacted to this specific comment.
    """
    return feed_service.get_comment_reactions(db, post_id=post_id, comment_id=comment_id)
