from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import app.auth.service as auth_service
import app.users.service as user_service
from app.auth.schemas import Token
from app.auth.utils import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.core.database import AsyncSession
from app.users.models import User
from app.users.schemas import UserRegister, UserRole


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    db_user = await user_service.get_user_by_username(
        session=session, username=username
    )
    if db_user is None:
        return None
    if not verify_password(
        plain_password=password, hashed_password=db_user.password
    ):
        return None
    return db_user


async def login_for_access_token(
    session: AsyncSession,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await auth_service.authenticate_user(
        session=session,
        username=form_data.username,
        password=form_data.password,
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_token_expires.total_seconds(),
    )


async def signup_user(
    session: AsyncSession, user_register: UserRegister
) -> User:
    db_user = await user_service.get_user_by_username(
        session=session, username=user_register.username
    )
    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    db_user = await user_service.get_user_by_email(
        session=session, email=user_register.email
    )
    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )
    user_register.password = hash_password(user_register.password)
    user = User(
        **user_register.model_dump(), is_active=True, role=UserRole.USER
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
