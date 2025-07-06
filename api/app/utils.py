from datetime import datetime

from loguru import logger

from app.core.config import timezone_vi


def serialize_datetime(value: datetime) -> str:
    try:
        value = value.astimezone(timezone_vi).replace(tzinfo=timezone_vi)
    except Exception as e:
        logger.error(
            f"Error converting timezone to {timezone_vi}: {e}. Leaving as is."
        )
    return value.strftime("%Y-%m-%d - %H:%M:%S")
