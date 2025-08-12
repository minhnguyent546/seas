from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer

from app.schemas import Sender
from app.utils import serialize_datetime


class ChatSessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    is_favorite: bool
    user_id: str
    created_at: datetime
    updated_at: datetime
    session_metadata: dict[str, Any]

    # @field_serializer("created_at")
    # def serialize_created_at(self, value: datetime, _info):
    #     return serialize_datetime(value)

    # @field_serializer("updated_at")
    # def serialize_updated_at(self, value: datetime, _info):
    #     return serialize_datetime(value)


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

    # @field_serializer("created_at")
    # def serialize_created_at(self, value: datetime, _info):
    #     return serialize_datetime(value)
