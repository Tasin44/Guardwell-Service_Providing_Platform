"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Security by Default (Native bcrypt & PyJWT):
   - Python 3.14+ compatible modern cryptography.
   - bcrypt library is used directly for battle-tested, salted password hashing.
   - PyJWT provides standard RFC 7519 JWT encoding & decoding with HS256.
2. Token Separation:
   - Access tokens (short-lived)
   - Refresh tokens (extended)
   - Password reset tokens (single-use scope)
3. Cryptographically Secure OTP:
   - Python secrets module generates unpredictable 6-digit numeric codes.
================================================================================
"""

from datetime import datetime, timedelta, timezone
import secrets
from typing import Any, Dict, Optional, Union
import bcrypt
import jwt
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against the hashed password stored in DB."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hashes a plaintext password using modern salted bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    claims: Optional[Dict[str, Any]] = None
) -> str:
    """Creates a signed JWT Access Token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "access"
    }
    if claims:
        to_encode.update(claims)

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT Refresh Token with extended validity."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "refresh"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_password_reset_token(subject: Union[str, Any]) -> str:
    """Generates a short-lived (15 mins) token specifically for Password Reset."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=15)
    to_encode = {
        "sub": str(subject),
        "exp": int(expire.timestamp()),
        "iat": int(now.timestamp()),
        "type": "password_reset"
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def generate_six_digit_otp() -> str:
    """Generates a 6-digit numeric OTP string using Python's secrets module."""
    return f"{secrets.randbelow(900000) + 100000}"























