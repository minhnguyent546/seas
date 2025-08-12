import uuid

from fastapi import APIRouter, HTTPException, status

import app.chats.service as chats_service
from app.chats.schemas import (
    ChatMessageCreate,
    ChatMessagePublic,
    ChatSessionCreate,
    ChatSessionPublic,
    ChatSessionUpdate,
)
from app.deps import (
    AsyncSessionDep,
    CurrentActiveUserDep,
)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/chat_sessions", response_model=list[ChatSessionPublic])
async def get_chat_sessions(
    session: AsyncSessionDep, current_user: CurrentActiveUserDep
):
    """
    Get all chat sessions for the current user.
    """
    chat_sessions = await chats_service.get_chat_sessions_by_user_id(
        session=session, user_id=str(current_user.id)
    )

    return chat_sessions


@router.post(
    "/chat_sessions",
    response_model=ChatSessionPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_session(
    session: AsyncSessionDep,
    chat_session_create: ChatSessionCreate,
    current_user: CurrentActiveUserDep,
):
    """
    Create a new chat session for the current user.
    """
    chat_session = await chats_service.create_chat_session(
        session=session,
        chat_session_create=chat_session_create,
        current_user=current_user,
    )
    return chat_session


@router.get(
    "/chat_sessions/latest-chat-session", response_model=ChatSessionPublic
)
async def get_latest_chat_session(
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """
    Get the latest chat session for the current user.
    """
    chat_session = await chats_service.get_latest_chat_session(
        session=session, user_id=str(current_user.id)
    )
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No chat session found",
        )
    return chat_session


@router.get(
    "/chat_sessions/{chat_session_id}", response_model=ChatSessionPublic
)
async def get_chat_session(
    chat_session_id: uuid.UUID,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """
    Get a specific chat session by ID for the current user.
    """
    chat_session = await chats_service.get_chat_session_by_id(
        session=session, chat_session_id=str(chat_session_id)
    )
    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found",
        )
    if chat_session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this chat session",
        )
    return chat_session


@router.patch(
    "/chat_sessions/{chat_session_id}", response_model=ChatSessionPublic
)
async def update_chat_session(
    chat_session_id: uuid.UUID,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
    chat_session_update: ChatSessionUpdate,
):
    """Update a chat session by ID."""
    chat_session = await chats_service.update_chat_session(
        session=session,
        chat_session_id=str(chat_session_id),
        chat_session_update=chat_session_update,
        current_user=current_user,
    )
    return chat_session


@router.get("/chat_sessions/{chat_session_id}/messages")
async def get_chat_messages(
    chat_session_id: uuid.UUID,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Get chat messages for a specific session."""
    chat_messages = await chats_service.get_chat_messages_by_chat_session_id(
        session=session,
        chat_session_id=str(chat_session_id),
        user_id=str(current_user.id),
    )
    return chat_messages


@router.post(
    "/chat_sessions/{chat_session_id}/messages",
    response_model=ChatMessagePublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_new_message(
    chat_session_id: uuid.UUID,
    chat_message_create: ChatMessageCreate,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Create a new message in a chat session."""
    chat_message = await chats_service.create_new_message(
        session=session,
        chat_session_id=str(chat_session_id),
        chat_message_create=chat_message_create,
        user_id=str(current_user.id),
    )
    return chat_message
