import enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas import Sender


class ChatSessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_favorite: bool
    user_id: str
    created_at: datetime
    updated_at: datetime
    session_metadata: dict[str, Any]


class ChatSessionCreate(BaseModel):
    session_metadata: dict[str, Any] = {}


class ChatSessionUpdate(BaseModel):
    is_favorite: bool | None = None
    session_metadata: dict[str, Any] | None = None


class ChatMessageCreate(BaseModel):
    sender: Sender
    content: str


class ChatMessageFeedbackType(str, enum.Enum):
    LIKE_ACCURATE_INFORMATION = "LIKE_ACCURATE_INFORMATION"
    LIKE_HELPFUL_ANSWER = "LIKE_HELPFUL_ANSWER"

    DISLIKE_NOT_RELEVANT = "DISLIKE_NOT_RELEVANT"
    DISLIKE_INCORRECT_INFORMATION = "DISLIKE_INCORRECT_INFORMATION"
    DISLIKE_INCOMPLETE_ANSWER = "DISLIKE_INCOMPLETE_ANSWER"
    DISLIKE_OTHER = "DISLIKE_OTHER"


class ChatMessageFeedbackCreate(BaseModel):
    chat_message_id: str
    feedback: ChatMessageFeedbackType
    detail: str | None = None


class ChatMessageFeedbackPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    chat_message_id: str
    feedback: ChatMessageFeedbackType
    created_at: datetime


class ChatMessagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    chat_session_id: str
    sender: Sender
    content: str
    created_at: datetime
    chat_message_feedback: ChatMessageFeedbackPublic | None = None
