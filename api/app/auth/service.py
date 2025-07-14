import secrets
from datetime import timedelta
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import app.auth.service as auth_service
import app.users.service as users_service
from app.auth.schemas import Token
from app.auth.utils import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.core.database import AsyncSession
from app.users.models import User
from app.users.schemas import UserCreate, UserRegister, UserRole


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    db_user = await users_service.get_user_by_username(
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


async def google_oauth2_callback(
    session: AsyncSession, auth_access_token: dict[str, Any]
) -> Token:
    userinfo = auth_access_token.get("userinfo")
    access_token = auth_access_token.get("access_token")
    if not userinfo:
        # Fetch user info if not included in the token
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = await client.get(
                str(settings.GOOGLE_OAUTH2_USERINFO_URL), headers=headers
            )
            userinfo = response.json()

    email = userinfo.get("email")
    full_name = userinfo.get("name")
    if not email or not full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incomplete user information received from Google OAuth2",
        )

    existing_user = await users_service.get_user_by_email(
        session=session, email=email
    )
    user = None
    if existing_user is not None:
        if not existing_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Inactive user",
            )

        # Update existing user information if needed
        existing_user.full_name = full_name
        await session.commit()
        user = existing_user
    else:
        # Generate username from email, handling potential conflicts
        base_username = email.split("@")[0]
        username = base_username
        counter = 1
        while await users_service.get_user_by_username(
            session=session, username=username
        ):
            username = f"{base_username}_{counter}"
            counter += 1

        random_password = secrets.token_urlsafe(32)
        user_create = UserCreate(
            username=username,
            email=email,
            full_name=full_name,
            is_active=True,
            password=hash_password(random_password),
            role=UserRole.USER,
        )
        user = User(**user_create.model_dump())
        session.add(user)
        await session.commit()

    assert user is not None

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
    db_user = await users_service.get_user_by_username(
        session=session, username=user_register.username
    )
    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    db_user = await users_service.get_user_by_email(
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
