import os
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Any

import emails
import jwt
import markdown_to_data
from fastapi import BackgroundTasks, HTTPException, UploadFile, status
from fastapi.routing import APIRoute
from markdown_to_data.to_md.to_md_parser import to_md_parser

from app.core.config import settings, timezone_vi
from app.core.logger import logger
from app.schemas import EmailData
from app.templates import email_templates


def serialize_datetime(value: datetime) -> str:
    try:
        value = value.astimezone(timezone_vi).replace(tzinfo=timezone_vi)
    except Exception as e:
        logger.error(
            f"Error converting timezone to {timezone_vi}: {e}. Leaving as is."
        )
    return value.strftime("%Y-%m-%d - %H:%M:%S")


def render_email_template(*, template: str, context: dict[str, Any]) -> str:
    template_path = email_templates.get_template(template)
    html_content = template_path.render(context)
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
    response = message.send(to=email_to, smtp=settings.smtp_options)
    logger.info(f"Sent email to {email_to} with subject: {subject}")

    if not response.success:
        logger.error(f"Failed to send email: {response.error}")
        logger.error(f"SMTP options: {settings.smtp_options}")
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail="Failed to send email. Please try again later.",
        )
    else:
        logger.info("Email sent successfully")


def send_email_in_background(
    *,
    background_tasks: BackgroundTasks,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    # TODO: consider replace this with Celery
    if not settings.emails_enabled:
        raise RuntimeError("Email environment variables are not configured.")

    message = emails.Message(
        charset="utf-8",
        subject=subject,
        html=html_content,
        mail_from=(settings.EMAILS_FROM_NAME, settings.EMAILS_FROM_EMAIL),
    )
    # Don't send immediately, only add to background tasks
    background_tasks.add_task(
        message.send, to=email_to, smtp=settings.smtp_options
    )
    logger.info(
        f"Added email to background tasks for {email_to} with subject: {subject}"
    )


def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template="testing_email.html",
        context={
            "project_name": project_name,
            "email": email_to,
            "sender_address": settings.SENDER_ADDRESS,
        },
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
            "sender_address": settings.SENDER_ADDRESS,
            "link": reset_password_url,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "email": email_to,
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


def custom_generate_unique_id(route: APIRoute) -> str:
    if route.tags:
        return f"{route.tags[0]}-{route.name}"
    return f"default-{route.name}"


def save_uploaded_file(file: UploadFile) -> str:
    unique_name = f"{uuid.uuid4()}.md"
    file_path = os.path.join(settings.DOC_UPLOAD_DIR, unique_name)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return file_path


def extract_markdown_tables(
    md_content: str, remove_tables: bool = True
) -> tuple[str, list[str]]:
    if not md_content:
        return (md_content, [])

    try:
        md = markdown_to_data.Markdown(md_content)
        elements = md.md_list
        table_elements = []
        new_elements = []
        for element in elements:
            if "table" in element.keys():
                if len(element.keys()) > 1:
                    raise RuntimeError(
                        f"Expected only one key in table element, found {element.keys()}"
                    )
                table_elements.append(element)
            else:
                new_elements.append(element)

        if remove_tables:
            new_content = to_md_parser(new_elements, spacer=1)
        else:
            new_content = md_content

        tables = []
        if table_elements:
            tables = [
                to_md_parser([table_element], spacer=1)
                for table_element in table_elements
            ]

        return (new_content, tables)
    except Exception as e:
        logger.error(f"Failed to extract markdown tables: {e}")
        return (md_content, [])


def get_langchain_llm(model_name: str, **kwargs):
    if "/" not in model_name:
        raise ValueError(
            f"Expected model name have the format <provider>/<model_name>, got {model_name}"
        )

    provider, model_name = model_name.split("/")
    if provider == "google":
        from langchain_google_genai import GoogleGenerativeAI

        return GoogleGenerativeAI(model=model_name, **kwargs)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=model_name, **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider}")
