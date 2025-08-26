# Configuration

Media Audit can be configured through command-line arguments, configuration files, or environment variables. This guide covers all configuration options.

## Configuration File

Create a YAML configuration file for complex setups:

```yaml
# config.yaml
# Media Audit Configuration

# Paths to scan (can be single path or list)
paths:
  - /media/Movies
  - /media/TVShows
  - /media/Documentaries

# File extensions to include
extensions:
  - .mkv
  - .mp4
  - .avi
  - .mov
  - .wmv
  - .flv
  - .webm

# Patterns to exclude (regex)
exclude_patterns:
  - ".*sample.*"
  - ".*trailer.*"
  - "^\\..*"  # Hidden files

# Output configuration
output:
  path: ./reports/media-audit.html
  format: html  # html or json
  overwrite: true
  open_after: true  # Auto-open report in browser

# Media type detection
media_type: auto  # auto, movie, tv, or mixed

# Validation settings
validation:
  enabled: true
  check_duplicates: true
  check_naming: true
  check_quality: true
  check_episodes: true  # For TV shows
  min_quality: 720p
  max_quality: 2160p
  required_audio_codec: null  # e.g., "aac", "ac3"
  required_video_codec: null  # e.g., "h264", "hevc"

# Performance settings
performance:
  workers: 4  # Number of parallel workers
  batch_size: 100  # Files per batch
  timeout: 30  # FFprobe timeout in seconds

# Cache configuration
cache:
  enabled: true
  path: ~/.cache/media-audit
  ttl: 604800  # Time-to-live in seconds (1 week)
  max_size: 1073741824  # Max cache size in bytes (1GB)

# Logging
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR
  file: null  # Log file path (null for stdout only)
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# FFprobe settings
ffprobe:
  enabled: true
  path: ffprobe  # Path to ffprobe binary
  options:
    - -v
    - quiet
    - -print_format
    - json
    - -show_format
    - -show_streams

# Report settings
report:
  title: "Media Library Audit Report"
  theme: default  # default, dark, or custom
  show_thumbnails: false
  include_metadata: true
  group_by: directory  # directory, media_type, quality, or none
```

## Command-Line Options

All configuration options can be overridden via command-line:

```bash
media-audit scan [OPTIONS] [PATHS]...
```

### Basic Options

| Option | Description | Default |
|--------|-------------|---------|
| `--output`, `-o` | Output file path | `media-audit-report.html` |
| `--format`, `-f` | Output format (HTML/JSON) | `html` |
| `--config`, `-c` | Configuration file path | None |
| `--verbose`, `-v` | Enable verbose output | False |
| `--quiet`, `-q` | Suppress all output | False |

### Scanning Options

| Option | Description | Default |
|--------|-------------|---------|
| `--recursive`, `-r` | Scan directories recursively | True |
| `--extensions`, `-e` | File extensions to include | All video |
| `--exclude` | Patterns to exclude | None |
| `--media-type` | Media type (auto/movie/tv) | `auto` |
| `--follow-symlinks` | Follow symbolic links | False |

### Validation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--validate` | Enable validation | True |
| `--check-duplicates` | Check for duplicate files | True |
| `--check-naming` | Validate naming conventions | True |
| `--check-quality` | Check video quality | True |
| `--min-quality` | Minimum acceptable quality | None |
| `--validate-episodes` | Check for missing TV episodes | True |

### Performance Options

| Option | Description | Default |
|--------|-------------|---------|
| `--workers`, `-w` | Number of parallel workers | 4 |
| `--no-probe` | Skip FFprobe analysis | False |
| `--cache` | Enable caching | True |
| `--cache-ttl` | Cache time-to-live (seconds) | 604800 |
| `--timeout` | FFprobe timeout (seconds) | 30 |

## Environment Variables

Configure Media Audit using environment variables:

```bash
# Set default configuration file
export MEDIA_AUDIT_CONFIG=/path/to/config.yaml

# Set default paths
export MEDIA_AUDIT_PATHS="/media/Movies:/media/TV"

# Set FFprobe path
export MEDIA_AUDIT_FFPROBE_PATH=/usr/local/bin/ffprobe

# Set cache directory
export MEDIA_AUDIT_CACHE_DIR=~/.cache/media-audit

# Set log level
export MEDIA_AUDIT_LOG_LEVEL=DEBUG
```

## Configuration Precedence

Configuration values are resolved in this order (highest to lowest priority):

1. Command-line arguments
2. Environment variables
3. Configuration file
4. Default values

Example:

```bash
# config.yaml sets workers: 4
# Environment sets MEDIA_AUDIT_WORKERS=8
# Command uses --workers 16

media-audit scan --config config.yaml --workers 16
# Result: workers = 16 (command-line wins)
```

## Profile-Based Configuration

Create multiple configuration profiles for different use cases:

### Quick Scan Profile

```yaml
# quick-scan.yaml
performance:
  workers: 8
ffprobe:
  enabled: false
validation:
  enabled: false
cache:
  enabled: true
```

### Deep Analysis Profile

```yaml
# deep-analysis.yaml
performance:
  workers: 2
  timeout: 60
ffprobe:
  enabled: true
validation:
  enabled: true
  check_duplicates: true
  check_naming: true
  check_quality: true
report:
  include_metadata: true
  show_thumbnails: true
```

### TV Show Profile

```yaml
# tv-shows.yaml
media_type: tv
validation:
  check_episodes: true
  check_naming: true
patterns:
  tv_show: "^(?P<show>[^/]+)/Season (?P<season>\\d+)/.*S(?P<s>\\d+)E(?P<e>\\d+)"
```

Use profiles:

```bash
media-audit scan --config quick-scan.yaml /media
media-audit scan --config deep-analysis.yaml /media
media-audit scan --config tv-shows.yaml "/media/TV Shows"
```

## Advanced Configuration

### Custom Validation Rules

```yaml
validation:
  custom_rules:
    - name: "4K Movies Must Be HEVC"
      condition: "quality == '2160p'"
      requirement: "video_codec == 'hevc'"
      severity: error

    - name: "HD Content Preferred Codecs"
      condition: "quality >= '1080p'"
      requirement: "video_codec in ['h264', 'hevc']"
      severity: warning

    - name: "Minimum Bitrate for 4K"
      condition: "quality == '2160p'"
      requirement: "video_bitrate >= 15000000"
      severity: warning
```

### Pattern Matching

```yaml
patterns:
  movie: "^(?P<title>.*?)\\s*\\((?P<year>\\d{4})\\)"
  tv_show: "^(?P<show>.*?)/S(?P<season>\\d{2})E(?P<episode>\\d{2})"
  quality: "(720p|1080p|2160p|4K)"
  source: "(BluRay|BRRip|WEB-DL|WEBRip|HDTV)"
```

### Report Customization

```yaml
report:
  custom_css: ./custom.css
  custom_template: ./template.html
  sections:
    - summary
    - issues
    - file_list
    - statistics
    - recommendations
  charts:
    - quality_distribution
    - codec_usage
    - file_sizes
    - bitrate_analysis
```

## Configuration Examples

### Minimal Configuration

```yaml
paths: /media
output:
  path: report.html
```

### Plex/Jellyfin Server

```yaml
paths:
  - /var/lib/plexmediaserver/Movies
  - /var/lib/plexmediaserver/TV Shows
validation:
  check_naming: true
  naming_pattern: "plex"  # Use Plex naming conventions
output:
  format: json
  path: /var/log/media-audit/report.json
```

### Archive Validation

```yaml
paths: /archives/media
validation:
  check_quality: true
  min_quality: 1080p
  required_video_codec: h264
  required_audio_codec: aac
performance:
  workers: 1  # Sequential for archives
cache:
  enabled: false  # Always fresh scan
```

## Best Practices

### 1. Use Configuration Files

For repeated scans, always use a configuration file:

```bash
media-audit scan --config ~/.config/media-audit/default.yaml
```

### 2. Enable Caching

For large libraries, caching significantly improves performance:

```yaml
cache:
  enabled: true
  ttl: 604800  # 1 week
```

### 3. Adjust Workers

Set workers based on your system:

- **SSD**: 4-8 workers
- **HDD**: 2-4 workers
- **Network**: 1-2 workers

### 4. Use Appropriate Timeouts

Adjust timeout for network or slow storage:

```yaml
performance:
  timeout: 60  # Increase for network storage
```

### 5. Validate Incrementally

For large libraries, validate in stages:

```bash
# First pass: Quick scan without probe
media-audit scan --no-probe /media

# Second pass: Validate structure
media-audit scan --no-ffprobe --validate /media

# Third pass: Full analysis
media-audit scan --config full-analysis.yaml /media
```

## Troubleshooting Configuration

### Debug Configuration Loading

```bash
media-audit scan --config config.yaml --verbose
```

### Validate Configuration

```bash
media-audit config validate --config config.yaml
```

### Show Effective Configuration

```bash
media-audit config show --config config.yaml --env
```

## Next Steps

- Explore [Basic Usage](../user-guide/usage.md)
- Learn about [Patterns](../user-guide/patterns.md)
- Customize [Reports](../user-guide/reports.md)
