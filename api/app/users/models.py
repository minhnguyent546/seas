import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base
from app.core.config import timezone_vi
from app.users.schemas import UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    username: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole), default=UserRole.USER
    )
    password: Mapped[str] = mapped_column(String())
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now(tz=timezone_vi)
    )

    def __repr__(self) -> str:
        return (
            f"<User(id={self.id!r}, username={self.username!r}, email={self.email!r}, "
            f"full_name={self.full_name!r}, role={self.role!r}, "
            f"is_active={self.is_active!r})>"
        )


if __name__ == "__main__":
    test_user = User(
        id=1,
        username="testuser",
        email="testuser@example.com",
        full_name="Test User",
        password="securepassword",
        role=UserRole.USER,
        is_active=True,
    )

    print(
        f"{
            select(
                User.username,
                User.email,
                func.count(User.is_active).label('num_active_users'),
            ).order_by(User.username.desc())
        }"
    )
    print(f"{User.username = }")
    print(f"{test_user = }")

    sub_query = select(User.id, User.username).where(User.is_active).subquery()
    print(f"{sub_query = }")
    result = select(sub_query.c.id, sub_query.c.username).order_by(
        sub_query.c.username
    )
    print(f"{result = }")
