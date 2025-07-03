import secrets

import pytz
from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

timezone_vi = pytz.timezone("Asia/Ho_Chi_Minh")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",  # parent directory
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True,
    )

    # general
    API_PREFIX: str = "/api/v1"
    API_PORT: int = 8444

    # cors
    CORS_ORIGINS: list[str] = ["http://localhost:8444"]

    # jwt
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 2 * 24 * 60  # 2 days

    # postgres
    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    FIRST_USER_USERNAME: str = "root"
    FIRST_USER_PASSWORD: str

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
