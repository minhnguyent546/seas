from typing import Annotated

from authlib.integrations.starlette_client import OAuth
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr

import app.auth.service as auth_service
import app.users.service as users_service
import app.utils as app_utils
from app.auth.schemas import NewPassword
from app.auth.utils import hash_password
from app.core.config import settings
from app.deps import (
    AsyncSessionDep,
    CurrentActiveUserDep,
    get_current_superuser,
)
from app.schemas import LoginResponse, MessageResponse
from app.users.schemas import UserPublic, UserRegister

oauth_client = OAuth()
oauth_client.register(
    name="google",
    client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
    client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid profile email",
    },
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    session: AsyncSessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
):
    """Login with username and password."""
    token = await auth_service.login_for_access_token(
        session=session, form_data=form_data
    )
    response.set_cookie(
        key="access_token",
        value=token.access_token,
        max_age=int(token.expires_in),
        **settings.cookie_common_options,
    )
    return LoginResponse(
        message="Login successful",
        token_type="bearer",
        expires_in=token.expires_in,
    )


@router.get("/login/google-oauth2", status_code=status.HTTP_303_SEE_OTHER)
async def login_via_google_oauth2(
    request: Request, response_class=RedirectResponse
):
    """Login with Google OAuth2."""
    redirect_uri = request.url_for("google_oauth2_callback")
    return await oauth_client.google.authorize_redirect(request, redirect_uri)  # pyright: ignore[reportOptionalMemberAccess]


@router.get("/login/google-oauth2/callback", response_class=RedirectResponse)
async def google_oauth2_callback(session: AsyncSessionDep, request: Request):
    """Callback to handle redirect from Google OAuth2."""
    try:
        # Let Authlib handle the state validation automatically
        auth_access_token = await oauth_client.google.authorize_access_token(  # pyright: ignore[reportOptionalMemberAccess]
            request
        )

        token = await auth_service.google_oauth2_callback(
            session=session, auth_access_token=auth_access_token
        )
        response = RedirectResponse(
            url=settings.FRONTEND_HOST, status_code=status.HTTP_303_SEE_OTHER
        )
        response.set_cookie(
            key="access_token",
            value=token.access_token,
            max_age=int(token.expires_in),
            **settings.cookie_common_options,
        )
        return response
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error during Google OAuth2 authorization: {str(err)}",
        ) from err


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


@router.post("/signout", response_model=MessageResponse)
async def signout(response: Response):
    """Signout the user"""
    response.delete_cookie("access_token", **settings.cookie_common_options)
    return MessageResponse(message="Sign out successful")


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
