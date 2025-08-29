"""Error handling and reporting utilities."""

from __future__ import annotations

import logging
import sys
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from media_audit.core.exceptions import (
    CacheError,
    ConfigurationError,
    MediaAuditError,
    ParseError,
    ProbeError,
    ScanError,
    ValidationError,
)

T = TypeVar("T")

console = Console(stderr=True)
logger = logging.getLogger(__name__)


class ErrorReporter:
    """Handles error reporting to users and logs."""

    def __init__(self, verbose: bool = False, debug: bool = False):
        """Initialize error reporter.

        Args:
            verbose: Show detailed error messages
            debug: Show full stack traces
        """
        self.verbose = verbose
        self.debug = debug

    def report_error(self, error: Exception, context: str = "") -> None:
        """Report an error to the user and logs.

        Args:
            error: The exception to report
            context: Additional context about where the error occurred
        """
        # Log the full error
        logger.error(f"{context}: {error}", exc_info=self.debug)

        # Determine error type and message
        if isinstance(error, ConfigurationError):
            self._show_config_error(error)
        elif isinstance(error, ScanError):
            self._show_scan_error(error)
        elif isinstance(error, ProbeError):
            self._show_probe_error(error)
        elif isinstance(error, ValidationError):
            self._show_validation_error(error)
        elif isinstance(error, ParseError):
            self._show_parse_error(error)
        elif isinstance(error, CacheError):
            self._show_cache_error(error)
        elif isinstance(error, MediaAuditError):
            self._show_generic_error(error)
        else:
            self._show_unexpected_error(error)

        if self.debug:
            self._show_traceback()

    def _show_config_error(self, error: ConfigurationError) -> None:
        """Show configuration error."""
        console.print(
            Panel(
                Text(f"Configuration Error: {error}", style="red"),
                title="[red]Configuration Problem[/red]",
                border_style="red",
            )
        )
        if self.verbose:
            console.print("[yellow]Tip:[/yellow] Check your config file syntax and required fields")

    def _show_scan_error(self, error: ScanError) -> None:
        """Show scan error."""
        console.print(
            Panel(
                Text(f"Scan Error: {error}", style="red"),
                title="[red]Scanning Problem[/red]",
                border_style="red",
            )
        )
        if self.verbose:
            console.print("[yellow]Tip:[/yellow] Verify the media paths exist and are accessible")

    def _show_probe_error(self, error: ProbeError) -> None:
        """Show probe error."""
        console.print(
            Panel(
                Text(f"Media Probe Error: {error}", style="red"),
                title="[red]FFprobe Problem[/red]",
                border_style="red",
            )
        )
        if self.verbose:
            console.print("[yellow]Tip:[/yellow] Ensure FFmpeg/FFprobe is installed and in PATH")
            console.print("Install with: [cyan]winget install FFmpeg[/cyan] (Windows)")
            console.print("           : [cyan]brew install ffmpeg[/cyan] (macOS)")
            console.print("           : [cyan]apt install ffmpeg[/cyan] (Linux)")

    def _show_validation_error(self, error: ValidationError) -> None:
        """Show validation error."""
        console.print(
            Panel(
                Text(f"Validation Error: {error}", style="red"),
                title="[red]Validation Problem[/red]",
                border_style="red",
            )
        )

    def _show_parse_error(self, error: ParseError) -> None:
        """Show parse error."""
        console.print(
            Panel(
                Text(f"Parse Error: {error}", style="red"),
                title="[red]Parsing Problem[/red]",
                border_style="red",
            )
        )
        if self.verbose:
            console.print(
                "[yellow]Tip:[/yellow] Check file naming conventions match expected patterns"
            )

    def _show_cache_error(self, error: CacheError) -> None:
        """Show cache error."""
        console.print(
            Panel(
                Text(f"Cache Error: {error}", style="yellow"),
                title="[yellow]Cache Warning[/yellow]",
                border_style="yellow",
            )
        )
        if self.verbose:
            console.print(
                "[yellow]Note:[/yellow] Cache errors are non-fatal; continuing without cache"
            )

    def _show_generic_error(self, error: MediaAuditError) -> None:
        """Show generic media audit error."""
        console.print(
            Panel(
                Text(f"Error: {error}", style="red"),
                title="[red]Media Audit Error[/red]",
                border_style="red",
            )
        )

    def _show_unexpected_error(self, error: Exception) -> None:
        """Show unexpected error."""
        console.print(
            Panel(
                Text(f"Unexpected error: {error}", style="red"),
                title="[red]Unexpected Error[/red]",
                border_style="red",
            )
        )
        if self.verbose:
            console.print("[yellow]This might be a bug.[/yellow] Please report it at:")
            console.print("[cyan]https://github.com/beelzer/media-audit/issues[/cyan]")

    def _show_traceback(self) -> None:
        """Show full traceback."""
        console.print("\n[dim]Full traceback:[/dim]")
        console.print(traceback.format_exc())


def handle_errors(
    func: Callable[..., T],
    reporter: ErrorReporter | None = None,
    exit_on_error: bool = True,
    default_return: T | None = None,
) -> Callable[..., T | None]:
    """Decorator to handle errors in functions.

    Args:
        func: Function to wrap
        reporter: Error reporter instance
        exit_on_error: Whether to exit on error
        default_return: Default value to return on error

    Returns:
        Wrapped function
    """

    def wrapper(*args: Any, **kwargs: Any) -> T | None:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if reporter:
                reporter.report_error(e, f"In {func.__name__}")
            else:
                logger.error(f"Error in {func.__name__}: {e}")

            if exit_on_error:
                sys.exit(1)
            return default_return

    return wrapper


def create_error_reporter(verbose: bool = False, debug: bool = False) -> ErrorReporter:
    """Create an error reporter instance.

    Args:
        verbose: Show detailed error messages
        debug: Show full stack traces

    Returns:
        Error reporter instance
    """
    return ErrorReporter(verbose=verbose, debug=debug)
