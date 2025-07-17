import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.chats.schemas import ChatMessageFeedbackType
from app.core.base import Base
from app.core.config import timezone_vi
from app.schemas import Sender


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    is_favorite: Mapped[bool] = mapped_column(default=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone_vi)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(tz=timezone_vi),
        onupdate=lambda: datetime.now(tz=timezone_vi),
    )
    session_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)  # pyright: ignore[reportMissingTypeArgument]  # e.g., title, description, etc.
    chat_messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="chat_session", cascade="all, delete, delete-orphan"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True
    )
    sender: Mapped[Sender] = mapped_column(Enum(Sender))
    content: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone_vi)
    )
    chat_session: Mapped["ChatSession"] = relationship(
        back_populates="chat_messages"
    )


class ChatMessageFeedback(Base):
    __tablename__ = "chat_message_feedback"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    chat_message_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"), index=True
    )
    feedback: Mapped[ChatMessageFeedbackType] = mapped_column(
        Enum(ChatMessageFeedbackType)
    )
    detail: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(tz=timezone_vi)
    )
