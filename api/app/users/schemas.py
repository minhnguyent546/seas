import enum
from datetime import datetime

from loguru import logger
from pydantic import BaseModel, ConfigDict, EmailStr, field_serializer

from app.core.config import timezone_vi


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    is_active: bool = True
    password: str
    role: UserRole = UserRole.USER


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    full_name: str
    is_active: bool
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime, _info):
        try:
            value = value.astimezone(timezone_vi).replace(tzinfo=timezone_vi)
        except Exception as e:
            logger.error(f"Error converting timezone to {timezone_vi}: {e}. Leaving as is.")

        return value.strftime("%Y-%m-%d - %H:%M:%S")
