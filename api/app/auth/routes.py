from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

import app.auth.service as auth_service
from app.auth.schemas import NewPassword, Token
from app.deps import AsyncSessionDep, CurrentActiveUserDep
from app.users.schemas import UserPublic, UserRegister

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login/access-token", response_model=Token)
async def login_for_access_token(
    session: AsyncSessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Login with username and password to get an access token for future requests."""
    token = await auth_service.login_for_access_token(
        session=session, form_data=form_data
    )
    return token


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
    user = await auth_service.signup_user(
        session=session, user_register=user_register
    )
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
