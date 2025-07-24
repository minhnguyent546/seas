"""
Enhanced logger setup with rotation, retention, and advanced features.

Use this logger with:

```python
from app.core.logger import logger, init_logger

# Basic usage
init_logger()

# Advanced usage with custom configuration
init_logger(
    level="INFO",
    log_file="app.log",
    rotate_size="100 MB",
    retention="7 days",
    compression="gz",
    json_format=False,
    enable_backtrace=True
)

logger.info("This is an info message")
logger.error("This is an error message")
```
"""

import sys
from pathlib import Path

from loguru import logger


def init_logger(
    level: str = "DEBUG",
    log_file: str | None = None,
    log_dir: str = "logs",
    compact: bool = False,
    json_format: bool = False,
    rotate_size: str | int = "50 MB",
    rotate_time: str | None = None,
    retention: str | int = "30 days",
    compression: str | None = "gz",
    enable_backtrace: bool = True,
    enable_diagnose: bool = True,
    catch_exceptions: bool = True,
    enqueue: bool = True,
) -> None:
    """
    Initialize the logger.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Name of the log file (optional)
        log_dir: Directory to store log files
        compact: Use compact format (module:line instead of name:function:line)
        json_format: Use JSON format for structured logging
        rotate_size: Rotate when file reaches this size (e.g., "50 MB", "100 KB")
        rotate_time: Rotate based on time (e.g., "1 day", "1 week", "midnight")
        retention: How long to keep old log files (e.g., "30 days", 10)
        compression: Compression format for old logs ("gz", "bz2", "xz", or None)
        enable_backtrace: Include backtrace in error logs
        enable_diagnose: Include variable values in tracebacks
        catch_exceptions: Catch and log unhandled exceptions
        enqueue: Use multiprocessing-safe logging
    """

    # Remove default handler
    logger.remove()

    # Initialize paths
    log_path = Path(log_dir)
    full_log_path = None

    # Create log directory if it doesn't exist
    if log_file:
        log_path.mkdir(exist_ok=True)
        full_log_path = log_path / log_file

    # Determine format based on options
    if json_format:
        console_format = _get_json_format()
        file_format = _get_json_format()
    else:
        console_format = _get_text_format(compact=compact, colored=True)
        file_format = _get_text_format(compact=compact, colored=False)

    # Add console handler
    logger.add(
        sys.stdout,
        format=console_format,
        level=level,
        backtrace=enable_backtrace,
        diagnose=enable_diagnose,
        enqueue=enqueue,
        colorize=not json_format,
    )

    # Add file handler if specified
    if log_file and full_log_path:
        # Determine rotation config - prioritize time over size if both specified
        rotation_config = rotate_time if rotate_time else rotate_size

        logger.add(
            str(full_log_path),
            format=file_format,
            level="DEBUG",  # Always log everything to file
            rotation=rotation_config,
            retention=retention,
            compression=compression,
            backtrace=enable_backtrace,
            diagnose=enable_diagnose,
            enqueue=enqueue,
            serialize=json_format,
        )

        # Add error-specific log file
        error_log_path = log_path / f"error_{log_file}"
        logger.add(
            str(error_log_path),
            format=file_format,
            level="ERROR",
            rotation=rotate_size,
            retention=retention,
            compression=compression,
            backtrace=enable_backtrace,
            diagnose=enable_diagnose,
            enqueue=enqueue,
            serialize=json_format,
            filter=lambda record: record["level"].name
            in ["ERROR", "CRITICAL"],
        )

    # Catch unhandled exceptions
    if catch_exceptions:
        logger.catch(message="An unhandled exception occurred:")

    # Log initialization
    logger.info(
        "Logger initialized",
        extra={
            "level": level,
            "log_file": str(full_log_path) if full_log_path else None,
            "rotation": rotate_time if rotate_time else rotate_size,
            "retention": retention,
            "compression": compression,
        },
    )


def _get_text_format(compact: bool = False, colored: bool = True) -> str:
    """Get text format string for logging."""
    if colored:
        if compact:
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{module}:{line}</cyan> - "
                "<level>{message}</level>"
            )
        else:
            return (
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}:{function}:{line}</cyan> - "
                "<level>{message}</level>"
            )
    else:
        if compact:
            return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {module}:{line} - {message}"
        else:
            return "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"


def _get_json_format() -> str:
    """Get JSON format string for structured logging."""
    return "{time} {level} {name} {function} {line} {message}"
