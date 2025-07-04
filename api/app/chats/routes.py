from fastapi import APIRouter

from app.deps import (
    AsyncSessionDep,
    CurrentActiveUserDep,
)

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("/")
async def get_chats(
    session: AsyncSessionDep, current_user: CurrentActiveUserDep
):
    return {"chats": "ok"}
