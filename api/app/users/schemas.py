import enum
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


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
