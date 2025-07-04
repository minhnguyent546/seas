from fastapi import APIRouter

import app.users.service as user_service
from app.deps import AsyncSessionDep
from app.users.schemas import UserPublic

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=list[UserPublic])
async def get_users(
    session: AsyncSessionDep, offset: int = 0, limit: int = 100
):
    users = await user_service.get_users(
        session=session, offset=offset, limit=limit
    )
    return users
