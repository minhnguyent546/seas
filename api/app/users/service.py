from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, select

from app.auth.utils import hash_password
from app.core.database import AsyncSession
from app.users.models import User
from app.users.schemas import UserCreate


async def get_user_by_id(
    session: AsyncSession,
    user_id: str,
) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_username(
    session: AsyncSession,
    username: str,
) -> User | None:
    result = await session.execute(
        select(User).where(User.username == username)
    )
    return result.scalars().first()


async def get_user_by_email(
    session: AsyncSession,
    email: str,
) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def get_users(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 100,
) -> Sequence[User]:
    result = await session.execute(select(User).offset(offset).limit(limit))
    return result.scalars().all()


async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(User))
    return result.scalar_one()


async def create_user(session: AsyncSession, user_create: UserCreate) -> User:
    db_user = await get_user_by_username(
        session=session, username=user_create.username
    )
    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    db_user = await get_user_by_email(session=session, email=user_create.email)
    if db_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists",
        )
    user_create.password = hash_password(user_create.password)
    user = User(
        **user_create.model_dump(),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
