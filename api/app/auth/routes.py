from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

import app.auth.service as auth_service
import app.users.service as users_service
import app.utils as app_utils
from app.auth.schemas import NewPassword, Token
from app.auth.utils import hash_password
from app.deps import (
    AsyncSessionDep,
    CurrentActiveUserDep,
    get_current_superuser,
)
from app.schemas import MessageResponse
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


@router.post("/password-recovery/{email}", response_model=MessageResponse)
async def recover_password(session: AsyncSessionDep, email: EmailStr):
    """Recover password by email."""
    user = await users_service.get_user_by_email(session=session, email=email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with this email.",
        )
    password_reset_token = app_utils.generate_password_reset_token(
        email=user.email
    )
    email_data = app_utils.generate_password_reset_email(
        email_to=user.email, username=user.username, token=password_reset_token
    )
    app_utils.send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return MessageResponse(message="Password reset email sent")


@router.post("/password-reset", response_model=MessageResponse)
async def reset_password(session: AsyncSessionDep, new_password: NewPassword):
    """
    Reset password
    """
    email = app_utils.verify_password_reset_token(token=new_password.token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token.",
        )
    user = await users_service.get_user_by_email(session=session, email=email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with this email.",
        )
    hashed_password = hash_password(new_password.new_password)
    user.password = hashed_password
    session.add(user)
    await session.commit()
    return MessageResponse(message="Password reset successfully")
    # TODO: invalidate this reset password token (e.g. using token blacklist)


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_superuser)],
    response_class=HTMLResponse,
)
async def recover_password_html_content(
    session: AsyncSessionDep, email: EmailStr
):
    """
    Recover password with HTML. Requires superuser permissions.
    """
    user = await users_service.get_user_by_email(session=session, email=email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with this email.",
        )
    password_reset_token = app_utils.generate_password_reset_token(
        email=user.email
    )
    email_data = app_utils.generate_password_reset_email(
        email_to=user.email, username=user.username, token=password_reset_token
    )
    return HTMLResponse(content=email_data.html_content, status_code=200)
