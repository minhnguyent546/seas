from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import load_only

from app.chats.models import ChatMessage, ChatSession
from app.chats.schemas import (
    ChatMessageCreate,
    ChatSessionCreate,
)
from app.core.config import timezone_vi
from app.core.database import AsyncSession
from app.users.models import User


async def get_chat_session_by_id(
    session: AsyncSession,
    chat_session_id: str,
) -> ChatSession | None:
    chat_session_result = await session.execute(
        select(ChatSession).where(ChatSession.id == chat_session_id)
    )
    chat_session = chat_session_result.scalars().first()
    return chat_session


async def get_chat_sessions_by_user_id(
    session: AsyncSession, user_id: str
) -> list[ChatSession]:
    chat_sessions_result = await session.execute(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.created_at)
    )
    chat_sessions = chat_sessions_result.scalars().all()
    return list(chat_sessions)


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


async def get_chat_messages_by_chat_session_id(
    session: AsyncSession,
    chat_session_id: str,
    user_id: str | None = None,
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
    if user_id is not None and chat_session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat session.",
        )
    chat_messages_result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_session_id == chat_session_id)
        .order_by(ChatMessage.created_at)
    )
    chat_messages = chat_messages_result.scalars().all()
    return list(chat_messages)


async def create_new_message(
    session: AsyncSession,
    chat_session_id: str,
    chat_message_create: ChatMessageCreate,
    user_id: str | None = None,
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
    if user_id is not None and chat_session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat session.",
        )
    message_created_at = datetime.now(tz=timezone_vi)
    chat_message = ChatMessage(
        **chat_message_create.model_dump(),
        chat_session_id=chat_session_id,
        created_at=datetime.now(tz=timezone_vi),
    )
    session.add(chat_message)
    chat_session.updated_at = message_created_at
    await session.commit()
    await session.refresh(chat_message)
    return chat_message
