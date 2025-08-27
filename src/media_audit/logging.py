"""Logging configuration for media-audit."""

from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


def setup_logger(
    name: str = "media_audit",
    level: int = logging.INFO,
    log_file: Path | None = None,
    console_output: bool = True,
) -> Logger:
    """Set up a logger with rich formatting and optional file output.

    Args:
        name: Logger name
        level: Logging level
        log_file: Optional file path for log output
        console_output: Whether to output to console

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler with rich formatting
    if console_output:
        console = Console(stderr=True)
        console_handler = RichHandler(
            console=console,
            show_time=False,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
            tracebacks_show_locals=False,
        )
        console_handler.setLevel(level)
        logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str | None = None) -> Logger:
    """Get a logger instance.

    Args:
        name: Optional logger name (defaults to media_audit)

    Returns:
        Logger instance
    """
    if name:
        return logging.getLogger(f"media_audit.{name}")
    return logging.getLogger("media_audit")
