"""Report generation module."""

from .html import HTMLReportGenerator
from .json import JSONReportGenerator

__all__ = ["HTMLReportGenerator", "JSONReportGenerator"]