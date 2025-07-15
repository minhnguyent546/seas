from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from pydantic import ValidationError

import app.users.service as user_service
from app.core.config import settings
from app.core.database import AsyncSessionDep
from app.users.models import User
from app.users.schemas import UserRole

cookie_scheme = APIKeyCookie(name="access_token", auto_error=False)


async def get_current_user(
    session: AsyncSessionDep,
    access_token: Annotated[str | None, Depends(cookie_scheme)] = None,
) -> User:
    if access_token is None:
        detail = "Not authenticated"
        if settings.ENVIRONMENT == "development":
            detail += " (No access token provided in cookie)"

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Cookie"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Cookie"},
    )
    try:
        payload = jwt.decode(
            jwt=access_token,
            key=settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (jwt.InvalidTokenError, ValidationError) as e:
        raise credentials_exception from e

    user = await user_service.get_user_by_id(session=session, user_id=user_id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_superuser(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    if not current_user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Should be a superuser/admin",
        )
    return current_user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
CurrentActiveUserDep = Annotated[User, Depends(get_current_active_user)]
CurrentSuperuserDep = Annotated[User, Depends(get_current_superuser)]
