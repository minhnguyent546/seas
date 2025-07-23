import uuid

from fastapi import APIRouter, Depends, HTTPException, status

import app.users.service as user_service
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
    updated_current_user = await user_service.update_user_me(
        session=session,
        user_update_me=user_update_me,
        current_user=current_user,
    )
    return updated_current_user


@router.patch("/me/password", response_model=MessageResponse)
async def update_my_password(
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
    update_password: UpdatePassword,
):
    """Update current user's password"""
    message = await user_service.update_my_password(
        session=session,
        current_user=current_user,
        update_password=update_password,
    )
    return message


@router.delete("/me", response_model=MessageResponse)
async def delete_user_me(
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Delete current user"""
    message = await user_service.delete_user_me(
        session=session, current_user=current_user
    )
    return message


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
    user = await user_service.update_user_by_id(
        user_id=user_id, session=session, user_update=user_update
    )
    return user


@router.delete(
    "/{user_id}",
    dependencies=[Depends(get_current_superuser)],
    response_model=MessageResponse,
)
async def delete_user_by_id(
    user_id: uuid.UUID,
    session: AsyncSessionDep,
    current_user: CurrentActiveUserDep,
):
    """Delete a user by ID. Requires superuser permissions."""
    message = await user_service.delete_user_by_id(
        user_id=user_id, session=session, current_user=current_user
    )
    return message
