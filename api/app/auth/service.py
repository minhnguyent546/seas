import app.users.service as user_service
from app.auth.utils import verify_password
from app.core.database import AsyncSession
from app.users.models import User


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> User | None:
    db_user = await user_service.get_user_by_username(
        session=session, username=username
    )
    if db_user is None:
        return None
    if not verify_password(
        plain_password=password, hashed_password=db_user.password
    ):
        return None
    return db_user
