import uuid

import pytest
from fastapi import status
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio(loop_scope="session")
async def test_chat_session_and_chat_messages(
    client: AsyncClient, superuser_token_headers: dict[str, str]
):
    # test creating a chat session
    create_res = await client.post(
        f"{settings.API_PREFIX}/chats/chat_sessions",
        headers=superuser_token_headers,
        json={
            "session_metadata": {
                "title": "Test Get Chat Sessions",
                "description": "This is a test for getting chat sessions.",
            },
        },
    )
    assert create_res.status_code == status.HTTP_201_CREATED, create_res.text
    created_session = create_res.json()
    created_session_id = created_session["id"]

    # test retrieving all chat sessions
    get_res = await client.get(
        f"{settings.API_PREFIX}/chats/chat_sessions",
        headers=superuser_token_headers,
    )
    assert get_res.status_code == status.HTTP_200_OK, get_res.text

    # Verify the response
    chat_sessions = get_res.json()
    assert isinstance(chat_sessions, list), (
        "Response should be a list of chat sessions"
    )
    assert len(chat_sessions) > 0, "Chat sessions list should not be empty"

    # Verify that the created session is in the response
    session_ids = [session["id"] for session in chat_sessions]
    assert created_session_id in session_ids, (
        "Created session should be in the response"
    )

    # Find the created session in the response and verify its metadata
    created_session_in_response = next(
        (
            session
            for session in chat_sessions
            if session["id"] == created_session_id
        ),
        None,
    )
    assert created_session_in_response is not None, (
        "Created session should be found in the response"
    )
    assert (
        created_session_in_response["session_metadata"]["title"]
        == "Test Get Chat Sessions"
    )
    assert (
        created_session_in_response["session_metadata"]["description"]
        == "This is a test for getting chat sessions."
    )

    # test creating chat messages
    create_message_res = await client.post(
        f"{settings.API_PREFIX}/chats/chat_sessions/{created_session_id}/messages",
        headers=superuser_token_headers,
        json={
            "content": "This is a test message.",
            "sender": "USER",
        },
    )
    assert create_message_res.status_code == status.HTTP_201_CREATED, (
        create_message_res.text
    )
    user_chat_message = create_message_res.json()
    assert user_chat_message["chat_session_id"] == created_session_id
    assert user_chat_message["content"] == "This is a test message."
    assert user_chat_message["sender"] == "USER"

    create_message_res = await client.post(
        f"{settings.API_PREFIX}/chats/chat_sessions/{created_session_id}/messages",
        headers=superuser_token_headers,
        json={
            "content": "This is a response from the CHATBOT.",
            "sender": "BOT",
        },
    )
    assert create_message_res.status_code == status.HTTP_201_CREATED, (
        create_message_res.text
    )
    bot_chat_message = create_message_res.json()
    assert bot_chat_message["chat_session_id"] == created_session_id
    assert (
        bot_chat_message["content"] == "This is a response from the CHATBOT."
    )
    assert bot_chat_message["sender"] == "BOT"

    # get chat messages
    get_messages_res = await client.get(
        f"{settings.API_PREFIX}/chats/chat_sessions/{created_session_id}/messages",
        headers=superuser_token_headers,
    )
    assert get_messages_res.status_code == status.HTTP_200_OK, (
        get_messages_res.text
    )
    chat_messages = get_messages_res.json()
    assert isinstance(chat_messages, list), (
        "Response should be a list of chat messages"
    )
    assert len(chat_messages) == 2, "There should be two chat messages"
    assert chat_messages[0]["id"] == user_chat_message["id"]
    assert chat_messages[1]["id"] == bot_chat_message["id"]


@pytest.mark.asyncio(loop_scope="session")
async def test_get_chat_session_not_found(
    client: AsyncClient, superuser_token_headers: dict[str, str]
):
    # Attempt to retrieve a non-existent chat session
    non_existent_session_id = uuid.uuid4()
    res = await client.get(
        f"{settings.API_PREFIX}/chats/chat_sessions/{non_existent_session_id}",
        headers=superuser_token_headers,
    )

    assert res.status_code == status.HTTP_404_NOT_FOUND, res.text
    json_data = res.json()
    assert json_data["detail"] == "Chat session not found"
