import uuid

from fastapi import APIRouter, Depends, HTTPException, status

import app.users.service as user_service
from app.auth.utils import hash_password, verify_password
from app.deps import (
    AsyncSessionDep,
    CurrentActiveUserDep,
    get_current_superuser,
)
from app.schemas import MessageResponse
from app.users.schemas import (
    UpdatePassword,
    UserCreate,
    UserPublic,
    UserPublicList,
    UserRole,
    UserUpdate,
    UserUpdateMe,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    dependencies=[Depends(get_current_superuser)],
    response_model=UserPublicList,
)
async def get_users(
    session: AsyncSessionDep, offset: int = 0, limit: int = 100
):
    """Get users. Requires superuser permissions."""
    users = await user_service.get_users(
        session=session, offset=offset, limit=limit
    )
    users_count = await user_service.count_users(session=session)
    return UserPublicList(
        users=list(users),
        count=users_count,
    )


@router.post(
    "/",
    dependencies=[Depends(get_current_superuser)],
    response_model=UserPublic,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(session: AsyncSessionDep, user_create: UserCreate):
    """Create a new user. Requires superuser permissions."""
    db_user = await user_service.create_user(
        session=session, user_create=user_create
    )
    # TODO: we might want to setup an email and send a email here
    return db_user


@router.get("/me", response_model=UserPublic)
async def get_user_me(
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Get current user"""
    return current_user


@router.patch("/me", response_model=UserPublic)
async def update_user_me(
    session: AsyncSessionDep,
    user_update_me: UserUpdateMe,
    current_user: CurrentActiveUserDep,
):
    """Update current user's information"""
    if user_update_me.email is not None:
        existing_user = await user_service.get_user_by_email(
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


@router.patch("/me/password", response_model=MessageResponse)
async def update_my_password(
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
    update_password: UpdatePassword,
):
    """Update current user's password"""
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


@router.delete("/me", response_model=MessageResponse)
async def delete_user_me(
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Delete current user"""
    if current_user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser cannot delete themselves",
        )
    await session.delete(current_user)
    await session.commit()
    return MessageResponse(message='"User deleted successfully"')


@router.get("/{user_id}", response_model=UserPublic)
async def get_user_by_id(
    user_id: uuid.UUID,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Get user by ID"""
    user = await user_service.get_user_by_id(
        session=session, user_id=str(user_id)
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user.id == current_user.id:
        return current_user
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Should be a superuser/admin",
        )
    return user


@router.patch(
    "/{user_id}",
    dependencies=[Depends(get_current_superuser)],
    response_model=UserPublic,
)
async def update_user_by_id(
    user_id: uuid.UUID, session: AsyncSessionDep, user_update: UserUpdate
):
    """Update a user by ID. Requires superuser permissions."""
    db_user = await user_service.get_user_by_id(
        session=session, user_id=str(user_id)
    )
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    if user_update.email is not None:
        existing_user = await user_service.get_user_by_email(
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


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user_by_id(
    user_id: uuid.UUID,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Delete a user by ID. Requires superuser permissions."""
    db_user = await user_service.get_user_by_id(
        session=session, user_id=str(user_id)
    )
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
