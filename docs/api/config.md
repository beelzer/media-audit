# Configuration API Reference

This reference documents the configuration system for Media Audit, including all configuration options, file formats, and programmatic access patterns.

## Configuration Structure

Media Audit uses YAML configuration files with the following top-level sections:

```yaml
scan:          # Scanning and validation options
  # ...
report:        # Report generation options
  # ...
```

## Scan Configuration

The `scan` section controls media discovery, validation, and processing behavior.

### `root_paths`

**Type**: `list[str]`
**Required**: Yes
**Description**: List of root directories to scan for media content.

```yaml
scan:
  root_paths:
    - "/mnt/movies"
    - "/mnt/tv-shows"
    - "D:\\Media\\Movies"    # Windows paths
    - "\\\\nas\\media"       # UNC paths
```

**Validation**:

- All paths must exist and be readable directories
- Relative paths are resolved from configuration file location
- Environment variables are expanded: `"${HOME}/media"`

**Examples**:

```yaml
# Unix/Linux paths
root_paths:
  - "/media/movies"
  - "/media/tv"
  - "/media/anime"

# Windows paths
root_paths:
  - "D:/Movies"
  - "E:/TV Shows"
  - "F:/Anime"

# Mixed environments
root_paths:
  - "/mnt/movies"      # Linux mount
  - "\\\\server\\tv"   # Windows share
```

### `profiles`

**Type**: `list[str]`
**Default**: `["all"]`
**Description**: Media server profiles to use for pattern matching.

```yaml
scan:
  profiles:
    - "plex"
    - "jellyfin"
    - "emby"
```

**Valid Values**:

- `"plex"` - Plex Media Server patterns
- `"jellyfin"` - Jellyfin patterns
- `"emby"` - Emby patterns
- `"all"` - Combined patterns from all servers

**Behavior**:

- Multiple profiles are merged (union of patterns)
- Order doesn't matter
- `"all"` is equivalent to `["plex", "jellyfin", "emby"]`

### `allowed_codecs`

**Type**: `list[str]`
**Default**: `["hevc", "h265", "av1"]`
**Description**: List of acceptable video codecs.

```yaml
scan:
  allowed_codecs:
    - "hevc"
    - "h265"
    - "av1"
    - "h264"    # Include if H.264 is acceptable
```

**Valid Values**:

- `"hevc"` / `"h265"` - High Efficiency Video Codec
- `"av1"` - AOMedia Video 1
- `"h264"` - H.264/AVC (typically flagged for re-encoding)
- `"vp9"` - VP9
- `"mpeg4"` - MPEG-4
- `"mpeg2"` - MPEG-2
- `"other"` - Any unrecognized codec

**Notes**:

- Case insensitive matching
- Videos with non-allowed codecs generate warnings
- H.264 generates additional re-encoding recommendations

### `include_patterns` and `exclude_patterns`

**Type**: `list[str]`
**Default**: `[]` (empty)
**Description**: Glob patterns for file inclusion/exclusion.

```yaml
scan:
  include_patterns:
    - "*.mkv"
    - "*.mp4"
    - "*.m4v"
  exclude_patterns:
    - "*.sample.*"
    - "*trailer*"
    - "*/extras/*"
    - "*/deleted/*"
    - ".*"              # Hidden files
```

**Pattern Syntax**:

- Standard Unix glob patterns
- `*` matches any characters except path separator
- `**` matches any characters including path separator
- `?` matches single character
- `[abc]` matches any character in brackets
- `{a,b,c}` matches any of the comma-separated patterns

**Processing Order**:

1. Include patterns applied first (if any)
2. Exclude patterns applied to included files
3. Empty include list means include all files

### `concurrent_workers`

**Type**: `int`
**Default**: `4`
**Range**: `1-32`
**Description**: Number of concurrent workers for parallel processing.

```yaml
scan:
  concurrent_workers: 8
```

**Performance Guidelines**:

- **Low-end systems**: 2-4 workers
- **Mid-range systems**: 4-8 workers
- **High-end systems**: 8-16 workers
- **Network storage**: Reduce workers to minimize network load
- **SSD storage**: Can handle more workers than HDD

**Resource Impact**:

- Each worker consumes ~50-100MB RAM
- Higher worker count increases CPU usage
- Network storage may have optimal worker count < CPU cores

### `cache_enabled`

**Type**: `bool`
**Default**: `true`
**Description**: Enable/disable caching system.

```yaml
scan:
  cache_enabled: true
```

**Behavior**:

- `true`: Enable caching for faster subsequent scans
- `false`: Disable caching, always perform fresh analysis

**When to Disable**:

- First-time scans of new libraries
- Troubleshooting scan issues
- Testing configuration changes
- Ensuring completely fresh results

### `cache_dir`

**Type**: `str`
**Default**: `"~/.cache/media-audit"`
**Description**: Directory for cache storage.

```yaml
scan:
  cache_dir: "/fast/ssd/cache"
```

**Recommendations**:

- Use fastest available storage (SSD preferred)
- Ensure sufficient free space (1-5GB for large libraries)
- Use local storage for network-attached media
- Consider separate cache per environment

**Path Expansion**:

- `~` expands to user home directory
- Environment variables are expanded
- Relative paths resolved from config file location

### `patterns`

**Type**: `object`
**Description**: Custom pattern definitions for asset matching.

```yaml
scan:
  patterns:
    poster_patterns:
      - "^poster\\."
      - "^folder\\."
      - "^cover\\."
    background_patterns:
      - "^fanart\\."
      - "^backdrop\\."
    banner_patterns:
      - "^banner\\."
    trailer_patterns:
      - "-trailer\\."
      - "^trailers/.*"
    title_card_patterns:
      - "^S\\d{2}E\\d{2}\\."
```

**Pattern Types**:

- `poster_patterns`: Movie/series poster images
- `background_patterns`: Fanart/backdrop images
- `banner_patterns`: Series banner images
- `trailer_patterns`: Trailer video files
- `title_card_patterns`: Episode thumbnail images

**Pattern Syntax**:

- Python regex patterns (case insensitive)
- Use `\\` to escape special characters
- `^` anchors to start of filename
- `$` anchors to end of filename
- `.*` matches any characters

## Report Configuration

The `report` section controls report generation and output formatting.

### `output_path`

**Type**: `str`
**Description**: Path for HTML report output.

```yaml
report:
  output_path: "audit-report.html"
```

**Path Handling**:

- Relative paths resolved from current working directory
- Parent directories created automatically
- File extension should be `.html`

### `json_path`

**Type**: `str`
**Description**: Path for JSON report output.

```yaml
report:
  json_path: "audit-data.json"
```

**JSON Structure**:

- Machine-readable format
- Complete scan results
- Suitable for automation and integration

### `auto_open`

**Type**: `bool`
**Default**: `false`
**Description**: Automatically open HTML report in browser.

```yaml
report:
  auto_open: true
```

**Behavior**:

- Opens report in default system browser
- Only applies to HTML reports
- Useful for interactive usage

### `show_thumbnails`

**Type**: `bool`
**Default**: `true`
**Description**: Include thumbnail images in HTML reports.

```yaml
report:
  show_thumbnails: false
```

**Impact**:

- `true`: Shows poster thumbnails when available
- `false`: Text-only report (faster generation)
- Thumbnails are Base64 encoded in HTML

### `problems_only`

**Type**: `bool`
**Default**: `false`
**Description**: Show only items with validation issues.

```yaml
report:
  problems_only: true
```

**Filtering**:

- `true`: Only items with errors or warnings
- `false`: All scanned items regardless of status
- Reduces report size for large clean libraries

## Configuration Loading

### File Discovery

Configuration files are loaded in the following order:

1. **Explicit path** (`--config` option)
2. **Environment variable** (`MEDIA_AUDIT_CONFIG`)
3. **Current directory** (`./config.yaml`)
4. **User config directory** (`~/.config/media-audit/config.yaml`)
5. **System config directory** (`/etc/media-audit/config.yaml`)

### Environment Variable Expansion

Configuration values support environment variable expansion:

```yaml
scan:
  root_paths:
    - "${MEDIA_ROOT}/movies"
    - "${MEDIA_ROOT}/tv"
  cache_dir: "${TEMP_DIR}/media-audit-cache"

report:
  output_path: "${REPORT_DIR}/audit-${DATE}.html"
```

**Supported Formats**:

- `${VAR}` - Standard format
- `${VAR:-default}` - With default value
- `$VAR` - Shell-style (less recommended)

### Configuration Validation

All configuration is validated on load:

```python
# Example validation errors
ValidationError: scan.root_paths is required
ValidationError: scan.concurrent_workers must be between 1 and 32
ValidationError: scan.allowed_codecs contains invalid codec 'invalid'
ValidationError: report.output_path directory is not writable
```

## Programmatic Configuration

### Python API

```python
from media_audit.config import Config, ScanConfig, ReportConfig
from pathlib import Path

# Create configuration programmatically
config = Config(
    scan=ScanConfig(
        root_paths=[Path("/media/movies"), Path("/media/tv")],
        profiles=["plex", "jellyfin"],
        allowed_codecs=[CodecType.HEVC, CodecType.AV1],
        concurrent_workers=8,
        cache_enabled=True
    ),
    report=ReportConfig(
        output_path=Path("reports/audit.html"),
        json_path=Path("reports/audit.json"),
        auto_open=False,
        problems_only=True
    )
)

# Save configuration
config.save(Path("config.yaml"))

# Load configuration
config = Config.from_file(Path("config.yaml"))

# Load from dictionary
config_dict = {
    "scan": {
        "root_paths": ["/media"],
        "profiles": ["plex"]
    }
}
config = Config.from_dict(config_dict)
```

### Configuration Merging

```python
# Load base configuration
base_config = Config.from_file("base-config.yaml")

# Override specific values
overrides = {
    "scan": {
        "concurrent_workers": 16,
        "problems_only": True
    }
}

# Merge configurations
merged_config = base_config.merge(overrides)
```

### Dynamic Configuration

```python
import os
from media_audit.config import Config

def create_dynamic_config():
    """Create configuration based on runtime conditions."""

    # Detect available CPU cores
    worker_count = min(os.cpu_count() or 4, 16)

    # Check available storage
    import shutil
    free_space = shutil.disk_usage("/").free
    cache_enabled = free_space > 10 * 1024**3  # Enable if >10GB free

    # Environment-specific paths
    if os.name == 'nt':  # Windows
        root_paths = ["D:/Movies", "E:/TV Shows"]
        cache_dir = os.path.expandvars("${APPDATA}/media-audit")
    else:  # Unix-like
        root_paths = ["/mnt/movies", "/mnt/tv"]
        cache_dir = os.path.expanduser("~/.cache/media-audit")

    config = Config(
        scan=ScanConfig(
            root_paths=[Path(p) for p in root_paths],
            concurrent_workers=worker_count,
            cache_enabled=cache_enabled,
            cache_dir=Path(cache_dir)
        )
    )

    return config
```

## Configuration Examples

### Development Configuration

```yaml
# dev-config.yaml
scan:
  root_paths:
    - "./test-media"
  profiles: ["all"]
  allowed_codecs: ["hevc", "h265", "av1", "h264"]  # Allow H.264 for testing
  concurrent_workers: 2
  cache_enabled: false  # Fresh scans for testing

report:
  output_path: "dev-audit.html"
  json_path: "dev-audit.json"
  auto_open: true
  problems_only: false  # Show all items during development
```

### Production Configuration

```yaml
# prod-config.yaml
scan:
  root_paths:
    - "/mnt/movies-4k"
    - "/mnt/movies-hd"
    - "/mnt/tv-shows"
  profiles: ["plex", "jellyfin"]
  allowed_codecs: ["hevc", "av1"]  # Strict codec requirements
  concurrent_workers: 16
  cache_enabled: true
  cache_dir: "/nvme/cache/media-audit"
  exclude_patterns:
    - "*.sample.*"
    - "*trailer*"
    - "*/extras/*"

report:
  output_path: "/reports/daily-audit.html"
  json_path: "/reports/daily-audit.json"
  auto_open: false
  problems_only: true  # Focus on issues
  show_thumbnails: false  # Faster generation
```

### CI/CD Configuration

```yaml
# ci-config.yaml
scan:
  root_paths:
    - "${MEDIA_ROOT}"  # From environment
  profiles: ["all"]
  allowed_codecs: ["hevc", "av1"]
  concurrent_workers: 4  # Conservative for shared runners
  cache_enabled: false  # Fresh validation every run
  include_patterns:
    - "*.mkv"
    - "*.mp4"
  exclude_patterns:
    - "*.sample.*"
    - "*/temp/*"

report:
  output_path: "validation-report.html"
  json_path: "validation-results.json"
  auto_open: false
  problems_only: true
  show_thumbnails: false
```

### Multi-Environment Configuration

```yaml
# multi-env-config.yaml
scan:
  root_paths:
    # Production paths
    - "/mnt/prod/movies"
    - "/mnt/prod/tv"
    # Staging paths
    - "/mnt/staging/movies"
    - "/mnt/staging/tv"
    # Development paths
    - "/home/dev/test-media"

  profiles: ["plex", "jellyfin"]
  allowed_codecs: ["hevc", "av1", "h264"]  # Mixed tolerance
  concurrent_workers: 8
  cache_enabled: true
  cache_dir: "/tmp/media-audit-cache"  # Shared cache

report:
  output_path: "multi-env-audit.html"
  json_path: "multi-env-audit.json"
  problems_only: false
  show_thumbnails: true
```

## Configuration Validation

### Schema Definition

```python
# Configuration schema (internal)
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "scan": {
            "type": "object",
            "properties": {
                "root_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1
                },
                "profiles": {
                    "type": "array",
                    "items": {"enum": ["plex", "jellyfin", "emby", "all"]}
                },
                "allowed_codecs": {
                    "type": "array",
                    "items": {"enum": ["hevc", "h265", "av1", "h264", "vp9", "mpeg4", "mpeg2", "other"]}
                },
                "concurrent_workers": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 32
                },
                "cache_enabled": {"type": "boolean"}
            },
            "required": ["root_paths"]
        },
        "report": {
            "type": "object",
            "properties": {
                "auto_open": {"type": "boolean"},
                "show_thumbnails": {"type": "boolean"},
                "problems_only": {"type": "boolean"}
            }
        }
    },
    "required": ["scan"]
}
```

### Validation Examples

```yaml
# Valid configuration
scan:
  root_paths: ["/media"]  # ✓ Required field present
  concurrent_workers: 8   # ✓ Within valid range

# Invalid configurations
scan:
  root_paths: []          # ✗ Empty array not allowed
  concurrent_workers: 0   # ✗ Below minimum value
  profiles: ["invalid"]   # ✗ Invalid profile name
```

### Custom Validation

```python
from media_audit.config import Config, ValidationError

class CustomConfig(Config):
    """Configuration with additional validation."""

    def validate(self):
        """Perform custom validation."""
        super().validate()

        # Custom validation rules
        if self.scan.concurrent_workers > os.cpu_count():
            raise ValidationError(
                f"concurrent_workers ({self.scan.concurrent_workers}) exceeds CPU count ({os.cpu_count()})"
            )

        # Validate cache directory
        if self.scan.cache_enabled and self.scan.cache_dir:
            if not self.scan.cache_dir.parent.exists():
                raise ValidationError(f"Cache directory parent does not exist: {self.scan.cache_dir.parent}")
```

## Best Practices

### Configuration Organization

1. **Environment-Specific Configs**: Separate configs for dev/staging/prod
2. **Base Configuration**: Common settings in base config, override specifics
3. **Version Control**: Store configs in version control (exclude secrets)
4. **Documentation**: Comment complex configurations

### Performance Tuning

1. **Worker Count**: Start with CPU cores × 1.5, adjust based on testing
2. **Cache Location**: Use fastest storage for cache directory
3. **Pattern Optimization**: Specific patterns perform better than broad ones
4. **Exclusion Patterns**: Exclude unnecessary files to improve scan speed

### Security Considerations

1. **Path Validation**: Ensure all paths are trusted and accessible
2. **Environment Variables**: Be cautious with sensitive values in env vars
3. **File Permissions**: Validate config file permissions in production
4. **Cache Security**: Protect cache directory from unauthorized access

### Maintenance

1. **Regular Review**: Review configurations for outdated settings
2. **Performance Monitoring**: Monitor scan times and adjust workers accordingly
3. **Cache Management**: Periodically clear cache for schema updates
4. **Validation Testing**: Test configurations in non-production environments
