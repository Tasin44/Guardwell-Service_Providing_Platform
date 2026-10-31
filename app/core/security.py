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
import secrets #Cryptographically secure random number generator (unlike random, it's safe for security use).

from typing import Any, Dict, Optional, Union
import bcrypt#library for password hashing/verifying.
import jwt#library for creating/validating JSON Web Tokens.
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


#Its responsibility is to create an access JWT token.
def create_access_token(
    subject: Union[str, Any],#Usually the user's ID
    expires_delta: Optional[timedelta] = None,
    claims: Optional[Dict[str, Any]] = None#Additional information to store in the token
) -> str:#Returns the JWT as a string

    """Creates a signed JWT Access Token."""
    #If a custom expiration was passed, use it; otherwise use the default from config.
    now = datetime.now(timezone.utc)#Gets the current UTC time.
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),           # who the token belongs to (e.g., user db ID)
        "exp": int(expire.timestamp()),# expiry time (Unix seconds)
        "iat": int(now.timestamp()),   # "issued at" time
        "type": "access"               # token type marker
    }
    if claims:
        to_encode.update(claims)


# Be careful: JWT payloads are encoded, not encrypted. Don't put passwords, secrets, or sensitive personal data inside them. Also, trusted claims should not be allowed to overwrite reserved fields such as sub, exp, or type.

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)



def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT Refresh Token with extended validity."""
    now = datetime.now(timezone.utc)#Gets the current UTC time.
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {#This creates the refresh token's payload.
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

