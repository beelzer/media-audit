# Report Formats

Media Audit generates comprehensive reports in both HTML and JSON formats. This guide covers report features, customization options, and how to interpret the results.

## HTML Reports

### Overview

The HTML report provides an interactive, user-friendly interface for reviewing your media library audit results.

```bash
# Generate HTML report
media-audit scan --roots "D:\Media" --report audit.html --open

# Problems-only report
media-audit scan --roots "D:\Media" --problems-only --report issues.html
```

### Features

#### Interactive Interface

- **Search Bar**: Find specific movies or TV shows quickly
- **Filter Options**: Show/hide different types of issues
- **Sort Controls**: Sort by name, status, or issue count
- **Responsive Design**: Works on desktop, tablet, and mobile devices

#### Visual Elements

- **Status Indicators**: Color-coded icons for validation status
- **Issue Categorization**: Group issues by type (assets, encoding, structure)
- **Progress Bars**: Visual representation of library health
- **Thumbnails**: Poster images when available

#### Navigation

- **Fixed Header**: Always visible controls while scrolling
- **Jump to Top**: Quick navigation for long reports
- **Collapsible Sections**: Expand/collapse detailed information

### Report Sections

#### Summary Dashboard

```html
<!-- Generated summary section -->
<div class="summary-card">
  <h2>Scan Summary</h2>
  <div class="stats-grid">
    <div class="stat">
      <span class="number">150</span>
      <span class="label">Movies</span>
    </div>
    <div class="stat">
      <span class="number">45</span>
      <span class="label">TV Series</span>
    </div>
    <div class="stat error">
      <span class="number">23</span>
      <span class="label">Errors</span>
    </div>
    <div class="stat warning">
      <span class="number">67</span>
      <span class="label">Warnings</span>
    </div>
  </div>
</div>
```

#### Movies Section

- **Movie Cards**: Each movie displayed as a card with poster (if available)
- **Issue Lists**: Detailed breakdown of each validation issue
- **File Information**: Video codec, resolution, file size
- **Asset Status**: Visual indicators for posters, backgrounds, trailers

#### TV Shows Section

- **Series Overview**: Series-level information and issues
- **Season Breakdown**: Each season with its specific issues
- **Episode Details**: Individual episode validation results
- **Hierarchical Display**: Nested structure showing series → seasons → episodes

### Customization Options

#### Report Configuration

```yaml
# config.yaml
report:
  output_path: custom-report.html
  auto_open: true
  show_thumbnails: true
  problems_only: false
```

#### CSS Customization

The HTML report includes embedded CSS that can be customized:

```html
<!-- Custom styles can be added -->
<style>
.custom-theme {
  --primary-color: #your-color;
  --error-color: #your-error-color;
  --warning-color: #your-warning-color;
}
</style>
```

## JSON Reports

### Overview

JSON reports provide structured data perfect for automation, integration, and programmatic analysis.

```bash
# Generate JSON report
media-audit scan --roots "D:\Media" --json audit.json

# Both HTML and JSON
media-audit scan --roots "D:\Media" --report audit.html --json audit.json
```

### JSON Structure

#### Root Schema

```json
{
  "scan_info": {
    "scan_time": "2025-01-15T10:30:00Z",
    "duration": 45.2,
    "root_paths": ["/path/to/movies", "/path/to/tv"],
    "total_items": 195,
    "total_issues": 90,
    "errors": []
  },
  "movies": [...],
  "series": [...],
  "statistics": {
    "movies_count": 150,
    "series_count": 45,
    "total_episodes": 1250,
    "error_count": 23,
    "warning_count": 67
  }
}
```

#### Movie Entry Schema

```json
{
  "name": "The Matrix",
  "path": "/movies/The Matrix (1999)",
  "year": 1999,
  "type": "movie",
  "status": "error",
  "assets": {
    "posters": ["/movies/The Matrix (1999)/poster.jpg"],
    "backgrounds": [],
    "trailers": ["/movies/The Matrix (1999)/trailer.mp4"]
  },
  "video_info": {
    "path": "/movies/The Matrix (1999)/The Matrix (1999).mkv",
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
```

#### TV Series Schema

```json
{
  "name": "Breaking Bad",
  "path": "/tv/Breaking Bad",
  "type": "tv_series",
  "status": "warning",
  "total_episodes": 62,
  "assets": {
    "posters": ["/tv/Breaking Bad/poster.jpg"],
    "backgrounds": ["/tv/Breaking Bad/fanart.jpg"],
    "banners": []
  },
  "seasons": [
    {
      "season_number": 1,
      "name": "Season 1",
      "path": "/tv/Breaking Bad/Season 01",
      "type": "tv_season",
      "status": "valid",
      "assets": {
        "posters": ["/tv/Breaking Bad/Season01.jpg"]
      },
      "episodes": [
        {
          "season_number": 1,
          "episode_number": 1,
          "name": "Pilot",
          "path": "/tv/Breaking Bad/Season 01/S01E01.mkv",
          "type": "tv_episode",
          "status": "valid",
          "video_info": {...},
          "assets": {
            "title_cards": ["/tv/Breaking Bad/Season 01/S01E01.jpg"]
          },
          "issues": []
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
      "details": {"expected": ["banner.jpg"]}
    }
  ]
}
```

### Data Analysis Examples

#### Python Analysis

```python
import json

def analyze_report(json_path):
    """Analyze JSON report data."""
    with open(json_path) as f:
        data = json.load(f)

    # Basic statistics
    print(f"Total items: {data['scan_info']['total_items']}")
    print(f"Total issues: {data['scan_info']['total_issues']}")

    # Issue breakdown
    error_count = sum(1 for movie in data['movies']
                     for issue in movie['issues']
                     if issue['severity'] == 'error')
    print(f"Error count: {error_count}")

    # Missing assets analysis
    missing_posters = [movie['name'] for movie in data['movies']
                      if not movie['assets']['posters']]
    print(f"Movies missing posters: {len(missing_posters)}")

    # Codec analysis
    codecs = {}
    for movie in data['movies']:
        if movie['video_info'] and movie['video_info']['codec']:
            codec = movie['video_info']['codec']
            codecs[codec] = codecs.get(codec, 0) + 1
    print(f"Codec distribution: {codecs}")

# Usage
analyze_report('audit.json')
```

#### PowerShell Analysis

```powershell
# Load and analyze JSON report
$report = Get-Content audit.json | ConvertFrom-Json

# Summary statistics
Write-Host "Movies: $($report.movies.Count)"
Write-Host "TV Series: $($report.series.Count)"
Write-Host "Total Issues: $($report.scan_info.total_issues)"

# Find movies with H.264 codec
$h264Movies = $report.movies | Where-Object {
    $_.video_info.codec -eq "h264"
} | Select-Object name, path

Write-Host "Movies with H.264 codec:"
$h264Movies | Format-Table -AutoSize

# Export problem items
$problemItems = $report.movies | Where-Object { $_.issues.Count -gt 0 }
$problemItems | Export-Csv -Path "problem-movies.csv" -NoTypeInformation
```

#### Bash/jq Analysis

```bash
#!/bin/bash
# Analyze JSON report using jq

JSON_FILE="audit.json"

# Basic stats
echo "=== Scan Summary ==="
jq -r '.scan_info | "Duration: \(.duration)s\nTotal Items: \(.total_items)\nTotal Issues: \(.total_issues)"' $JSON_FILE

# Movies by codec
echo -e "\n=== Codec Distribution ==="
jq -r '.movies[] | select(.video_info != null) | .video_info.codec' $JSON_FILE | sort | uniq -c | sort -nr

# Movies missing posters
echo -e "\n=== Movies Missing Posters ==="
jq -r '.movies[] | select(.assets.posters | length == 0) | .name' $JSON_FILE

# Series with most issues
echo -e "\n=== Series with Most Issues ==="
jq -r '.series[] | "\(.issues | length) \(.name)"' $JSON_FILE | sort -nr | head -5

# Export H.264 movies for re-encoding
echo -e "\n=== Exporting H.264 Movies ==="
jq -r '.movies[] | select(.video_info.codec == "h264") | .video_info.path' $JSON_FILE > h264-files.txt
echo "H.264 files saved to h264-files.txt"
```

## Report Interpretation

### Status Indicators

#### Valid Status

- ✅ **Green**: All requirements met
- No validation issues found
- Assets present and codec approved

#### Warning Status

- ⚠️ **Yellow**: Minor issues that don't break functionality
- Missing optional assets (trailers, banners, title cards)
- Non-preferred but acceptable codecs

#### Error Status

- ❌ **Red**: Critical issues requiring attention
- Missing required assets (posters, backgrounds)
- No video files found
- Severe structural problems

### Issue Categories

#### Assets Issues

- **Missing Poster**: No poster/folder image found
- **Missing Background**: No fanart/backdrop image found
- **Missing Trailer**: No trailer video found (warning)
- **Missing Banner**: No banner image found (TV shows, warning)
- **Missing Title Card**: No episode thumbnail found (warning)

#### Encoding Issues

- **Non-preferred Codec**: Video uses H.264 instead of HEVC/AV1
- **Re-encoding Recommended**: Suggests modern codec for better compression
- **Probe Failed**: Unable to analyze video file

#### Structure Issues

- **Invalid Directory Name**: Folder doesn't match expected pattern
- **Missing Video File**: No video content found
- **Unexpected Files**: Files that don't match any pattern

### Severity Levels

#### Error Severity

- **Impact**: Breaks media server functionality
- **Examples**: Missing posters, no video files
- **Action**: Must be fixed for proper operation

#### Warning Severity

- **Impact**: Reduces user experience quality
- **Examples**: Missing trailers, H.264 codec
- **Action**: Should be fixed when convenient

## Advanced Report Features

### Custom Filtering

#### Configuration-Based Filtering

```yaml
# config.yaml
report:
  problems_only: true
  min_severity: warning  # Only show warnings and errors
  exclude_categories:
    - encoding          # Skip codec warnings
  include_categories:
    - assets           # Only show asset issues
```

#### Runtime Filtering

```bash
# Show only movies with issues
media-audit scan --roots "D:\Movies" --problems-only --report movie-issues.html

# Combined with other filters
media-audit scan \
  --roots "D:\Movies" \
  --allow-codecs h264 hevc av1 \  # Allow H.264 to focus on assets
  --problems-only \
  --report asset-issues.html
```

### Report Comparison

#### Generate Baseline

```bash
# Create baseline report
media-audit scan --roots "D:\Media" --json baseline.json

# After fixes, create new report
media-audit scan --roots "D:\Media" --json current.json
```

#### Compare Reports

```python
# compare-reports.py
import json

def compare_reports(baseline_path, current_path):
    """Compare two audit reports."""
    with open(baseline_path) as f:
        baseline = json.load(f)
    with open(current_path) as f:
        current = json.load(f)

    baseline_issues = baseline['scan_info']['total_issues']
    current_issues = current['scan_info']['total_issues']

    print(f"Baseline issues: {baseline_issues}")
    print(f"Current issues: {current_issues}")
    print(f"Improvement: {baseline_issues - current_issues} issues resolved")

    # Detailed comparison
    baseline_movies = {m['name']: len(m['issues']) for m in baseline['movies']}
    current_movies = {m['name']: len(m['issues']) for m in current['movies']}

    for movie, issues in baseline_movies.items():
        current_issues = current_movies.get(movie, 0)
        if issues > current_issues:
            print(f"✓ {movie}: {issues - current_issues} issues resolved")

compare_reports('baseline.json', 'current.json')
```

### Integration with External Tools

#### Media Server Integration

```python
# plex-integration.py
import json
import requests

def sync_with_plex(json_report, plex_url, plex_token):
    """Sync audit results with Plex."""
    with open(json_report) as f:
        data = json.load(f)

    # Find items missing posters
    missing_posters = []
    for movie in data['movies']:
        if not movie['assets']['posters']:
            missing_posters.append({
                'title': movie['name'],
                'path': movie['path'],
                'year': movie.get('year')
            })

    # Trigger Plex metadata refresh for these items
    for item in missing_posters:
        refresh_plex_metadata(item, plex_url, plex_token)

def refresh_plex_metadata(item, plex_url, token):
    """Trigger Plex metadata refresh."""
    # Implementation depends on Plex API
    pass
```

#### Automation Scripts

```bash
#!/bin/bash
# automated-fix.sh - Fix common issues automatically

JSON_REPORT="audit.json"

# Extract movies missing trailers
jq -r '.movies[] | select(.assets.trailers | length == 0) | .path' $JSON_REPORT | while read movie_path; do
    echo "Searching for trailer: $movie_path"
    # Search for trailers online or in separate directory
    find /trailers -name "*$(basename "$movie_path")*trailer*" -exec cp {} "$movie_path/" \;
done

# Extract H.264 files for batch re-encoding
jq -r '.movies[] | select(.video_info.codec == "h264") | .video_info.path' $JSON_REPORT > encode-queue.txt

echo "H.264 files ready for re-encoding saved to encode-queue.txt"
```

## Best Practices

### Report Generation

1. **Regular Scheduling**: Generate reports weekly or after media additions
2. **Version Control**: Keep historical reports for trend analysis
3. **Multiple Formats**: Generate both HTML (for review) and JSON (for automation)
4. **Focused Reports**: Use --problems-only for issue resolution

### Report Review

1. **Prioritize Errors**: Fix critical issues (missing posters) first
2. **Batch Similar Issues**: Fix all missing backgrounds together
3. **Track Progress**: Compare reports over time to measure improvement
4. **Document Changes**: Note what fixes were applied

### Automation

1. **CI/CD Integration**: Include media validation in deployment pipelines
2. **Monitoring**: Set up alerts when issue counts exceed thresholds
3. **Automatic Fixes**: Automate resolution of simple issues
4. **Regular Validation**: Schedule periodic scans to catch new issues

### Performance

1. **Incremental Scans**: Use caching for large libraries
2. **Targeted Scans**: Scan specific directories when troubleshooting
3. **Resource Management**: Adjust worker count based on system resources
4. **Report Size**: Use problems-only for large libraries to reduce report size
