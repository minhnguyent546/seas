from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlencode

import jwt
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from passlib.context import CryptContext

from app.core.config import settings
from app.users.schemas import OAuthProvider

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: Any,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=30)
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"sub": str(subject), "exp": expire}
    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def handle_oauth_error(
    provider: OAuthProvider, error: HTTPException | Exception
) -> RedirectResponse:
    """Handle OAuth errors by redirecting to frontend with error details."""
    if isinstance(error, HTTPException):
        error_detail = (
            error.detail
            if error.status_code in [400, 401, 403]
            else "Authentication failed"
        )
    else:
        error_detail = (
            f"Error during {provider.value.title()} OAuth2 authorization"
        )

    query_params = {
        "oauth2-provider": provider.value,
        "oauth2-error": error_detail,
    }
    frontend_url = f"{settings.FRONTEND_HOST}/login?{urlencode(query_params)}"
    return RedirectResponse(
        url=frontend_url, status_code=status.HTTP_303_SEE_OTHER
    )
