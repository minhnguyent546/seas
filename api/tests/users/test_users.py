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


@pytest.mark.asyncio(loop_scope="session")
async def test_update_my_password(
    client: AsyncClient, superuser_cookies: dict[str, str]
):
    old_password = settings.FIRST_USER_PASSWORD
    new_password = f"{old_password}-new"
    res = await client.patch(
        f"{settings.API_PREFIX}/users/me/password",
        json={"current_password": old_password, "new_password": new_password},
        cookies=superuser_cookies,
    )
    assert res.status_code == 200, res.text
    try:
        old_login = await client.post(
            f"{settings.API_PREFIX}/auth/login",
            data={
                "username": settings.FIRST_USER_USERNAME,
                "password": old_password,
            },
        )
        assert old_login.status_code != 200, old_login.text

        new_login = await client.post(
            f"{settings.API_PREFIX}/auth/login",
            data={
                "username": settings.FIRST_USER_USERNAME,
                "password": new_password,
            },
        )
        assert new_login.status_code == 200, new_login.text
    finally:
        await client.patch(
            f"{settings.API_PREFIX}/users/me/password",
            json={
                "current_password": new_password,
                "new_password": old_password,
            },
            cookies=superuser_cookies,
        )
