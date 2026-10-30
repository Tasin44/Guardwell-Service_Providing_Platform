"""
Standard Response Middleware and Helpers for Guardwell API.
Implements uniform response structure across all endpoints:
{
    "success": bool,
    "statusCode": int,
    "message": str,
    "data": any,
    "timestamp": ISO datetime string
}
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse, Response
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException


def extract_first_error(errors: Any) -> Optional[str]:
    """
    Extract the first readable error message from validation errors dict/list.
    Handles Pydantic validation error lists and nested dictionaries.
    """
    if isinstance(errors, dict):
        if "non_field_errors" in errors:
            extracted = extract_first_error(errors.get("non_field_errors"))
            if extracted:
                return extracted
        for field, value in errors.items():
            if isinstance(value, list) and value:
                nested = value[0]
                if isinstance(nested, (dict, list)):
                    extracted = extract_first_error(nested)
                    if extracted:
                        return f"{field} :: {extracted}"
                return f"{field} :: {nested}"
            if isinstance(value, str):
                return f"{field} :: {value}"
            extracted = extract_first_error(value)
            if extracted:
                return f"{field} :: {extracted}"
    elif isinstance(errors, list) and errors:
        first = errors[0]
        if isinstance(first, dict):
            # Typical Pydantic validation error format
            loc = " -> ".join([str(x) for x in first.get("loc", []) if x != "body"])
            msg = first.get("msg", "Validation error")
            return f"{loc}: {msg}" if loc else msg
        extracted = extract_first_error(first)
        if extracted:
            return extracted
    elif errors:
        return str(errors)
    return None


def success_response(
    data: Any = None,
    message: str = "Success",
    status_code: int = status.HTTP_200_OK
) -> JSONResponse:
    """Helper for explicit success responses."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "statusCode": status_code,
            "message": message,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


def error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    data: Any = None
) -> JSONResponse:
    """Helper for explicit error responses."""
    detail = extract_first_error(data)
    if detail and detail not in message:
        message = f"{message}: {detail}"
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "statusCode": status_code,
            "message": message,
            "data": data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    )


class StandardResponseMiddleware(BaseHTTPMiddleware):
    """
    Middleware that automatically transforms successful JSON responses
    into the standard envelope format if not already formatted.
    """
    async def dispatch(self, request: Request, call_next):
        # Exclude Swagger/OpenAPI docs and static file uploads from formatting
        path = request.url.path
        if (
            path in ["/docs", "/redoc", "/openapi.json"]
            or path.startswith("/admin")
            or path.startswith("/uploads")
            or path.endswith("/openapi.json")
        ):
            return await call_next(request)

        response: Response = await call_next(request)

        # Only transform application/json responses
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            # Read response body stream
            body_bytes = b""
            async for chunk in response.body_iterator:
                body_bytes += chunk

            try:
                raw_json = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                return Response(
                    content=body_bytes,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )

            # If response is already in standard format, return as is
            if isinstance(raw_json, dict) and "success" in raw_json and "statusCode" in raw_json:
                return JSONResponse(
                    status_code=response.status_code,
                    content=raw_json,
                    headers=dict(response.headers)
                )

            # Determine message based on response status code
            status_code = response.status_code
            is_success = 200 <= status_code < 400
            
            message = "Success" if is_success else "Error"
            if isinstance(raw_json, dict) and "message" in raw_json and isinstance(raw_json["message"], str):
                message = raw_json.pop("message")

            formatted_payload = {
                "success": is_success,
                "statusCode": status_code,
                "message": message,
                "data": raw_json if is_success else None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            if not is_success:
                formatted_payload["data"] = raw_json

            # Remove content-length as length changed
            headers = dict(response.headers)
            headers.pop("content-length", None)

            return JSONResponse(
                status_code=status_code,
                content=formatted_payload,
                headers=headers
            )

        return response


import re
from sqlalchemy.exc import IntegrityError


async def custom_integrity_exception_handler(request: Request, exc: IntegrityError):
    """
    Translates raw database IntegrityError (like UNIQUE constraints)
    into a clean, readable message.
    """
    raw_msg = str(exc.orig) if hasattr(exc, "orig") else str(exc)
    
    # Check for UNIQUE constraint failed: table.column
    unique_match = re.search(r"UNIQUE constraint failed:\s*([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)", raw_msg, re.IGNORECASE)
    if unique_match:
        table_name, column_name = unique_match.group(1), unique_match.group(2)
        readable_field = column_name.replace("_", " ").title()
        user_friendly_msg = f"An account with this {readable_field} already exists."
        return error_response(
            message=user_friendly_msg,
            status_code=status.HTTP_409_CONFLICT,
            data={"field": column_name, "error": f"{readable_field} must be unique."}
        )
    
    # Check for NOT NULL constraint
    not_null_match = re.search(r"NOT NULL constraint failed:\s*([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)", raw_msg, re.IGNORECASE)
    if not_null_match:
        column_name = not_null_match.group(2)
        readable_field = column_name.replace("_", " ").title()
        return error_response(
            message=f"{readable_field} cannot be empty.",
            status_code=status.HTTP_400_BAD_REQUEST,
            data={"field": column_name}
        )

    return error_response(
        message="Database constraint violation occurred.",
        status_code=status.HTTP_409_CONFLICT,
        data={"detail": raw_msg}
    )


# Global Exception Handlers to match DRF error response
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "An HTTP error occurred"
    data = exc.detail if not isinstance(exc.detail, str) else None
    return error_response(message=message, status_code=exc.status_code, data=data)


async def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    first_err = extract_first_error(exc.errors())
    message = f"Validation Error: {first_err}" if first_err else "Validation Error"
    return error_response(
        message=message,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        data=exc.errors()
    )


async def custom_general_exception_handler(request: Request, exc: Exception):
    return error_response(
        message=f"An unexpected error occurred: {str(exc)}",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
