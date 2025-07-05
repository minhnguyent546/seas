import uuid
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, select

from app.auth.utils import hash_password, verify_password
from app.core.database import AsyncSession
from app.schemas import MessageResponse
from app.users.models import User
from app.users.schemas import (
    UpdatePassword,
    UserCreate,
    UserRole,
    UserUpdate,
    UserUpdateMe,
)


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


async def update_user_me(
    session: AsyncSession,
    user_update_me: UserUpdateMe,
    current_user: User,
) -> User:
    if user_update_me.email is not None:
        existing_user = await get_user_by_email(
            session=session, email=user_update_me.email
        )
        if existing_user is not None and existing_user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )
    user_data = user_update_me.model_dump(exclude_unset=True)
    current_user.email = user_data.get("email", current_user.email)
    current_user.full_name = user_data.get("full_name", current_user.full_name)
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user


async def update_my_password(
    session: AsyncSession,
    current_user: User,
    update_password: UpdatePassword,
) -> MessageResponse:
    if not verify_password(
        plain_password=update_password.current_password,
        hashed_password=current_user.password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )
    if update_password.current_password == update_password.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )
    current_user.hashed_password = hash_password(update_password.new_password)
    session.add(current_user)
    await session.commit()
    return MessageResponse(message='"Password updated successfully"')


async def delete_user_me(
    session: AsyncSession,
    current_user: User,
) -> MessageResponse:
    if current_user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser cannot delete themselves",
        )
    await session.delete(current_user)
    await session.commit()
    return MessageResponse(message='"User deleted successfully"')


async def update_user_by_id(
    user_id: uuid.UUID, session: AsyncSession, user_update: UserUpdate
) -> User:
    db_user = await get_user_by_id(session=session, user_id=str(user_id))
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user_update.email is not None:
        existing_user = await get_user_by_email(
            session=session, email=user_update.email
        )
        if existing_user is not None and existing_user.id != db_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )
    user_data = user_update.model_dump(exclude_unset=True)
    db_user.email = user_data.get("email", db_user.email)
    db_user.full_name = user_data.get("full_name", db_user.full_name)
    db_user.is_active = user_data.get("is_active", db_user.is_active)
    db_user.role = user_data.get("role", db_user.role)
    if "password" in user_data:
        db_user.password = hash_password(user_data["password"])
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def delete_user_by_id(
    user_id: uuid.UUID,
    session: AsyncSession,
    current_user: User,
) -> MessageResponse:
    db_user = await get_user_by_id(session=session, user_id=str(user_id))
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if db_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser cannot delete themselves",
        )
    await session.delete(db_user)
    await session.commit()
    return MessageResponse(message='"User deleted successfully"')


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
