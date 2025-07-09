import secrets
from typing import Annotated, Any, Literal, Self

import pytz
from pydantic import (
    AnyUrl,
    BeforeValidator,
    EmailStr,
    PostgresDsn,
    computed_field,
    model_validator,
)
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
    SENDER_ADDRESS: str = "HCMC, Vietnam"

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
    EMAILS_FROM_EMAIL: EmailStr | None = None
    EMAILS_FROM_NAME: EmailStr | None = None
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 24  # 24 hours
    EMAIL_TEST_USER: str = "testuser@test.com"

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if self.EMAILS_FROM_NAME is None:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME  # pyright: ignore[reportConstantRedefinition]
        return self

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

    @computed_field
    @property
    def smtp_options(self) -> dict[str, Any]:
        if not self.emails_enabled:
            raise RuntimeError(
                "Email environment variables are not configured."
            )

        options = {
            "host": self.SMTP_HOST,
            "port": self.SMTP_PORT,
        }
        if self.SMTP_TLS:
            options["tls"] = True
        elif self.SMTP_SSL:
            options["ssl"] = True

        if self.SMTP_USER is not None:
            options["user"] = self.SMTP_USER
        if self.SMTP_PASSWORD is not None:
            options["password"] = self.SMTP_PASSWORD

        return options


settings = Settings()  # pyright: ignore[reportCallIssue]
