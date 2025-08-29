# Configuration

Media Audit can be configured through command-line arguments or YAML configuration files. This guide covers all available configuration options.

## Configuration File

Create a YAML configuration file to save your preferred settings:

```yaml
# config.yaml
# Media Audit Configuration

scan:
  # Root directories to scan
  root_paths:
    - /media/Movies
    - /media/TVShows

  # Media server profiles (plex, jellyfin, emby, all)
  profiles:
    - plex
    - jellyfin

  # Allowed video codecs (HEVC, H265, AV1, H264, etc.)
  allowed_codecs:
    - HEVC
    - H265
    - AV1

  # Include patterns (glob patterns)
  include_patterns:
    - "*.mkv"
    - "*.mp4"

  # Exclude patterns (glob patterns)
  exclude_patterns:
    - "*sample*"
    - "*trailer*"

  # Number of concurrent workers for scanning
  concurrent_workers: 4

  # Enable/disable caching
  cache_enabled: true

  # Cache directory (optional, defaults to ~/.cache/media-audit)
  cache_dir: ~/.cache/media-audit

report:
  # HTML report output path
  output_path: ./media-audit-report.html

  # JSON report output path (optional)
  json_path: ./media-audit-report.json

  # Auto-open HTML report after generation
  auto_open: true

  # Show thumbnails in report
  show_thumbnails: true

  # Only show items with problems
  problems_only: false
```

## Command-Line Options

All configuration options can be overridden via command-line arguments:

```bash
media-audit scan [OPTIONS]
```

### Basic Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--verbose` | `-v` | Enable verbose logging | False |
| `--debug` | | Enable debug logging | False |
| `--log-file` | | Log output to file | None |
| `--config` | `-c` | Configuration file path | None |
| `--help` | | Show help message | - |

### Scanning Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--roots` | `-r` | Root directories to scan (multiple) | Current dir |
| `--profiles` | `-p` | Media server profiles (plex, jellyfin, emby, all) | all |
| `--allow-codecs` | | Allowed video codecs | hevc, h265, av1 |
| `--include` | | Include patterns for scanning | All files |
| `--exclude` | | Exclude patterns for scanning | None |
| `--patterns` | | Custom patterns YAML file | None |
| `--workers` | `-w` | Number of concurrent workers | 4 |
| `--no-cache` | | Disable caching | False |

### Report Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--report` | `-o` | Report output path (HTML format) | `media-audit-report.html` |
| `--json` | `-j` | JSON report output path | None |
| `--open` | `-O` | Open HTML report after generation | False |
| `--problems-only` | | Show only items with problems | False |

## Using Configuration Files

### Load Configuration

```bash
# Use a specific configuration file
media-audit scan --config config.yaml

# Override configuration file settings
media-audit scan --config config.yaml --workers 8 --no-cache
```

### Generate Sample Configuration

```bash
# Generate a sample configuration file
media-audit init-config

# Generate with custom path
media-audit init-config --output my-config.yaml
```

## Configuration Examples

### Basic Movie Library Scan

```yaml
scan:
  root_paths:
    - /media/Movies
  profiles:
    - plex
  allowed_codecs:
    - HEVC
    - H264

report:
  output_path: movies-report.html
  auto_open: true
```

### TV Shows with Jellyfin

```yaml
scan:
  root_paths:
    - /media/TVShows
  profiles:
    - jellyfin
  exclude_patterns:
    - "*sample*"
    - "*.nfo"
    - "*.jpg"

report:
  output_path: tv-report.html
  problems_only: true
```

### Multi-Library Scan

```yaml
scan:
  root_paths:
    - /media/Movies
    - /media/TVShows
    - /media/Documentaries
  profiles:
    - all
  concurrent_workers: 8
  cache_enabled: true

report:
  output_path: full-library-report.html
  json_path: full-library-report.json
```

### Quick Scan (No Cache)

```yaml
scan:
  root_paths:
    - /media
  concurrent_workers: 16
  cache_enabled: false

report:
  problems_only: true
```

## Command-Line Examples

### Scan with Multiple Roots

```bash
media-audit scan -r /media/Movies -r /media/TVShows -o report.html
```

### Scan with Specific Profiles

```bash
media-audit scan -p plex -p jellyfin --report plex-jellyfin.html
```

### Scan with Custom Codecs

```bash
media-audit scan --allow-codecs H264 --allow-codecs HEVC
```

### Full Scan with All Options

```bash
media-audit scan \
  --roots /media/Movies \
  --roots /media/TVShows \
  --profiles plex \
  --allow-codecs HEVC \
  --allow-codecs AV1 \
  --workers 8 \
  --report report.html \
  --json report.json \
  --open \
  --verbose
```

## Environment Variables

While not directly supported, you can use shell features to set defaults:

```bash
# Create an alias with your preferred settings
alias media-scan='media-audit scan --config ~/.config/media-audit/default.yaml'

# Or create a shell function
media_scan() {
  media-audit scan \
    --roots "${MEDIA_PATH:-/media}" \
    --workers "${SCAN_WORKERS:-4}" \
    "$@"
}
```

## Configuration Precedence

When using both configuration files and command-line arguments:

1. Command-line arguments take precedence
2. Configuration file values are used as defaults
3. Built-in defaults apply if neither is specified

Example:

```bash
# config.yaml sets workers: 4
# Command uses --workers 8
media-audit scan --config config.yaml --workers 8
# Result: workers = 8 (command-line wins)
```

## Best Practices

### 1. Use Configuration Files for Repeated Scans

Create a configuration file for your common use cases:

```bash
media-audit init-config
# Edit the generated config.yaml
media-audit scan --config config.yaml
```

### 2. Enable Caching for Large Libraries

Caching significantly improves performance for repeated scans:

```yaml
scan:
  cache_enabled: true
```

### 3. Adjust Workers Based on Storage

- **SSD**: 4-8 workers
- **HDD**: 2-4 workers
- **Network**: 1-2 workers

### 4. Use Profiles for Media Servers

Match your media server's organization:

```yaml
scan:
  profiles:
    - plex  # For Plex media server
    # - jellyfin  # For Jellyfin
    # - emby  # For Emby
```

### 5. Filter Unnecessary Files

Exclude non-media files to speed up scanning:

```yaml
scan:
  exclude_patterns:
    - "*.nfo"
    - "*.jpg"
    - "*.png"
    - "*sample*"
    - "*trailer*"
```

## Troubleshooting

### View Configuration

Check what configuration is being used:

```bash
media-audit scan --config config.yaml --verbose
```

### Invalid Configuration

If your configuration file has errors:

```bash
# Validate YAML syntax
python -m yaml config.yaml

# Check with verbose output
media-audit scan --config config.yaml --debug
```

### Performance Issues

If scanning is slow:

1. Reduce workers for network/slow storage
2. Enable caching
3. Exclude unnecessary files
4. Use `--problems-only` for faster reports

## Next Steps

- Learn about [Basic Usage](../user-guide/usage.md)
- Understand [Media Patterns](../user-guide/patterns.md)
- Customize [Reports](../user-guide/reports.md)
