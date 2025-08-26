# Reports API Reference

This reference documents the report generation system for creating HTML and JSON output from scan results.

## Core Report Generators

### `HTMLReportGenerator`

Generates interactive HTML reports with embedded styling and JavaScript.

```python
from media_audit.report import HTMLReportGenerator
from pathlib import Path

class HTMLReportGenerator:
    """Generates interactive HTML reports."""

    def __init__(self):
        """Initialize HTML report generator."""
```

#### Methods

##### `generate()`

Main method for generating HTML reports.

```python
def generate(
    self,
    scan_result: ScanResult,
    output_path: Path,
    problems_only: bool = False,
    show_thumbnails: bool = True
) -> None:
    """Generate HTML report from scan results."""
```

**Parameters**:

- `scan_result`: Complete scan results to report on
- `output_path`: Where to save the HTML file
- `problems_only`: Show only items with validation issues
- `show_thumbnails`: Include poster thumbnails in report

**Process**:

1. Filter results based on `problems_only` setting
2. Generate HTML structure with embedded CSS and JavaScript
3. Create interactive elements (search, filters, sorting)
4. Write complete HTML file to output path

**Usage Example**:

```python
from media_audit.report import HTMLReportGenerator

generator = HTMLReportGenerator()
generator.generate(
    scan_result=scan_results,
    output_path=Path("audit-report.html"),
    problems_only=True,
    show_thumbnails=True
)

print(f"HTML report generated: audit-report.html")
```

#### HTML Structure

The generated HTML follows this structure:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Media Audit Report</title>
    <style>/* Embedded CSS */</style>
</head>
<body>
    <header class="fixed-header">
        <h1>Media Audit Report</h1>
        <div class="controls">
            <input type="search" id="searchBox" placeholder="Search...">
            <select id="filterSelect">...</select>
            <select id="sortSelect">...</select>
        </div>
    </header>

    <main>
        <section class="summary">
            <!-- Scan statistics -->
        </section>

        <section class="movies">
            <!-- Movie items -->
        </section>

        <section class="series">
            <!-- TV series items -->
        </section>
    </main>

    <script>/* Interactive JavaScript */</script>
</body>
</html>
```

#### Interactive Features

##### Search Functionality

```javascript
// Search implementation (embedded in HTML)
function filterItems(searchTerm) {
    const items = document.querySelectorAll('.media-item');
    const term = searchTerm.toLowerCase();

    items.forEach(item => {
        const title = item.querySelector('.item-title').textContent.toLowerCase();
        const path = item.querySelector('.item-path').textContent.toLowerCase();

        if (title.includes(term) || path.includes(term)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}
```

##### Status Filtering

```javascript
function filterByStatus(status) {
    const items = document.querySelectorAll('.media-item');

    items.forEach(item => {
        if (status === 'all' || item.classList.contains(status)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}
```

##### Sorting Options

```javascript
function sortItems(criteria) {
    const containers = [
        document.getElementById('movies-container'),
        document.getElementById('series-container')
    ];

    containers.forEach(container => {
        if (!container) return;

        const items = Array.from(container.querySelectorAll('.media-item'));

        items.sort((a, b) => {
            switch (criteria) {
                case 'name':
                    return a.dataset.name.localeCompare(b.dataset.name);
                case 'status':
                    return a.dataset.status.localeCompare(b.dataset.status);
                case 'issues':
                    return parseInt(b.dataset.issues) - parseInt(a.dataset.issues);
                default:
                    return 0;
            }
        });

        // Re-append sorted items
        items.forEach(item => container.appendChild(item));
    });
}
```

### `JSONReportGenerator`

Generates structured JSON reports suitable for automation and integration.

```python
from media_audit.report import JSONReportGenerator

class JSONReportGenerator:
    """Generates structured JSON reports."""

    def __init__(self):
        """Initialize JSON report generator."""
```

#### Methods

##### `generate()`

Main method for generating JSON reports.

```python
def generate(
    self,
    scan_result: ScanResult,
    output_path: Path
) -> None:
    """Generate JSON report from scan results."""
```

**Parameters**:

- `scan_result`: Complete scan results to serialize
- `output_path`: Where to save the JSON file

**Usage Example**:

```python
from media_audit.report import JSONReportGenerator

generator = JSONReportGenerator()
generator.generate(
    scan_result=scan_results,
    output_path=Path("audit-data.json")
)

print(f"JSON report generated: audit-data.json")
```

#### JSON Schema

The generated JSON follows this structure:

```json
{
  "scan_info": {
    "scan_time": "2025-01-15T10:30:00Z",
    "duration": 45.2,
    "root_paths": ["/media/movies", "/media/tv"],
    "total_items": 195,
    "total_issues": 90,
    "errors": ["Error message 1", "Error message 2"]
  },
  "statistics": {
    "movies_count": 150,
    "series_count": 45,
    "total_episodes": 1250,
    "error_count": 23,
    "warning_count": 67,
    "valid_count": 105
  },
  "movies": [
    {
      "name": "The Matrix",
      "path": "/media/movies/The Matrix (1999)",
      "year": 1999,
      "type": "movie",
      "status": "error",
      "assets": {
        "posters": ["/media/movies/The Matrix (1999)/poster.jpg"],
        "backgrounds": [],
        "banners": [],
        "trailers": ["/media/movies/The Matrix (1999)/trailer.mp4"],
        "title_cards": []
      },
      "video_info": {
        "path": "/media/movies/The Matrix (1999)/The Matrix (1999).mkv",
        "codec": "h264",
        "resolution": [1920, 1080],
        "duration": 8160.5,
        "bitrate": 5500000,
        "size": 5600000000
      },
      "issues": [
        {
          "category": "assets",
          "message": "Missing background/fanart image",
          "severity": "error",
          "details": {
            "expected": ["fanart.jpg", "background.jpg", "backdrop.jpg"]
          }
        }
      ],
      "metadata": {
        "imdb_id": "tt0133093",
        "tmdb_id": "603",
        "quality": "1080p",
        "source": "BluRay",
        "release_group": "GROUP"
      }
    }
  ],
  "series": [
    {
      "name": "Breaking Bad",
      "path": "/media/tv/Breaking Bad",
      "type": "tv_series",
      "status": "warning",
      "total_episodes": 62,
      "assets": {
        "posters": ["/media/tv/Breaking Bad/poster.jpg"],
        "backgrounds": ["/media/tv/Breaking Bad/fanart.jpg"],
        "banners": [],
        "trailers": [],
        "title_cards": []
      },
      "seasons": [
        {
          "season_number": 1,
          "name": "Season 1",
          "path": "/media/tv/Breaking Bad/Season 01",
          "type": "tv_season",
          "status": "valid",
          "assets": {
            "posters": ["/media/tv/Breaking Bad/Season01.jpg"],
            "backgrounds": [],
            "banners": [],
            "trailers": [],
            "title_cards": []
          },
          "episodes": [
            {
              "season_number": 1,
              "episode_number": 1,
              "name": "Pilot",
              "path": "/media/tv/Breaking Bad/Season 01/S01E01.mkv",
              "type": "tv_episode",
              "status": "valid",
              "episode_title": "Pilot",
              "video_info": {
                "path": "/media/tv/Breaking Bad/Season 01/S01E01.mkv",
                "codec": "hevc",
                "resolution": [1920, 1080],
                "duration": 2940.0,
                "bitrate": 3500000,
                "size": 1200000000
              },
              "assets": {
                "posters": [],
                "backgrounds": [],
                "banners": [],
                "trailers": [],
                "title_cards": ["/media/tv/Breaking Bad/Season 01/S01E01.jpg"]
              },
              "issues": [],
              "metadata": {
                "quality": "1080p",
                "source": "WEBDL",
                "release_group": "GROUP"
              }
            }
          ],
          "issues": []
        }
      ],
      "issues": [
        {
          "category": "assets",
          "message": "Missing series banner (optional)",
          "severity": "warning",
          "details": {
            "expected": ["banner.jpg"]
          }
        }
      ],
      "metadata": {
        "imdb_id": "tt0903747",
        "tvdb_id": "81189",
        "tmdb_id": "1396"
      }
    }
  ]
}
```

## Report Customization

### Custom HTML Templates

```python
class CustomHTMLReportGenerator(HTMLReportGenerator):
    """Custom HTML report generator with templates."""

    def __init__(self, template_dir: Path = None):
        super().__init__()
        self.template_dir = template_dir or Path("templates")

    def generate(self, scan_result: ScanResult, output_path: Path, **kwargs) -> None:
        """Generate report using custom templates."""

        # Load custom templates
        header_template = self.load_template("header.html")
        movie_template = self.load_template("movie_item.html")
        series_template = self.load_template("series_item.html")
        footer_template = self.load_template("footer.html")

        # Generate report sections
        html_content = self.build_html_with_templates(
            scan_result,
            header_template,
            movie_template,
            series_template,
            footer_template,
            **kwargs
        )

        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def load_template(self, template_name: str) -> str:
        """Load HTML template from file."""
        template_path = self.template_dir / template_name
        if template_path.exists():
            return template_path.read_text(encoding='utf-8')
        else:
            # Return default template
            return self.get_default_template(template_name)

    def build_html_with_templates(self, scan_result: ScanResult, *templates, **kwargs) -> str:
        """Build HTML using templates."""
        # Template rendering logic here
        pass

# Usage with custom templates
custom_generator = CustomHTMLReportGenerator(Path("custom_templates"))
custom_generator.generate(scan_results, Path("custom_report.html"))
```

### Themed Reports

```python
class ThemedReportGenerator(HTMLReportGenerator):
    """Report generator with theme support."""

    THEMES = {
        "dark": {
            "background": "#1a1a1a",
            "text": "#ffffff",
            "accent": "#4CAF50",
            "error": "#f44336",
            "warning": "#ff9800"
        },
        "light": {
            "background": "#ffffff",
            "text": "#333333",
            "accent": "#2196F3",
            "error": "#d32f2f",
            "warning": "#f57c00"
        },
        "blue": {
            "background": "#0d47a1",
            "text": "#ffffff",
            "accent": "#64b5f6",
            "error": "#ff5252",
            "warning": "#ffb74d"
        }
    }

    def __init__(self, theme: str = "light"):
        super().__init__()
        self.theme = self.THEMES.get(theme, self.THEMES["light"])

    def generate_css(self) -> str:
        """Generate themed CSS."""
        css_template = """
        body {
            background-color: {background};
            color: {text};
        }

        .header {
            background-color: {accent};
        }

        .error {
            color: {error};
        }

        .warning {
            color: {warning};
        }

        .accent {
            color: {accent};
        }
        """

        return css_template.format(**self.theme)

# Usage
dark_generator = ThemedReportGenerator("dark")
dark_generator.generate(scan_results, Path("dark_theme_report.html"))
```

## Advanced Report Features

### Report Statistics

```python
def generate_detailed_statistics(scan_result: ScanResult) -> dict:
    """Generate comprehensive statistics for reports."""

    stats = {
        "overview": {
            "total_items": scan_result.total_items,
            "total_issues": scan_result.total_issues,
            "scan_duration": scan_result.duration,
            "scan_time": scan_result.scan_time.isoformat()
        },
        "by_type": {
            "movies": len(scan_result.movies),
            "series": len(scan_result.series),
            "seasons": sum(len(s.seasons) for s in scan_result.series),
            "episodes": sum(s.total_episodes for s in scan_result.series)
        },
        "by_status": {
            "valid": 0,
            "warning": 0,
            "error": 0
        },
        "by_category": {
            "assets": 0,
            "encoding": 0,
            "structure": 0,
            "naming": 0,
            "quality": 0
        },
        "codecs": {},
        "resolutions": {},
        "file_sizes": {
            "total_size_gb": 0,
            "average_movie_size_gb": 0,
            "average_episode_size_gb": 0
        }
    }

    # Calculate statistics
    all_items = []
    all_items.extend(scan_result.movies)
    all_items.extend(scan_result.series)

    for series in scan_result.series:
        all_items.extend(series.seasons)
        for season in series.seasons:
            all_items.extend(season.episodes)

    # Status counts
    for item in all_items:
        stats["by_status"][item.status.value] += 1

        # Issue categories
        for issue in item.issues:
            if issue.category in stats["by_category"]:
                stats["by_category"][issue.category] += 1

    # Video statistics
    total_size = 0
    movie_sizes = []
    episode_sizes = []

    for movie in scan_result.movies:
        if movie.video_info:
            # Codec distribution
            codec = movie.video_info.codec.value if movie.video_info.codec else "unknown"
            stats["codecs"][codec] = stats["codecs"].get(codec, 0) + 1

            # Resolution distribution
            if movie.video_info.resolution:
                res_str = f"{movie.video_info.resolution[0]}x{movie.video_info.resolution[1]}"
                stats["resolutions"][res_str] = stats["resolutions"].get(res_str, 0) + 1

            # File sizes
            if movie.video_info.size:
                total_size += movie.video_info.size
                movie_sizes.append(movie.video_info.size)

    # Similar for episodes
    for series in scan_result.series:
        for season in series.seasons:
            for episode in season.episodes:
                if episode.video_info:
                    codec = episode.video_info.codec.value if episode.video_info.codec else "unknown"
                    stats["codecs"][codec] = stats["codecs"].get(codec, 0) + 1

                    if episode.video_info.resolution:
                        res_str = f"{episode.video_info.resolution[0]}x{episode.video_info.resolution[1]}"
                        stats["resolutions"][res_str] = stats["resolutions"].get(res_str, 0) + 1

                    if episode.video_info.size:
                        total_size += episode.video_info.size
                        episode_sizes.append(episode.video_info.size)

    # File size statistics
    stats["file_sizes"]["total_size_gb"] = round(total_size / (1024**3), 2)
    if movie_sizes:
        stats["file_sizes"]["average_movie_size_gb"] = round(
            sum(movie_sizes) / len(movie_sizes) / (1024**3), 2
        )
    if episode_sizes:
        stats["file_sizes"]["average_episode_size_gb"] = round(
            sum(episode_sizes) / len(episode_sizes) / (1024**3), 2
        )

    return stats
```

### Comparison Reports

```python
class ComparisonReportGenerator:
    """Generate comparison reports between scans."""

    def generate_comparison_report(
        self,
        baseline_result: ScanResult,
        current_result: ScanResult,
        output_path: Path
    ) -> None:
        """Generate comparison report between two scan results."""

        comparison = self.compare_results(baseline_result, current_result)

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Media Audit Comparison Report</title>
            <style>{self.get_comparison_css()}</style>
        </head>
        <body>
            <h1>Media Audit Comparison Report</h1>

            <section class="summary">
                <h2>Comparison Summary</h2>
                <div class="comparison-stats">
                    <div class="stat-group">
                        <h3>Total Issues</h3>
                        <div class="comparison">
                            <span class="baseline">{baseline_result.total_issues}</span>
                            <span class="arrow">→</span>
                            <span class="current">{current_result.total_issues}</span>
                            <span class="change {comparison['issues_trend']}">{comparison['issues_change']:+d}</span>
                        </div>
                    </div>

                    <div class="stat-group">
                        <h3>Total Items</h3>
                        <div class="comparison">
                            <span class="baseline">{baseline_result.total_items}</span>
                            <span class="arrow">→</span>
                            <span class="current">{current_result.total_items}</span>
                            <span class="change">{comparison['items_change']:+d}</span>
                        </div>
                    </div>
                </div>
            </section>

            <section class="improvements">
                <h2>Improvements</h2>
                <ul>
                    {''.join(f'<li>{improvement}</li>' for improvement in comparison['improvements'])}
                </ul>
            </section>

            <section class="new-issues">
                <h2>New Issues</h2>
                <ul>
                    {''.join(f'<li>{issue}</li>' for issue in comparison['new_issues'])}
                </ul>
            </section>

            <script>{self.get_comparison_js()}</script>
        </body>
        </html>
        """

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def compare_results(self, baseline: ScanResult, current: ScanResult) -> dict:
        """Compare two scan results."""

        # Create item lookup by path
        baseline_items = {item.path: item for item in self.get_all_items(baseline)}
        current_items = {item.path: item for item in self.get_all_items(current)}

        improvements = []
        new_issues = []

        # Find improvements
        for path, baseline_item in baseline_items.items():
            current_item = current_items.get(path)
            if current_item:
                baseline_issue_count = len(baseline_item.issues)
                current_issue_count = len(current_item.issues)

                if current_issue_count < baseline_issue_count:
                    improvement = f"{baseline_item.name}: {baseline_issue_count - current_issue_count} issues resolved"
                    improvements.append(improvement)

        # Find new issues
        for path, current_item in current_items.items():
            baseline_item = baseline_items.get(path)
            if baseline_item:
                baseline_issues = {issue.message for issue in baseline_item.issues}
                for issue in current_item.issues:
                    if issue.message not in baseline_issues:
                        new_issues.append(f"{current_item.name}: {issue.message}")

        issues_change = current.total_issues - baseline.total_issues
        items_change = current.total_items - baseline.total_items

        return {
            "issues_change": issues_change,
            "items_change": items_change,
            "issues_trend": "improvement" if issues_change < 0 else "regression" if issues_change > 0 else "stable",
            "improvements": improvements,
            "new_issues": new_issues
        }

    def get_all_items(self, scan_result: ScanResult) -> list:
        """Get all items from scan result."""
        items = []
        items.extend(scan_result.movies)
        items.extend(scan_result.series)

        for series in scan_result.series:
            items.extend(series.seasons)
            for season in series.seasons:
                items.extend(season.episodes)

        return items

# Usage
comparison_generator = ComparisonReportGenerator()
comparison_generator.generate_comparison_report(
    baseline_results,
    current_results,
    Path("comparison_report.html")
)
```

## Export Formats

### CSV Export

```python
import csv
from typing import Dict, Any

class CSVReportGenerator:
    """Generate CSV reports for data analysis."""

    def generate_csv_report(self, scan_result: ScanResult, output_path: Path) -> None:
        """Generate CSV report of all items and issues."""

        rows = []

        # Process movies
        for movie in scan_result.movies:
            base_row = {
                "type": "movie",
                "name": movie.name,
                "path": str(movie.path),
                "year": movie.year,
                "status": movie.status.value,
                "issue_count": len(movie.issues),
                "has_poster": bool(movie.assets.posters),
                "has_background": bool(movie.assets.backgrounds),
                "has_trailer": bool(movie.assets.trailers),
            }

            if movie.video_info:
                base_row.update({
                    "codec": movie.video_info.codec.value if movie.video_info.codec else None,
                    "resolution": f"{movie.video_info.resolution[0]}x{movie.video_info.resolution[1]}" if movie.video_info.resolution else None,
                    "duration_minutes": round(movie.video_info.duration / 60, 1) if movie.video_info.duration else None,
                    "size_gb": round(movie.video_info.size / (1024**3), 2) if movie.video_info.size else None,
                    "bitrate_mbps": round(movie.video_info.bitrate / 1_000_000, 1) if movie.video_info.bitrate else None,
                })

            # Add each issue as separate row
            if movie.issues:
                for issue in movie.issues:
                    issue_row = base_row.copy()
                    issue_row.update({
                        "issue_category": issue.category,
                        "issue_message": issue.message,
                        "issue_severity": issue.severity.value
                    })
                    rows.append(issue_row)
            else:
                rows.append(base_row)

        # Process TV series (similar structure)
        for series in scan_result.series:
            for season in series.seasons:
                for episode in season.episodes:
                    base_row = {
                        "type": "episode",
                        "series_name": series.name,
                        "name": episode.name,
                        "path": str(episode.path),
                        "season": episode.season_number,
                        "episode": episode.episode_number,
                        "status": episode.status.value,
                        "issue_count": len(episode.issues),
                        "has_title_card": bool(episode.assets.title_cards),
                    }

                    if episode.video_info:
                        base_row.update({
                            "codec": episode.video_info.codec.value if episode.video_info.codec else None,
                            "resolution": f"{episode.video_info.resolution[0]}x{episode.video_info.resolution[1]}" if episode.video_info.resolution else None,
                            "duration_minutes": round(episode.video_info.duration / 60, 1) if episode.video_info.duration else None,
                            "size_gb": round(episode.video_info.size / (1024**3), 2) if episode.video_info.size else None,
                        })

                    if episode.issues:
                        for issue in episode.issues:
                            issue_row = base_row.copy()
                            issue_row.update({
                                "issue_category": issue.category,
                                "issue_message": issue.message,
                                "issue_severity": issue.severity.value
                            })
                            rows.append(issue_row)
                    else:
                        rows.append(base_row)

        # Write CSV
        if rows:
            fieldnames = rows[0].keys()
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

# Usage
csv_generator = CSVReportGenerator()
csv_generator.generate_csv_report(scan_results, Path("media_audit.csv"))
```

### XML Export

```python
import xml.etree.ElementTree as ET
from xml.dom import minidom

class XMLReportGenerator:
    """Generate XML reports for structured data exchange."""

    def generate_xml_report(self, scan_result: ScanResult, output_path: Path) -> None:
        """Generate XML report."""

        # Create root element
        root = ET.Element("media_audit_report")
        root.set("version", "1.0")
        root.set("scan_time", scan_result.scan_time.isoformat())
        root.set("duration", str(scan_result.duration))

        # Scan info
        scan_info = ET.SubElement(root, "scan_info")
        ET.SubElement(scan_info, "total_items").text = str(scan_result.total_items)
        ET.SubElement(scan_info, "total_issues").text = str(scan_result.total_issues)

        # Root paths
        root_paths = ET.SubElement(scan_info, "root_paths")
        for path in scan_result.root_paths:
            ET.SubElement(root_paths, "path").text = str(path)

        # Movies section
        movies = ET.SubElement(root, "movies")
        movies.set("count", str(len(scan_result.movies)))

        for movie in scan_result.movies:
            movie_elem = ET.SubElement(movies, "movie")
            movie_elem.set("status", movie.status.value)

            ET.SubElement(movie_elem, "name").text = movie.name
            ET.SubElement(movie_elem, "path").text = str(movie.path)
            if movie.year:
                ET.SubElement(movie_elem, "year").text = str(movie.year)

            # Assets
            assets = ET.SubElement(movie_elem, "assets")
            for asset_type in ["posters", "backgrounds", "trailers"]:
                asset_list = getattr(movie.assets, asset_type)
                if asset_list:
                    asset_elem = ET.SubElement(assets, asset_type)
                    for asset_path in asset_list:
                        ET.SubElement(asset_elem, "file").text = str(asset_path)

            # Video info
            if movie.video_info:
                video = ET.SubElement(movie_elem, "video_info")
                if movie.video_info.codec:
                    ET.SubElement(video, "codec").text = movie.video_info.codec.value
                if movie.video_info.resolution:
                    resolution = ET.SubElement(video, "resolution")
                    ET.SubElement(resolution, "width").text = str(movie.video_info.resolution[0])
                    ET.SubElement(resolution, "height").text = str(movie.video_info.resolution[1])
                if movie.video_info.duration:
                    ET.SubElement(video, "duration").text = str(movie.video_info.duration)
                if movie.video_info.size:
                    ET.SubElement(video, "size").text = str(movie.video_info.size)

            # Issues
            if movie.issues:
                issues = ET.SubElement(movie_elem, "issues")
                issues.set("count", str(len(movie.issues)))

                for issue in movie.issues:
                    issue_elem = ET.SubElement(issues, "issue")
                    issue_elem.set("severity", issue.severity.value)
                    issue_elem.set("category", issue.category)
                    ET.SubElement(issue_elem, "message").text = issue.message

        # TV series section (similar structure)
        series_elem = ET.SubElement(root, "series")
        series_elem.set("count", str(len(scan_result.series)))
        # ... (implement similar to movies)

        # Format and write XML
        xml_string = ET.tostring(root, encoding='unicode')
        pretty_xml = minidom.parseString(xml_string).toprettyxml(indent="  ")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)

# Usage
xml_generator = XMLReportGenerator()
xml_generator.generate_xml_report(scan_results, Path("media_audit.xml"))
```

## Integration Examples

### Slack Notifications

```python
import requests
import json

class SlackReportGenerator:
    """Generate Slack notifications from scan results."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_summary_notification(self, scan_result: ScanResult) -> None:
        """Send summary notification to Slack."""

        # Prepare message
        color = "good" if scan_result.total_issues == 0 else "warning" if scan_result.total_issues < 10 else "danger"

        attachment = {
            "color": color,
            "title": "Media Audit Completed",
            "fields": [
                {
                    "title": "Total Items",
                    "value": str(scan_result.total_items),
                    "short": True
                },
                {
                    "title": "Issues Found",
                    "value": str(scan_result.total_issues),
                    "short": True
                },
                {
                    "title": "Scan Duration",
                    "value": f"{scan_result.duration:.1f} seconds",
                    "short": True
                },
                {
                    "title": "Movies",
                    "value": str(len(scan_result.movies)),
                    "short": True
                },
                {
                    "title": "TV Series",
                    "value": str(len(scan_result.series)),
                    "short": True
                }
            ],
            "footer": "Media Audit",
            "ts": int(scan_result.scan_time.timestamp())
        }

        if scan_result.total_issues > 0:
            # Add sample issues
            sample_issues = self.get_sample_issues(scan_result, limit=3)
            if sample_issues:
                attachment["fields"].append({
                    "title": "Sample Issues",
                    "value": "\n".join(f"• {issue}" for issue in sample_issues),
                    "short": False
                })

        payload = {
            "text": "Media Library Scan Results",
            "attachments": [attachment]
        }

        # Send to Slack
        response = requests.post(self.webhook_url, json=payload)
        response.raise_for_status()

    def get_sample_issues(self, scan_result: ScanResult, limit: int = 5) -> list[str]:
        """Get sample issues for notification."""
        issues = []

        for movie in scan_result.movies:
            if movie.issues:
                issues.append(f"{movie.name}: {movie.issues[0].message}")
                if len(issues) >= limit:
                    break

        if len(issues) < limit:
            for series in scan_result.series:
                if series.issues:
                    issues.append(f"{series.name}: {series.issues[0].message}")
                    if len(issues) >= limit:
                        break

        return issues

# Usage
slack_notifier = SlackReportGenerator("https://hooks.slack.com/services/...")
slack_notifier.send_summary_notification(scan_results)
```

### Email Reports

```python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

class EmailReportGenerator:
    """Generate and send email reports."""

    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send_report_email(
        self,
        scan_result: ScanResult,
        recipients: list[str],
        html_report_path: Path = None,
        json_report_path: Path = None
    ) -> None:
        """Send email with scan results and optional attachments."""

        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.username
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = f"Media Audit Report - {scan_result.total_issues} Issues Found"

        # Email body
        body = self.generate_email_body(scan_result)
        msg.attach(MIMEText(body, 'html'))

        # Attach reports
        if html_report_path and html_report_path.exists():
            self.attach_file(msg, html_report_path)

        if json_report_path and json_report_path.exists():
            self.attach_file(msg, json_report_path)

        # Send email
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)

    def generate_email_body(self, scan_result: ScanResult) -> str:
        """Generate HTML email body."""

        status_color = "#4CAF50" if scan_result.total_issues == 0 else "#FF9800" if scan_result.total_issues < 10 else "#F44336"

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #333;">Media Audit Report</h2>

            <div style="background-color: #f5f5f5; padding: 20px; border-radius: 5px; margin: 20px 0;">
                <h3>Scan Summary</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Scan Date:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{scan_result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Duration:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{scan_result.duration:.1f} seconds</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Total Items:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;">{scan_result.total_items}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Issues Found:</strong></td>
                        <td style="padding: 8px; border-bottom: 1px solid #ddd; color: {status_color};">
                            <strong>{scan_result.total_issues}</strong>
                        </td>
                    </tr>
                </table>
            </div>
        """

        if scan_result.total_issues > 0:
            html += """
            <div style="margin: 20px 0;">
                <h3>Top Issues</h3>
                <ul>
            """

            # Add top issues
            issue_count = 0
            for movie in scan_result.movies:
                for issue in movie.issues[:2]:  # Max 2 per movie
                    if issue_count >= 10:  # Max 10 total
                        break
                    color = "#F44336" if issue.severity.value == "error" else "#FF9800"
                    html += f"""
                    <li>
                        <strong style="color: {color};">{movie.name}:</strong>
                        {issue.message}
                    </li>
                    """
                    issue_count += 1
                if issue_count >= 10:
                    break

            html += "</ul></div>"

        html += """
            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                This report was generated automatically by Media Audit.
                See attached files for complete details.
            </p>
        </body>
        </html>
        """

        return html

    def attach_file(self, msg: MIMEMultipart, file_path: Path) -> None:
        """Attach file to email message."""
        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())

        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {file_path.name}'
        )

        msg.attach(part)

# Usage
email_generator = EmailReportGenerator(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-password"
)

email_generator.send_report_email(
    scan_results,
    recipients=["admin@example.com", "user@example.com"],
    html_report_path=Path("audit.html"),
    json_report_path=Path("audit.json")
)
```

## Best Practices

### Report Design

1. **User Experience**: Design reports for easy navigation and understanding
2. **Performance**: Optimize HTML/CSS for fast loading and responsive design
3. **Accessibility**: Include proper semantic HTML and ARIA labels
4. **Mobile Support**: Ensure reports work well on mobile devices

### Data Handling

1. **Large Libraries**: Implement pagination for very large media collections
2. **Memory Management**: Stream large datasets rather than loading all in memory
3. **File Paths**: Handle long paths and special characters properly
4. **Internationalization**: Support Unicode characters in file names

### Integration

1. **API Design**: Design report formats for easy integration with other tools
2. **Standards Compliance**: Use standard formats (JSON, XML, CSV) properly
3. **Versioning**: Version report schemas for backward compatibility
4. **Documentation**: Document report formats and integration patterns

### Security

1. **Path Disclosure**: Avoid exposing sensitive path information
2. **XSS Prevention**: Sanitize any user-provided content in HTML reports
3. **File Permissions**: Set appropriate permissions on generated reports
4. **Credential Management**: Securely handle email/API credentials
