from httpx import AsyncClient
from loguru import logger

from app.core.config import settings


async def get_superuser_token_headers(client: AsyncClient) -> dict[str, str]:
    form_data = {
        "username": settings.FIRST_USER_USERNAME,
        "password": settings.FIRST_USER_PASSWORD,
    }
    res = await client.post(
        f"{settings.API_PREFIX}/auth/login/access-token", data=form_data
    )
    json = res.json()
    logger.info(f"Login response: {json}")
    headers = {"Authorization": f"Bearer {json['access_token']}"}
    return headers
