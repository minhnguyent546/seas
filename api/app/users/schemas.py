import enum
from datetime import datetime
from typing import Annotated

from loguru import logger
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from app.core.config import timezone_vi


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    full_name: Annotated[str, Field(min_length=3, max_length=100)]
    is_active: bool = True
    password: Annotated[str, Field(min_length=6, max_length=128)]
    role: UserRole = UserRole.USER


class UserRegister(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    full_name: Annotated[str, Field(min_length=3, max_length=100)]
    password: Annotated[str, Field(min_length=6, max_length=128)]


class UserLogin(BaseModel):
    username: Annotated[str, Field(min_length=3, max_length=50)]
    password: Annotated[str, Field(min_length=6, max_length=128)]


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: Annotated[str | None, Field(min_length=3, max_length=100)] = (
        None
    )
    is_active: bool | None = None
    role: UserRole | None = None
    password: Annotated[str | None, Field(min_length=6, max_length=128)] = None


class UserUpdateMe(BaseModel):
    email: EmailStr | None = None
    full_name: Annotated[str | None, Field(min_length=3, max_length=100)] = (
        None
    )


class UpdatePassword(BaseModel):
    current_password: Annotated[str, Field(min_length=6, max_length=128)]
    new_password: Annotated[str, Field(min_length=6, max_length=128)]


class UserPublic(BaseModel):
    id: str
    username: Annotated[str, Field(min_length=3, max_length=50)]
    email: EmailStr
    full_name: Annotated[str, Field(min_length=3, max_length=100)]
    is_active: bool
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime, _info):
        try:
            value = value.astimezone(timezone_vi).replace(tzinfo=timezone_vi)
        except Exception as e:
            logger.error(
                f"Error converting timezone to {timezone_vi}: {e}. Leaving as is."
            )

        return value.strftime("%Y-%m-%d - %H:%M:%S")


class UserPublicList(BaseModel):
    users: list[UserPublic]
    count: int  # total number of users in the database
