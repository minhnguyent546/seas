import platform
import time
from datetime import datetime

import psutil
from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import text

from app.core.config import settings, timezone_vi
from app.core.database import AsyncSessionLocal
from app.utils import serialize_datetime


async def check_health(start_time: float):
    try:
        # Test database connectivity
        async with AsyncSessionLocal() as session:  # pyright: ignore[reportGeneralTypeIssues]
            # environment
            environment = getattr(settings, "ENVIRONMENT", "development")

            # Calculate uptime
            uptime_seconds = time.time() - start_time
            days, remainder = divmod(int(uptime_seconds), 24 * 60 * 60)
            hours, remainder = divmod(remainder, 60 * 60)
            minutes, seconds = divmod(remainder, 60)
            uptime = f"{days}d {hours}h {minutes}m {seconds}s"

            # Get system info
            memory = psutil.virtual_memory()

            health_check_data = {
                "status": "ok",
                "datetime": serialize_datetime(datetime.now(tz=timezone_vi)),
                "api_version": getattr(settings, "API_VERSION", "1.0.0"),
                "uptime": uptime,
                "system": {
                    "cpu_usage": f"{psutil.cpu_percent()}%",
                    "memory_usage": f"{memory.percent}%",
                    "platform": platform.platform(),
                    "python": platform.python_version(),
                },
            }

            if environment == "development":
                # Get database version
                db_version_result = await session.execute(
                    text("SELECT version()")
                )
                db_version = db_version_result.scalar()
                health_check_data["database"] = {
                    "connected": True,
                    "version": db_version,
                }

                # Total memory
                health_check_data["system"]["memory_total"] = (  # pyright: ignore[reportIndexIssue]
                    f"{psutil.virtual_memory().total / (1024**3):.2f} GiB"
                )

            return health_check_data
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "message": "Unable to connect to the database",
                "error": str(e),
            },
        ) from e
