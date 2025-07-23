from authlib.integrations.starlette_client import OAuth

from app.core.config import settings

oauth_client = OAuth()

oauth_client.register(
    name="github",
    client_id=settings.GITHUB_OAUTH2_CLIENT_ID,
    client_secret=settings.GITHUB_OAUTH2_CLIENT_SECRET,
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    client_kwargs={
        "scope": "read:user user:email",  # Request read-only user profile and email
    },
)

oauth_client.register(
    name="google",
    client_id=settings.GOOGLE_OAUTH2_CLIENT_ID,
    client_secret=settings.GOOGLE_OAUTH2_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid profile email",
    },
)
