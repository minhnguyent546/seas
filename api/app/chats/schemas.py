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


class ChatMessagePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    chat_session_id: str
    sender: Sender
    content: str
    created_at: datetime
