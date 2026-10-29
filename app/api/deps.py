"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Dependency Injection (DI):
   - FastAPI-এর Depends মেকানিজম ব্যবহার করে ডিপেনডেন্সি ইনজেক্ট করা হয়।
   - এর ফলে কন্ট্রোলার/রাউটার নিজে কোনো অবজেক্ট তৈরি করে না, ফ্রেমওয়ার্ক ইনজেক্ট করে।
2. Clean Role-Based Authorization (RBAC):
   - get_current_user: সাধারণ অথেনটিকেশন চেক করে।
   - get_current_admin: শুধুমাত্র অ্যাডমিন রোল নিশ্চিত করে (DIP ও ISP প্রিন্সিপাল)।
3. Fail-Fast Security:
   - ইনভ্যালিড টোকেন বা এক্সপায়ারড টোকেন রিকোয়েস্টের শুরুতেই 401 Unauthorized দিয়ে আটকে দেয়।
================================================================================
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import http_401_unauthorized, http_403_forbidden
from app.models.user import User, UserRole
from app.repositories.user_repository import user_repository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> User:
    """
    Validates JWT access token and returns the authenticated User instance.
    """
    if not token:
        raise http_401_unauthorized("Authentication token required.")

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_type = payload.get("type")
        if token_type != "access":
            raise http_401_unauthorized("Invalid token type. Access token expected.")
        
        user_id = payload.get("sub")
        if not user_id:
            raise http_401_unauthorized("Token payload missing subject.")
            
        user_id_int = int(user_id)
    except (jwt.PyJWTError, ValueError):
        raise http_401_unauthorized("Invalid or expired authentication token.")

    user = user_repository.get(db, user_id_int)
    if not user:
        raise http_401_unauthorized("User associated with this token does not exist.")

    if not user.is_active:
        raise http_401_unauthorized("User account is inactive.")

    return user


def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensures the requesting user possesses administrative privileges.
    """
    if current_user.role != UserRole.ADMIN:
        raise http_403_forbidden("Administrative privileges required for this action.")
    return current_user


def get_optional_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    Permits optional authentication (e.g. For quotes submitted by guests or logged-in users).
    """
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id:
            return user_repository.get(db, int(user_id))
    except Exception:
        return None
    return None
