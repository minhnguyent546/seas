"""Global schemas for the application."""

import enum
from typing import Any

from pydantic import BaseModel


class Sender(str, enum.Enum):
    USER = "USER"
    BOT = "BOT"
    SYSTEM = "SYSTEM"


class MessageStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class MessageResponse(BaseModel):
    status: MessageStatus = MessageStatus.SUCCESS
    message: str
    extra: dict[str, Any] = {}


class EmailData(BaseModel):
    html_content: str
    subject: str


class LoginResponse(BaseModel):
    message: str
    token_type: str = "bearer"
    expires_in: float  # in seconds
