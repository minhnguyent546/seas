"""Global schemas for the application."""

import enum

from pydantic import BaseModel


class MessageStatus(str, enum.Enum):
    SUCCESS = "success"
    ERROR = "error"


class MessageResponse(BaseModel):
    status: MessageStatus = MessageStatus.SUCCESS
    message: str
