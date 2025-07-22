from typing import Annotated

from fastapi import Depends
from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.users.service as user_service
from app.auth.utils import hash_password
from app.core.base import Base
from app.core.config import settings
from app.users.models import User
from app.users.schemas import UserCreate, UserRole

engine = create_async_engine(settings.SQLALCHEMY_POSTGRES_URI)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,  # pyright: ignore[reportArgumentType, reportCallIssue]
    class_=AsyncSession,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


async def init_db(session: AsyncSession):
    # tables should be created with alembic migrations
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    user = await user_service.get_user_by_username(
        session, settings.FIRST_USER_USERNAME
    )
    if user is None:
        logger.info(
            f"Creating first user with username: {settings.FIRST_USER_USERNAME}"
        )
        user_create = UserCreate(
            username=settings.FIRST_USER_USERNAME,
            email=settings.FIRST_USER_USERNAME + "@example.com",
            full_name="root",
            is_active=True,
            password=hash_password(settings.FIRST_USER_PASSWORD),
            role=UserRole.ADMIN,
        )
        user = User(**user_create.model_dump())
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("First user created")


async def get_async_session():
    async with AsyncSessionLocal() as async_session:  # pyright: ignore[reportGeneralTypeIssues]
        try:
            yield async_session
        except Exception:
            await async_session.rollback()
            raise
        finally:
            await async_session.close()

AsyncSessionDep = Annotated[AsyncSession, Depends(get_async_session)]
