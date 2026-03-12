"""Logging configuration for GlobKurier MCP Server.

This module sets up structured logging with:
- Console output (always enabled)
- Optional file output with rotation
- Configurable log levels
- Request/response logging capability
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from globkurier_mcp.config.settings import Settings


def setup_logging(settings: Settings) -> None:
    """Configure application-wide logging.

    Args:
        settings: Application settings containing logging configuration

    Sets up:
        - Root logger with configured level
        - Console handler (stdout)
        - File handler with rotation (if log_file_path is set)
        - Formatting for all handlers
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(settings.log_format)

    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if settings.log_file_path:
        log_file = Path(settings.log_file_path)

        # Create parent directories if they don't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=settings.log_file_max_bytes,
            backupCount=settings.log_file_backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(settings.log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        root_logger.info(
            f"File logging enabled: {log_file} "
            f"(max {settings.log_file_max_bytes} bytes, "
            f"{settings.log_file_backup_count} backups)"
        )

    # Log startup
    root_logger.info(
        f"Logging initialized: level={settings.log_level}, "
        f"file={'enabled' if settings.log_file_path else 'disabled'}"
    )

    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastmcp").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
