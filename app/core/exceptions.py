"""
================================================================================
ARCHITECTURE & DESIGN PATTERN:
1. Domain Exceptions & Separation of Concerns (SoC):
   - বিজনেস লজিক বা সার্ভিস লেয়ার HTTP-এর মতো ফ্রেমওয়ার্ক স্পেসিফিক কোড জানবে না।
   - সার্ভিস লেয়ার কাস্টম ডোমেইন এক্সেপশন রেইজ করবে, যা প্রেজেন্টেশন লেয়ারে হ্যান্ডল হবে।
2. Fail-Fast Principle:
   - কোনো ভ্যালিডেশন বা বিজনেস রুল ফেইল করলেই তৎক্ষণাৎ এক্সপ্লিসিট এক্সেপশন থ্রো করা হবে।
================================================================================
"""

from fastapi import HTTPException, status


class GuardwellException(Exception):
    """Base exception for all domain-specific errors in Guardwell."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(GuardwellException):
    """Raised when a requested database entity does not exist."""
    pass


class InvalidCredentialsException(GuardwellException):
    """Raised when user authentication credentials fail."""
    pass


class OTPExpiredOrInvalidException(GuardwellException):
    """Raised when an OTP is incorrect, expired, or already used."""
    pass


class UserAlreadyExistsException(GuardwellException):
    """Raised during signup if the email or phone number is already registered."""
    pass


class PermissionDeniedException(GuardwellException):
    """Raised when a user lacks appropriate role or privileges."""
    pass


class FeedBannedException(GuardwellException):
    """Raised when a user banned from the feed attempts social interactions."""
    pass


# Convenience HTTP Exception Factories for FastAPI Presentation Layer
def http_400_bad_request(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def http_401_unauthorized(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def http_403_forbidden(detail: str = "You do not have permission to perform this action") -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def http_404_not_found(detail: str = "Resource not found") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def http_409_conflict(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)