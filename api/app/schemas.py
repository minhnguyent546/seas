"""Global schemas for the application."""

import enum

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


class EmailData(BaseModel):
    html_content: str
    subject: str
