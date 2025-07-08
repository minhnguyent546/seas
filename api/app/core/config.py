import secrets
from typing import Annotated, Any, Literal

import pytz
from pydantic import AnyUrl, BeforeValidator, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

timezone_vi = pytz.timezone("Asia/Ho_Chi_Minh")


def parse_cors_origins(origins: Any) -> list[str] | str:
    if isinstance(origins, str) and not origins.startswith("["):
        return [
            origin.strip() for origin in origins.split(",") if origin.strip()
        ]
    elif isinstance(origins, (list, str)):
        return origins
    raise ValueError(f"Failed to parse CORS origins: {origins}")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",  # parent directory
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True,
    )

    # project name
    PROJECT_NAME: str = "SEAS"

    # environment
    ENVIRONMENT: Literal["development", "production"] = "development"

    # frontend
    FRONTEND_HOST: str = "http://localhost:5173"

    # general
    API_PREFIX: str = "/api/v1"
    API_PORT: int = 8444

    # cors
    BACKEND_CORS_ORIGINS: Annotated[
        list[AnyUrl] | str, BeforeValidator(parse_cors_origins)
    ] = []

    @computed_field
    @property
    def CORS_ORIGINS(self) -> list[str]:
        if isinstance(self.BACKEND_CORS_ORIGINS, str):
            return [self.BACKEND_CORS_ORIGINS, self.FRONTEND_HOST]
        return [
            str(origin).rstrip("/")
            for origin in self.BACKEND_CORS_ORIGINS
            if origin
        ] + [self.FRONTEND_HOST]

    # jwt
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2 * 24 * 60  # 2 days

    # postgres
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "seas"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    FIRST_USER_USERNAME: str = "root"
    FIRST_USER_PASSWORD: str

    # email
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587  # default secure port for email submission
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str = "SEAS"
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48  # 48 hours
    EMAIL_TEST_USER: str = "testuser@test.com"

    @computed_field
    @property
    def emails_enabled(self) -> bool:
        return (
            self.SMTP_HOST is not None and self.EMAILS_FROM_EMAIL is not None
        )

    @computed_field
    @property
    def SQLALCHEMY_POSTGRES_URI(self) -> str:
        postgres_dsn = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )  # pyright: ignore[reportReturnType]
        return postgres_dsn.encoded_string()


settings = Settings()  # pyright: ignore[reportCallIssue]
