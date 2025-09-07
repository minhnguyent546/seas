import secrets
from datetime import timedelta
from typing import Annotated, Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

import app.auth.service as auth_service
import app.users.service as users_service
from app.auth.schemas import TokenData
from app.auth.utils import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.core.database import AsyncSession
from app.users.models import User
from app.users.schemas import OAuthProvider, UserCreate, UserRegister, UserRole


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
) -> TokenData:
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
    return TokenData(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_token_expires.total_seconds(),
    )


async def google_oauth2_callback(
    session: AsyncSession, auth_access_token: dict[str, Any]
) -> TokenData:
    userinfo = auth_access_token.get("userinfo")
    access_token = auth_access_token.get("access_token")
    if not userinfo:
        # Fetch user info if not included in the token
        async with httpx.AsyncClient() as client:
            try:
                headers = {"Authorization": f"Bearer {access_token}"}
                response = await client.get(
                    str(settings.GOOGLE_OAUTH2_USERINFO_URL), headers=headers
                )
                response.raise_for_status()
                userinfo = response.json()
            except httpx.HTTPStatusError as err:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to fetch user information from Google: {str(err)}",
                ) from err

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

        # Check if user was created with a different OAuth provider
        if existing_user.oauth_provider != OAuthProvider.GOOGLE:
            if existing_user.oauth_provider == OAuthProvider.LOCAL:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An account with email {email} already exists. Please sign in with your username and password, or reset your password if you forgot it.",
                )
            else:
                # User created with different OAuth provider (e.g., GitHub)
                provider_name = existing_user.oauth_provider.value.title()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An account with email {email} already exists and was created using {provider_name}. Please sign in with {provider_name} instead.",
                )

        # Update existing user information if needed
        if existing_user.full_name != full_name:
            existing_user.full_name = full_name
            await session.commit()
        user = existing_user
    else:
        # create a new user
        if "@" in email:
            base_username = email.split("@")[0]
        else:
            base_username = email
        distinct_username = await users_service.get_distinct_username(
            session=session, base_username=base_username
        )
        random_password = secrets.token_urlsafe(32)
        user_create = UserCreate(
            username=distinct_username,
            email=email,
            full_name=full_name,
            is_active=True,
            password=hash_password(random_password),
            role=UserRole.USER,
            oauth_provider=OAuthProvider.GOOGLE,
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
    return TokenData(
        access_token=access_token,
        token_type="bearer",
        expires_in=access_token_expires.total_seconds(),
    )


async def github_oauth2_callback(
    session: AsyncSession, auth_access_token: dict[str, Any]
) -> TokenData:
    access_token = auth_access_token.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token received from GitHub OAuth2",
        )

    # Fetch user info from GitHub API
    async with httpx.AsyncClient() as client:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            # Get user profile
            user_response = await client.get(
                str(settings.GITHUB_OAUTH2_USERINFO_URL), headers=headers
            )
            user_response.raise_for_status()
            user_data = user_response.json()

            # Get user email if not public
            email = user_data.get("email")
            if not email:
                email_response = await client.get(
                    "https://api.github.com/user/emails", headers=headers
                )
                email_response.raise_for_status()
                emails = email_response.json()
                # Get the primary email
                for email_info in emails:
                    if email_info.get("primary", False):
                        email = email_info.get("email")
                        break

        except httpx.HTTPStatusError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to fetch user information from GitHub: {str(err)}",
            ) from err

    # Extract user information
    full_name = user_data.get("name") or user_data.get("login")
    if not email or not full_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incomplete user information received from GitHub OAuth2",
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

        # Check if user was created with a different OAuth provider
        if existing_user.oauth_provider != OAuthProvider.GITHUB:
            if existing_user.oauth_provider == OAuthProvider.LOCAL:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An account with email {email} already exists. Please sign in with your username and password, or reset your password if you forgot it.",
                )
            else:
                # User created with different OAuth provider (e.g., Google)
                provider_name = existing_user.oauth_provider.value.title()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"An account with email {email} already exists and was created using {provider_name}. Please sign in with {provider_name} instead.",
                )

        # Update existing user information if needed
        if existing_user.full_name != full_name:
            existing_user.full_name = full_name
            await session.commit()
        user = existing_user
    else:
        # create a new user
        if "@" in email:
            base_username = email.split("@")[0]
        else:
            base_username = user_data.get("login", email)
        distinct_username = await users_service.get_distinct_username(
            session=session, base_username=base_username
        )
        random_password = secrets.token_urlsafe(32)
        user_create = UserCreate(
            username=distinct_username,
            email=email,
            full_name=full_name,
            is_active=True,
            password=hash_password(random_password),
            role=UserRole.USER,
            oauth_provider=OAuthProvider.GITHUB,
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
    return TokenData(
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
        # Check if user was created with OAuth provider
        if db_user.oauth_provider != OAuthProvider.LOCAL:
            provider_name = db_user.oauth_provider.value.title()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"An account with email {user_register.email} already exists and was created using {provider_name}. Please sign in with {provider_name} instead.",
            )
        else:
            # User was created with local registration
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists",
            )
    user_register.password = hash_password(user_register.password)
    user = User(
        **user_register.model_dump(),
        is_active=True,
        role=UserRole.USER,
        oauth_provider=OAuthProvider.LOCAL,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
