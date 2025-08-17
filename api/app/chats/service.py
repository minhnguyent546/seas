from datetime import datetime
from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import load_only, selectinload

from app.chats.models import ChatMessage, ChatMessageFeedback, ChatSession
from app.chats.schemas import (
    ChatMessageCreate,
    ChatMessageFeedbackCreate,
    ChatSessionCreate,
    ChatSessionUpdate,
)
from app.core.config import timezone_vi
from app.core.database import AsyncSession
from app.schemas import MessageResponse, Sender
from app.users.models import User
from app.users.schemas import UserRole


async def get_chat_session_by_id(
    session: AsyncSession,
    chat_session_id: str,
    current_user: User | None = None,
) -> ChatSession | None:
    chat_session_result = await session.execute(
        select(ChatSession).where(ChatSession.id == chat_session_id)
    )
    chat_session = chat_session_result.scalars().first()

    if current_user is not None and chat_session is not None:
        if (
            current_user.role != UserRole.ADMIN
            and chat_session.user_id != current_user.id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this chat session.",
            )

    return chat_session


async def get_chat_sessions_by_user_id(
    session: AsyncSession,
    user_id: str,
    offset: int = 0,
    limit: int = 50,
    sort_by: Literal["created_at", "updated_at"] | None = None,
    sort_order: Literal["asc", "desc"] = "desc",
) -> list[ChatSession]:
    statement = select(ChatSession).where(ChatSession.user_id == user_id)
    if sort_by is not None:
        sort_field = getattr(ChatSession, sort_by, None)
        if sort_field is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sort_by value.",
            )
        if sort_order == "asc":
            statement = statement.order_by(sort_field)
        else:
            statement = statement.order_by(sort_field.desc())

    statement = statement.offset(offset).limit(limit)
    chat_sessions_result = await session.execute(statement)
    chat_sessions = chat_sessions_result.scalars().all()
    return list(chat_sessions)


async def get_latest_chat_session(
    session: AsyncSession, user_id: str
) -> ChatSession | None:
    chat_sessions_result = await session.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at.desc())
        .limit(1)
    )
    chat_session = chat_sessions_result.scalar_one_or_none()
    return chat_session


async def create_chat_session(
    session: AsyncSession,
    chat_session_create: ChatSessionCreate,
    current_user: User,
) -> ChatSession:
    chat_session = ChatSession(
        user_id=current_user.id,
        **chat_session_create.model_dump(),
    )
    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)
    return chat_session


async def update_chat_session(
    session: AsyncSession,
    chat_session_id: str,
    chat_session_update: ChatSessionUpdate,
    current_user: User,
) -> ChatSession:
    chat_session_result = await session.execute(
        select(ChatSession).where(ChatSession.id == chat_session_id)
    )
    chat_session = chat_session_result.scalars().first()
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )
    if (
        current_user.role != UserRole.ADMIN
        and chat_session.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this chat session.",
        )
    chat_session_data = chat_session_update.model_dump(exclude_unset=True)
    chat_session.is_favorite = chat_session_data.get(
        "is_favorite", chat_session.is_favorite
    )
    if "session_metadata" in chat_session_data:
        # Create a new dictionary to ensure SQLAlchemy detects the change
        new_session_metadata = chat_session.session_metadata.copy()
        new_session_metadata.update(chat_session_data["session_metadata"])
        chat_session.session_metadata = new_session_metadata

    session.add(chat_session)
    await session.commit()
    await session.refresh(chat_session)
    return chat_session


async def delete_chat_session(
    session: AsyncSession,
    chat_session_id: str,
    current_user: User,
) -> MessageResponse:
    chat_session_result = await session.execute(
        select(ChatSession).where(ChatSession.id == chat_session_id)
    )
    chat_session = chat_session_result.scalars().first()
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )
    if (
        current_user.role != UserRole.ADMIN
        and chat_session.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this chat session.",
        )

    await session.delete(chat_session)
    await session.commit()
    return MessageResponse(message="Chat session deleted successfully")


async def get_chat_messages_by_chat_session_id(
    session: AsyncSession,
    chat_session_id: str,
    current_user: User,
) -> list[ChatMessage]:
    chat_session_result = await session.execute(
        select(ChatSession)
        .where(ChatSession.id == chat_session_id)
        .options(load_only(ChatSession.id, ChatSession.user_id))
    )
    chat_session = chat_session_result.scalars().first()
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )
    if (
        current_user.role != UserRole.ADMIN
        and chat_session.user_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat session.",
        )
    chat_messages_result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_session_id == chat_session_id)
        .order_by(ChatMessage.created_at)
        .options(selectinload(ChatMessage.chat_message_feedback))
    )
    chat_messages = chat_messages_result.scalars().all()
    return list(chat_messages)


async def create_new_message(
    session: AsyncSession,
    chat_session_id: str,
    chat_message_create: ChatMessageCreate,
    user_id: str,
) -> ChatMessage:
    chat_session_result = await session.execute(
        select(ChatSession)
        .where(ChatSession.id == chat_session_id)
        .options(
            load_only(
                ChatSession.id, ChatSession.user_id, ChatSession.updated_at
            )
        )
    )
    chat_session = chat_session_result.scalars().first()
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )
    if chat_session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat session.",
        )
    message_created_at = datetime.now(tz=timezone_vi)
    chat_message = ChatMessage(
        **chat_message_create.model_dump(),
        chat_session_id=chat_session_id,
        created_at=message_created_at,
    )
    chat_session.updated_at = message_created_at
    session.add(chat_message)
    await session.commit()
    await session.refresh(chat_message)
    return chat_message


async def create_message_feedback(
    session: AsyncSession,
    chat_message_feedback_create: ChatMessageFeedbackCreate,
    current_user: User,
) -> ChatMessageFeedback:
    chat_message_result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.id == chat_message_feedback_create.chat_message_id)
        .options(
            selectinload(ChatMessage.chat_session),
            load_only(
                ChatMessage.id,
                ChatMessage.chat_session_id,
                ChatMessage.sender,
            ),
        )
    )
    chat_message = chat_message_result.scalars().first()
    if chat_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat message not found.",
        )
    if chat_message.sender != Sender.BOT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only bot messages can be feedbacked.",
        )

    chat_session = chat_message.chat_session
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat session.",
        )

    existing_feedback_result = await session.execute(
        select(ChatMessageFeedback).where(
            ChatMessageFeedback.chat_message_id == chat_message.id,
        )
    )
    existing_feedback = existing_feedback_result.scalars().first()
    if existing_feedback is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feedback already exists",
        )

    message_feedback = ChatMessageFeedback(
        **chat_message_feedback_create.model_dump()
    )
    session.add(message_feedback)
    await session.commit()
    await session.refresh(message_feedback)
    return message_feedback
