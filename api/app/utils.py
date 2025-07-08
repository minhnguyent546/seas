import pathlib
from datetime import datetime, timedelta
from typing import Any

import emails
import jwt
from jinja2 import Template
from loguru import logger

from app.core.config import settings, timezone_vi
from app.schemas import EmailData


def serialize_datetime(value: datetime) -> str:
    try:
        value = value.astimezone(timezone_vi).replace(tzinfo=timezone_vi)
    except Exception as e:
        logger.error(
            f"Error converting timezone to {timezone_vi}: {e}. Leaving as is."
        )
    return value.strftime("%Y-%m-%d - %H:%M:%S")


def render_email_template(*, template: str, context: dict[str, Any]) -> str:
    template_path = (
        pathlib.Path(__file__).parent / "templates" / "build" / template
    )
    template_str = template_path.read_text(encoding="utf-8")
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *, email_to: str, subject: str = "", html_content: str = ""
) -> None:
    if not settings.emails_enabled:
        raise RuntimeError("Email environment variables are not configured.")

    message = emails.Message(
        charset="utf-8",
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True

    if settings.SMTP_USER is not None:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD is not None:
        smtp_options["password"] = settings.SMTP_PASSWORD
    response = message.send(to=email_to, smtp=smtp_options)  # noqa: F841
    logger.info("'Sent email to {email_to} with subject: {subject}'")


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template="test_email.html",
        context={"project_name": project_name, "email": email_to},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_email(
    email_to: str, username: str, token: str
) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password reset request for {username}"
    reset_password_url = (
        f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    )
    html_content = render_email_template(
        template="reset_password.html",
        context={
            "project_name": project_name,
            "username": username,
            "reset_password_url": reset_password_url,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    time_delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(tz=timezone_vi)
    expire = now + time_delta
    exp = expire.timestamp()
    to_encode = {"exp": exp, "nbf": now.timestamp(), "sub": email}
    encoded_jwt = jwt.encode(
        payload=to_encode,
        key=settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            jwt=token, key=settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return decoded_token.get("sub")
    except jwt.InvalidTokenError:
        logger.error("Invalid password reset token")
        return None
