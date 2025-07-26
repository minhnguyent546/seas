from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",  # parent directory
        env_ignore_empty=True,
        extra="ignore",
        case_sensitive=True,
    )

    # FastMCP configs
    FASTMCP_PORT: int = 8666

settings = Settings()  # pyright: ignore[reportCallIssue]

