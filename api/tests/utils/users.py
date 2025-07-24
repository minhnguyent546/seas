from httpx import AsyncClient

from app.core.config import settings
from app.core.logger import logger


async def get_superuser_cookies(client: AsyncClient) -> dict[str, str]:
    form_data = {
        "username": settings.FIRST_USER_USERNAME,
        "password": settings.FIRST_USER_PASSWORD,
    }
    res = await client.post(
        f"{settings.API_PREFIX}/auth/login", data=form_data
    )
    logger.info(f"Login response status: {res.status_code}")
    return dict(res.cookies)
