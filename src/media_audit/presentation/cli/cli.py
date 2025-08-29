"""Command-line interface for media-audit."""

from __future__ import annotations

import sys
import webbrowser
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from media_audit.core import ScanResult, ValidationStatus
from media_audit.domain import MediaScanner
from media_audit.infrastructure import Config, ReportConfig, ScanConfig
from media_audit.presentation.reports import HTMLReportGenerator, JSONReportGenerator
from media_audit.shared import setup_logger
from media_audit.shared.error_handler import create_error_reporter
from media_audit.shared.platform_utils import get_cache_dir, run_async

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option()
def cli(ctx: click.Context) -> None:
    """Media Audit - Scan and validate your media library."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(scan)


@cli.command()
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
    "--log-file",
    type=click.Path(path_type=Path),
    help="Log output to file",
)
@click.option(
    "--roots",
    "-r",
    multiple=True,
    help="Root directories to scan (can specify multiple)",
)
@click.option(
    "--profiles",
    "-p",
    multiple=True,
    default=["all"],
    help="Media server profiles to use (plex, jellyfin, emby, all)",
)
@click.option(
    "--report",
    "-o",
    type=click.Path(path_type=Path),
    help="Output HTML report path",
)
@click.option(
    "--json",
    "-j",
    type=click.Path(path_type=Path),
    help="Output JSON report path",
)
@click.option(
    "--open",
    "-O",
    "auto_open",
    is_flag=True,
    help="Open HTML report in browser after generation",
)
@click.option(
    "--allow-codecs",
    multiple=True,
    help="Allowed video codecs (default: hevc, h265, av1)",
)
@click.option(
    "--include",
    multiple=True,
    help="Include patterns for scanning",
)
@click.option(
    "--exclude",
    multiple=True,
    help="Exclude patterns for scanning",
)
@click.option(
    "--patterns",
    type=click.Path(exists=True, path_type=Path),
    help="Custom patterns YAML file",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True, path_type=Path),
    help="Configuration file path",
)
@click.option(
    "--workers",
    "-w",
    type=int,
    default=4,
    help="Number of concurrent workers",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable caching",
)
@click.option(
    "--problems-only",
    is_flag=True,
    help="Show only items with problems in report",
)
def scan(
    verbose: bool,
    debug: bool,
    log_file: Path | None,
    roots: tuple[str, ...],
    profiles: tuple[str, ...],
    report: Path | None,
    json: Path | None,
    auto_open: bool,
    allow_codecs: tuple[str, ...],
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    patterns: Path | None,
    config: Path | None,
    workers: int,
    no_cache: bool,
    problems_only: bool,
) -> None:
    """Scan media libraries and generate reports."""
    # Setup logging
    import logging

    log_level = logging.INFO
    if debug:
        log_level = logging.DEBUG
    elif verbose:
        log_level = logging.INFO

    logger = setup_logger(level=log_level, log_file=log_file)
    logger.info("Starting media audit scan")

    # Create error reporter
    error_reporter = create_error_reporter(verbose=verbose, debug=debug)

    # Load configuration
    try:
        cfg = Config.from_file(config) if config else Config()
    except Exception as e:
        error_reporter.report_error(e, "Failed to load configuration")
        sys.exit(1)

    # Override with command-line options
    if roots:
        cfg.scan.root_paths = [Path(r) for r in roots]

    if not cfg.scan.root_paths:
        console.print(
            "[red]Error:[/red] No root paths specified. Use --roots or provide a config file."
        )
        sys.exit(1)

    if profiles and profiles != ("all",):
        cfg.scan.profiles = list(profiles)

    if allow_codecs:
        from media_audit.core import CodecType

        cfg.scan.allowed_codecs = []
        for codec in allow_codecs:
            try:
                cfg.scan.allowed_codecs.append(CodecType[codec.upper()])
            except KeyError:
                console.print(f"[yellow]Warning:[/yellow] Unknown codec '{codec}', skipping")

    if include:
        cfg.scan.include_patterns = list(include)

    if exclude:
        cfg.scan.exclude_patterns = list(exclude)

    if workers:
        cfg.scan.concurrent_workers = workers

    if no_cache:
        cfg.scan.cache_enabled = False

    if report:
        cfg.report.output_path = report

    if json:
        cfg.report.json_path = json

    if auto_open:
        cfg.report.auto_open = auto_open

    if problems_only:
        cfg.report.problems_only = problems_only

    # Load custom patterns if provided
    if patterns:
        import yaml

        from media_audit.domain import MediaPatterns

        with patterns.open("r", encoding="utf-8") as f:
            pattern_data = yaml.safe_load(f)
            cfg.scan.patterns = MediaPatterns(**pattern_data)

    # Start scanning
    console.print("\n[bold cyan]📺 Media Audit Scanner[/bold cyan]\n")
    console.print(f"[dim]Scanning {len(cfg.scan.root_paths)} root path(s)...[/dim]\n")

    try:
        scanner = MediaScanner(cfg.scan)

        # Run async scan with platform-specific configuration
        result = run_async(scanner.scan(), suppress_warnings=True)
    except Exception as e:
        error_reporter.report_error(e, "Scan failed")
        sys.exit(1)

    # Check if scan was cancelled
    was_cancelled = any("cancelled" in str(err).lower() for err in result.errors)

    # Display results summary
    _display_summary(result)

    if was_cancelled:
        console.print("\n[yellow]Scan was cancelled. Reports will not be generated.[/yellow]")
        sys.exit(2)  # Exit with special code for cancellation

    # Generate reports
    if cfg.report.output_path:
        console.print(f"\n[cyan]Generating HTML report:[/cyan] {cfg.report.output_path}")
        try:
            html_gen = HTMLReportGenerator()
            html_gen.generate(result, cfg.report.output_path, cfg.report.problems_only)

            if cfg.report.auto_open:
                report_path = cfg.report.output_path.resolve()
                webbrowser.open(str(report_path.as_uri()))
        except Exception as e:
            error_reporter.report_error(e, "Failed to generate HTML report")

    if cfg.report.json_path:
        console.print(f"[cyan]Generating JSON report:[/cyan] {cfg.report.json_path}")
        try:
            json_gen = JSONReportGenerator()
            json_gen.generate(result, cfg.report.json_path)
        except Exception as e:
            error_reporter.report_error(e, "Failed to generate JSON report")

    # Exit with error code if issues found
    if result.total_issues > 0:
        sys.exit(1)


@cli.command()
@click.argument("output", type=click.Path(path_type=Path))
@click.option("--full", is_flag=True, help="Generate full config with all options")
def init_config(output: Path, full: bool = False) -> None:
    """Generate a sample configuration file."""
    # Check if file exists
    if output.exists() and not click.confirm(f"File {output} already exists. Overwrite?"):
        console.print("[yellow]Aborted.[/yellow]")
        return

    sample_config = Config(
        scan=ScanConfig(
            root_paths=[Path("D:/Media"), Path("E:/Media")],
            profiles=["plex", "jellyfin"],
            concurrent_workers=4,
            cache_enabled=True,
        ),
        report=ReportConfig(
            output_path=Path("report.html"),
            json_path=Path("report.json"),
            auto_open=True,
            show_thumbnails=True,
            problems_only=False,
        ),
    )

    sample_config.save(output)
    console.print(f"[green]✓[/green] Created sample configuration at {output}")
    console.print("\n[dim]Edit this file to customize your scan settings.[/dim]")


@cli.command()
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Custom cache directory to clear (default: ~/.cache/media-audit)",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Skip confirmation prompt",
)
def clear_cache(cache_dir: Path | None, force: bool) -> None:
    """Clear the media-audit cache directory."""
    import shutil

    # Determine cache directory
    cache_path = cache_dir or get_cache_dir()

    # Check if cache directory exists
    if not cache_path.exists():
        console.print(f"[yellow]Cache directory does not exist:[/yellow] {cache_path}")
        return

    # Calculate cache size
    try:
        total_size = sum(f.stat().st_size for f in cache_path.rglob("*") if f.is_file())
        size_mb = total_size / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb / 1024:.1f} GB"
    except Exception:
        size_str = "unknown size"

    # Show cache info and confirm
    console.print(f"[cyan]Cache directory:[/cyan] {cache_path}")
    console.print(f"[cyan]Cache size:[/cyan] {size_str}")

    if not force and not click.confirm("Are you sure you want to clear the cache?"):
        console.print("[yellow]Aborted.[/yellow]")
        return

    # Clear the cache
    try:
        shutil.rmtree(cache_path, ignore_errors=True)
        console.print(f"[green]SUCCESS:[/green] Cache cleared successfully ({size_str} freed)")
        console.print("[dim]The cache will be recreated on the next scan.[/dim]")
    except Exception as e:
        console.print(f"[red]ERROR:[/red] Failed to clear cache: {e}")
        sys.exit(1)


def _count_issues_by_severity(result: ScanResult) -> tuple[int, int]:
    """Count issues by severity level.

    Returns:
        Tuple of (error_count, warning_count)

    """
    error_count = 0
    warning_count = 0

    # Count all issues from all media items
    all_items: list[Any] = []
    all_items.extend(result.movies)
    all_items.extend(result.series)

    for series in result.series:
        all_items.extend(series.seasons)
        for season in series.seasons:
            all_items.extend(season.episodes)

    for item in all_items:
        for issue in item.issues:
            match issue.severity:
                case ValidationStatus.ERROR:
                    error_count += 1
                case ValidationStatus.WARNING:
                    warning_count += 1
                case _:
                    pass

    return error_count, warning_count


def _display_summary(result: ScanResult) -> None:
    """Display scan results summary."""
    # Create summary table
    table = Table(title="Scan Summary", show_header=True, header_style="bold cyan")
    table.add_column("Category", style="dim")
    table.add_column("Count", justify="right")

    table.add_row("Total Items", str(result.total_items))
    table.add_row("Movies", str(len(result.movies)))
    table.add_row("TV Series", str(len(result.series)))
    table.add_row("Total Issues", str(result.total_issues))

    # Count by severity using a helper function
    error_count, warning_count = _count_issues_by_severity(result)

    table.add_row("[red]Errors[/red]", f"[red]{error_count}[/red]")
    table.add_row("[yellow]Warnings[/yellow]", f"[yellow]{warning_count}[/yellow]")
    table.add_row("Scan Duration", f"{result.duration:.2f}s")

    console.print(table)

    # Show sample issues
    if result.total_issues > 0:
        console.print("\n[bold]Sample Issues Found:[/bold]")

        items_with_issues = result.get_items_with_issues()[:5]  # Show first 5
        for item in items_with_issues:
            console.print(f"\n[cyan]{item.name}[/cyan] ({item.path})")
            for issue in item.issues[:3]:  # Show first 3 issues per item
                severity_color = "red" if issue.severity == ValidationStatus.ERROR else "yellow"
                console.print(f"  [{severity_color}]▸[/{severity_color}] {issue.message}")

        if result.total_issues > 5:
            console.print(f"\n[dim]... and {result.total_issues - 5} more issues[/dim]")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
