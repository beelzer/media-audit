"""New command-line interface for media-audit."""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from media_audit.presentation.reports import HTMLReportGenerator, JSONReportGenerator
from media_audit.scanner import Scanner, ScannerConfig
from media_audit.scanner.results import ScanResults
from media_audit.shared import setup_logger

console = Console()


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    default="config.yaml",
    help="Configuration file path",
)
@click.option(
    "--roots",
    "-r",
    multiple=True,
    help="Override root directories to scan",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose logging",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable caching",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    help="Number of concurrent workers",
)
@click.option(
    "--report",
    "-o",
    type=click.Path(path_type=Path),
    help="HTML report output path",
)
@click.option(
    "--json",
    "-j",
    type=click.Path(path_type=Path),
    help="JSON report output path",
)
@click.option(
    "--open",
    "-O",
    "auto_open",
    is_flag=True,
    help="Open HTML report after generation",
)
@click.option(
    "--problems-only",
    is_flag=True,
    help="Only show items with problems in report",
)
def scan(
    config: Path,
    roots: tuple[str, ...],
    verbose: bool,
    debug: bool,
    no_cache: bool,
    workers: int | None,
    report: Path | None,
    json: Path | None,
    auto_open: bool,
    problems_only: bool,
) -> None:
    """Scan media libraries and generate reports."""
    # Setup logging
    import logging

    log_level = logging.WARNING
    if debug:
        log_level = logging.DEBUG
    elif verbose:
        log_level = logging.INFO

    setup_logger(level=log_level)

    # Load configuration
    try:
        if config.exists():
            scanner_config = ScannerConfig.from_file(config)
        else:
            console.print(f"[yellow]Config file not found: {config}[/yellow]")
            console.print("[dim]Using default configuration[/dim]")
            scanner_config = ScannerConfig()
    except Exception as e:
        console.print(f"[red]Failed to load config:[/red] {e}")
        sys.exit(1)

    # Apply overrides
    if roots:
        scanner_config.root_paths = [Path(r) for r in roots]

    if no_cache:
        scanner_config.cache_enabled = False

    if workers is not None:
        scanner_config.concurrent_workers = workers

    if report:
        scanner_config.output_path = report

    if json:
        scanner_config.json_path = json

    if auto_open:
        scanner_config.auto_open = auto_open

    if problems_only:
        scanner_config.problems_only = problems_only

    # Validate configuration
    errors = scanner_config.validate()
    if errors:
        console.print("[red]Configuration errors:[/red]")
        for error in errors:
            console.print(f"  • {error}")
        sys.exit(1)

    # Run scan
    console.print("\n[bold cyan]Media Audit Scanner[/bold cyan]\n")

    try:
        scanner = Scanner(scanner_config)
        results = scanner.scan()
    except KeyboardInterrupt:
        console.print("\n[yellow]Scan cancelled by user[/yellow]")
        sys.exit(2)
    except Exception as e:
        console.print(f"[red]Scan failed:[/red] {e}")
        if debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)

    # Display summary
    _display_summary(results)

    # Generate reports if not cancelled
    if not results.cancelled:
        _generate_reports(scanner_config, results)

    # Exit with error code if issues found
    if results.total_issues > 0:
        sys.exit(1)


def _display_summary(results: ScanResults) -> None:
    """Display scan results summary."""
    stats = results.get_stats()

    # Create summary table
    table = Table(title="Scan Summary", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    table.add_row("Total Items", str(stats["total_items"]))
    table.add_row("Movies", str(stats["movies"]))
    table.add_row("TV Series", str(stats["series"]))
    table.add_row("Total Issues", str(stats["total_issues"]))

    if stats["errors"] > 0:
        table.add_row("[red]Errors[/red]", f"[red]{stats['errors']}[/red]")
    else:
        table.add_row("Errors", "0")

    if stats["warnings"] > 0:
        table.add_row("[yellow]Warnings[/yellow]", f"[yellow]{stats['warnings']}[/yellow]")
    else:
        table.add_row("Warnings", "0")

    table.add_row("Scan Duration", f"{stats['duration']:.2f}s")

    console.print(table)

    # Show sample issues
    if results.total_issues > 0:
        console.print("\n[bold]Sample Issues:[/bold]")

        items = results.get_items_with_issues()[:5]
        for item in items:
            console.print(f"\n[cyan]{item.name}[/cyan]")
            for issue in item.issues[:2]:
                severity_color = "red" if issue.severity.name == "ERROR" else "yellow"
                console.print(f"  [{severity_color}]•[/{severity_color}] {issue.message}")

        if results.total_issues > 5:
            console.print(f"\n[dim]... and {results.total_issues - 5} more issues[/dim]")


def _generate_reports(config: ScannerConfig, results: ScanResults) -> None:
    """Generate HTML and JSON reports."""
    # Convert to old format for compatibility
    from media_audit.core import ScanResult

    old_result = ScanResult(
        scan_time=results.scan_time,
        duration=results.duration,
        root_paths=config.root_paths,
        errors=results.errors,
    )
    old_result.movies = results.movies
    old_result.series = results.series
    old_result.update_stats()

    # Generate HTML report
    if config.output_path:
        console.print(f"\n[cyan]Generating HTML report:[/cyan] {config.output_path}")
        try:
            html_gen = HTMLReportGenerator()
            html_gen.generate(old_result, config.output_path, config.problems_only)

            if config.auto_open:
                report_path = config.output_path.resolve()
                webbrowser.open(str(report_path.as_uri()))
        except Exception as e:
            console.print(f"[red]Failed to generate HTML report:[/red] {e}")

    # Generate JSON report
    if config.json_path:
        console.print(f"[cyan]Generating JSON report:[/cyan] {config.json_path}")
        try:
            json_gen = JSONReportGenerator()
            json_gen.generate(old_result, config.json_path)
        except Exception as e:
            console.print(f"[red]Failed to generate JSON report:[/red] {e}")


def main() -> None:
    """Main entry point."""
    scan()


if __name__ == "__main__":
    main()
