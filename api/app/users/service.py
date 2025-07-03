from typing import Sequence

from sqlalchemy import select

from app.core.database import AsyncSession
from app.users.models import User


async def get_user_by_id(
    session: AsyncSession,
    user_id: int,
) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalars().first()


async def get_users(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 100,
) -> Sequence[User]:
    result = await session.execute(select(User).offset(offset).limit(limit))
    return result.scalars().all()
