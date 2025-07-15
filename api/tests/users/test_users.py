import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio(loop_scope="session")
async def test_get_user_me_superuser(
    client: AsyncClient, superuser_cookies: dict[str, str]
):
    res = await client.get(
        f"{settings.API_PREFIX}/users/me", cookies=superuser_cookies
    )
    assert res.status_code == 200, res.text
    user = res.json()
    assert user
    assert user["username"] == "root"
    assert user["email"] == "root@example.com"
    assert user["full_name"] == "root"
    assert user["is_active"] is True
    assert user["role"] == "ADMIN"
