import secrets
from typing import Annotated, Any, Literal, Self

import pytz
from pydantic import (
    AnyHttpUrl,
    AnyUrl,
    BeforeValidator,
    EmailStr,
    PostgresDsn,
    TypeAdapter,
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
    ENVIRONMENT: Literal["development", "staging", "production"] = (
        "development"
    )

    # frontend
    FRONTEND_HOST: str = "http://localhost:5173"

    # general
    API_PREFIX: str = "/api/v1"
    API_PORT: int = 8444

    # google oauth2
    GOOGLE_OAUTH2_CLIENT_ID: str
    GOOGLE_OAUTH2_CLIENT_SECRET: str
    GOOGLE_OAUTH2_USERINFO_URL: AnyHttpUrl = TypeAdapter(
        AnyHttpUrl
    ).validate_python("https://www.googleapis.com/oauth2/v3/userinfo")

    # github oauth2
    GITHUB_OAUTH2_CLIENT_ID: str
    GITHUB_OAUTH2_CLIENT_SECRET: str
    GITHUB_OAUTH2_USERINFO_URL: AnyHttpUrl = TypeAdapter(
        AnyHttpUrl
    ).validate_python("https://api.github.com/user")

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

    # llm
    CHAT_MODEL: str = "google/gemini-2.5-flash"
    TABLE_SUMMARY_MODEL: str = "openai/gpt-4o"
    GOOGLE_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # embeddings model
    BAAI_EMBEDDING_MODEL: str = "BAAI/bge-m3"

    CHUNK_SIZE: int = 2048
    CHUNK_OVERLAP: int = 256

    # query expansion
    QUERY_EXPANSION_MODEL: str = "google/gemini-2.5-flash"

    # reranking model
    BAAI_RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"

    # doc upload dir
    DOC_UPLOAD_DIR: str = "uploaded-docs"

    # qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_NAME: str = "seas_documents"
    QDRANT_VECTOR_SIZE: int = 1024  # embeddings dimension

    # config for adding document in batch
    BATCH_DOCUMENT_UPLOAD_MAX_BATCH_SIZE: int = 20
    BATCH_DOCUMENT_UPLOAD_MAX_TOTAL_CHUNKS: int = 5_000

    # openrouter
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_API_KEY: str = ""

    # Hugging Face stuff
    PRELOAD_HF_MODELS: bool = False
    HF_HOME: str = "/app/.hf_models"

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

    @property
    def cookie_common_options(self) -> dict[str, Any]:
        return {
            "path": "/",
            "secure": False,  # TODO: should be set to True in production
            "httponly": True,
            "samesite": "lax",
        }


settings = Settings()  # pyright: ignore[reportCallIssue]
