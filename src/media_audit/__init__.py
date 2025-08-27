"""Media Audit - A tool for scanning and validating media libraries.

This package provides a comprehensive solution for scanning media libraries,
validating content organization, and generating detailed reports compatible
with various media servers like Plex, Jellyfin, and Emby.
"""

from __future__ import annotations

__version__ = "0.3.0"

# Only expose version at package level
# All other imports should be done from specific submodules
__all__ = ["__version__"]
