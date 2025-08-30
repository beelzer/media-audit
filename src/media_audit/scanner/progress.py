"""Multi-root progress tracking with separate bars for each root."""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    ProgressColumn,
    Task,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.text import Text

if TYPE_CHECKING:
    from .config import ScannerConfig


class CacheStatsColumn(ProgressColumn):  # type: ignore[misc]
    """Custom column to show completed/total [cached] stats."""

    def render(self, task: Task) -> Text:
        """Render the cache stats."""
        completed = int(task.completed)
        total = task.total if task.total is not None else 0

        # Get cache hits from task fields (we'll store it there)
        cache_hits = task.fields.get("cache_hits", 0)

        # Format: completed/total [cache_hits]
        base_text = Text(f"{completed}/{total}", style="white")

        if cache_hits > 0:
            base_text.append(" ")
            base_text.append(f"[{cache_hits}]", style="green")

        return base_text


class ProgressTracker:
    """Progress tracker with separate bars for each root path."""

    def __init__(self, config: ScannerConfig):
        """Initialize progress tracker."""
        self.config = config
        self.console = Console()
        self._cancelled = False
        self._cancel_lock = threading.Lock()
        self._progress: Progress | None = None

        # Track tasks for each root
        self._root_tasks: dict[Path, int] = {}
        self._root_totals: dict[Path, int] = {}
        self._root_cache_hits: dict[Path, int] = {}  # Track cache hits per root
        self._current_root: Path | None = None
        self._discovery_task: int | None = None
        self._season_task: int | None = None  # Track current season scanning task

    def start(self) -> None:
        """Start progress tracking."""
        self._cancelled = False

        # Create progress with multiple bars (ASCII-safe for Windows)
        self._progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            CacheStatsColumn(),  # Custom column with cache stats
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )
        self._progress.start()

        # Start ESC monitoring if available
        if sys.platform == "win32":
            try:
                import importlib.util

                if importlib.util.find_spec("msvcrt"):
                    esc_thread = threading.Thread(target=self._monitor_esc, daemon=True)
                    esc_thread.start()
            except ImportError:
                pass

    def stop(self) -> None:
        """Stop progress tracking."""
        if self._progress:
            self._progress.stop()
            self._progress = None

    def cancel(self) -> None:
        """Mark as cancelled."""
        with self._cancel_lock:
            self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if cancelled."""
        with self._cancel_lock:
            return self._cancelled

    def update_discovery(self, message: str) -> None:
        """Update discovery progress."""
        # Fixed width for consistency
        label_width = 15  # Shorter for discovery
        label = "Discovery:".ljust(label_width)

        # Truncate long messages
        msg_width = 40
        if len(message) > msg_width:
            message = message[: msg_width - 3] + "..."
        message = message.ljust(msg_width)

        description = f"[cyan]{label} {message}"

        if self._progress:
            if self._discovery_task is None:
                self._discovery_task = self._progress.add_task(description, total=None)
            else:
                self._progress.update(self._discovery_task, description=description)

    def setup_root_processing(self, root: Path, total: int) -> None:
        """Setup processing for a specific root path."""
        if self._progress and root not in self._root_tasks:
            # Store total for this root
            self._root_totals[root] = total
            self._root_cache_hits[root] = 0  # Initialize cache hits

            # Create task for this root with fixed width
            root_name = self._format_root_name(root)
            root_width = 15  # Same as discovery for alignment
            if len(root_name) > root_width:
                root_name = root_name[: root_width - 3] + "..."
            root_name = root_name.ljust(root_width)

            # Add placeholder for item name
            item_placeholder = "Starting...".ljust(40)

            task_id = self._progress.add_task(
                f"[yellow]{root_name} {item_placeholder}",
                total=total,
                cache_hits=0,  # Initialize cache_hits field
            )
            self._root_tasks[root] = task_id

    def setup_processing(self, total: int) -> None:
        """Setup overall processing (discovery complete)."""
        if self._progress and self._discovery_task is not None:
            # Mark discovery as complete with fixed width
            label_width = 15  # Same as discovery
            label = "Discovery:".ljust(label_width)
            msg = f"Complete - found {total} items".ljust(40)

            self._progress.update(
                self._discovery_task, completed=True, description=f"[green]{label} {msg}"
            )

    def update_processing(self, current: int, total: int, item_name: str) -> None:
        """Update processing message for current item (called at start)."""
        if not self._progress:
            return

        # Determine which root this item belongs to
        item_root = self._get_item_root(item_name)

        if item_root and item_root in self._root_tasks:
            # Format root name with fixed width
            root_name = self._format_root_name(item_root)
            root_width = 15  # Same as discovery for alignment
            if len(root_name) > root_width:
                root_name = root_name[: root_width - 3] + "..."
            root_name = root_name.ljust(root_width)

            # Truncate item name with fixed width
            item_width = 40
            display_name = item_name
            if len(display_name) > item_width:
                display_name = "..." + display_name[-(item_width - 3) :]
            display_name = display_name.ljust(item_width)

            # Update the specific root's description only (no progress advance)
            task_id = self._root_tasks[item_root]

            # Build description with fixed total width
            description = f"[yellow]{root_name} {display_name}"

            # Update description only
            self._progress.update(task_id, description=description)

    def advance_processing(self, current: int, total: int) -> None:
        """Advance the progress bar after processing completes."""
        if not self._progress or not self._current_root:
            return

        # Advance the progress for the current root
        if self._current_root in self._root_tasks:
            task_id = self._root_tasks[self._current_root]
            self._progress.update(task_id, advance=1)

    def set_current_root(self, root: Path) -> None:
        """Set the current root being processed."""
        self._current_root = root

    def _get_item_root(self, item_name: str) -> Path | None:
        """Determine which root an item belongs to."""
        # Use current root if set
        if self._current_root:
            return self._current_root

        # Otherwise try to match based on path
        for root in self._root_tasks:
            if str(root) in item_name or root.name in item_name:
                return root

        # Default to first root if can't determine
        if self._root_tasks:
            return list(self._root_tasks.keys())[0]

        return None

    def _format_root_name(self, root: Path) -> str:
        """Format root path for display."""
        # Show just the last two parts of the path for clarity
        parts = root.parts

        # Special handling for Media folder structure
        if len(parts) > 2 and parts[-2].lower() == "media":
            # Just show "Movies" or "TV Shows" without "Media/"
            return parts[-1]
        elif len(parts) > 2:
            return f"{parts[-2]}/{parts[-1]}"
        elif len(parts) > 1:
            return f"{parts[-1]}"
        return str(root)

    def start_series_scan(self, series_name: str, total_episodes: int) -> None:
        """Start scanning a TV series with episode progress."""
        if self._progress and total_episodes > 0:
            # Format series name with fixed width
            label_width = 15  # Same as main labels for alignment
            series_label = "  → Episodes"
            series_label = series_label.ljust(label_width)

            msg = f"Starting scan of {total_episodes} episodes...".ljust(40)

            # Create task with determinate progress
            self._season_task = self._progress.add_task(
                f"[dim cyan]{series_label} {msg}", total=total_episodes
            )

    def update_episode_scan(
        self, episode_num: int, total_episodes: int, episode_info: str, is_cached: bool = False
    ) -> None:
        """Update episode scanning progress.

        Args:
            episode_num: Current episode number (0-based for 'start', 1-based for 'complete')
            total_episodes: Total number of episodes
            episode_info: Episode info like "S01E02: Episode Name"
            is_cached: Whether this episode was cached
        """
        if self._progress and self._season_task is not None:
            # Format display
            label_width = 15  # Same as main labels for alignment
            series_label = "  → Episodes"
            series_label = series_label.ljust(label_width)

            # Format episode info
            msg_width = 40
            msg = f"{episode_info[:20]} [cached]" if is_cached else episode_info

            if len(msg) > msg_width:
                msg = msg[: msg_width - 3] + "..."
            msg = msg.ljust(msg_width)

            # Update - completed shows the actual progress
            self._progress.update(
                self._season_task,
                completed=episode_num,
                description=f"[dim cyan]{series_label} {msg}",
            )

    def end_series_scan(self) -> None:
        """End the current series scan and remove season progress bar."""
        if self._progress and self._season_task is not None:
            # Mark as complete and remove the task
            self._progress.update(self._season_task, visible=False)
            self._progress.remove_task(self._season_task)
            self._season_task = None

    def add_issue(self) -> None:
        """Increment issue counter (no-op in this version)."""
        pass

    def add_cache_hit(self, root: Path | None = None) -> None:
        """Increment cache hit counter for a root."""
        if not root:
            root = self._current_root

        if root and root in self._root_cache_hits:
            self._root_cache_hits[root] += 1

            # Update the task's cache_hits field
            if root in self._root_tasks and self._progress:
                task_id = self._root_tasks[root]
                task = self._progress.tasks[task_id]
                task.fields["cache_hits"] = self._root_cache_hits[root]

    def _monitor_esc(self) -> None:
        """Monitor for ESC key on Windows."""
        try:
            import msvcrt

            while not self.is_cancelled():
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key == b"\x1b":
                        self.cancel()
                        self.console.print("\n[yellow]Scan cancelled[/yellow]")
                        break
                time.sleep(0.1)
        except Exception:
            pass
