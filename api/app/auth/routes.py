from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

import app.auth.service as auth_service
import app.users.service as user_service
from app.auth.schemas import NewPassword, Token
from app.auth.utils import create_access_token, hash_password
from app.core.config import settings
from app.deps import AsyncSessionDep, CurrentActiveUserDep
from app.users.models import User
from app.users.schemas import UserPublic, UserRegister, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login/access-token", response_model=Token)
async def login_for_access_token(
    session: AsyncSessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """
    Login with username and password to get an access token for future requests."""
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


@router.post(
    "/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def signup(
    session: AsyncSessionDep,
    user_register: UserRegister,
):
    """
    Sign up a new user.
    """
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


@router.post("/login/test-token", response_model=UserPublic)
async def test_token(current_user: CurrentActiveUserDep):
    """Test if your access token is valid."""
    return current_user


@router.post("/password-recovery/{email}")
async def recover_password(session: AsyncSessionDep, email: EmailStr):
    """Recover password by email."""
    pass


@router.post("/password-reset")
async def reset_password(session: AsyncSessionDep, new_password: NewPassword):
    """
    Reset password using a token.
    The token should be sent to the user's email during the password recovery process.
    """
    pass
