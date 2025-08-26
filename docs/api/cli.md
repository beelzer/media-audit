# CLI API Reference

This reference documents the command-line interface for Media Audit, including all commands, options, and usage patterns.

## Command Structure

```bash
media-audit [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS]
```

## Global Options

### Version and Help

```bash
--version                   # Show version and exit
--help                      # Show help message
```

## Commands

### `scan`

Primary command for scanning media libraries and generating validation reports.

```bash
media-audit scan [OPTIONS]
```

#### Core Options

##### `--roots` / `-r`

Specify root directories to scan. Can be used multiple times.

```bash
--roots PATH [PATH ...]
-r PATH [PATH ...]

# Examples
--roots "D:\Movies"
--roots "D:\Movies" "E:\TV Shows" "F:\Anime"
-r /mnt/movies -r /mnt/tv
```

**Details:**

- **Type**: Path (string)
- **Multiple**: Yes
- **Required**: Yes (unless specified in config)
- **Validation**: Must exist and be readable directories

##### `--config` / `-c`

Path to YAML configuration file.

```bash
--config PATH
-c PATH

# Examples
--config config.yaml
-c /etc/media-audit/production.yaml
```

**Details:**

- **Type**: Path to existing file
- **Default**: None
- **Validation**: File must exist and be valid YAML

##### `--report` / `-o`

Output path for HTML report.

```bash
--report PATH
-o PATH

# Examples
--report audit.html
-o /reports/daily-audit.html
```

**Details:**

- **Type**: Path (string)
- **Default**: None (no HTML report generated)
- **Directory Creation**: Parent directories created automatically

##### `--json` / `-j`

Output path for JSON report.

```bash
--json PATH
-j PATH

# Examples
--json audit.json
-j /reports/audit.json
```

**Details:**

- **Type**: Path (string)
- **Default**: None (no JSON report generated)
- **Format**: Structured JSON data suitable for automation

##### `--open` / `-O`

Auto-open HTML report in default browser after generation.

```bash
--open
-O
```

**Details:**

- **Type**: Flag (boolean)
- **Default**: False
- **Requires**: HTML report path (`--report`)

#### Media Server Options

##### `--profiles` / `-p`

Media server profiles to use for pattern matching.

```bash
--profiles PROFILE [PROFILE ...]
-p PROFILE [PROFILE ...]

# Examples
--profiles plex
--profiles plex jellyfin emby
-p all
```

**Details:**

- **Type**: String choices
- **Choices**: `plex`, `jellyfin`, `emby`, `all`
- **Multiple**: Yes
- **Default**: `["all"]`

##### `--patterns`

Path to custom patterns YAML file.

```bash
--patterns PATH

# Example
--patterns custom-patterns.yaml
```

**Details:**

- **Type**: Path to existing file
- **Validation**: Must be valid YAML with pattern definitions

#### Video Codec Options

##### `--allow-codecs`

Specify allowed video codecs.

```bash
--allow-codecs CODEC [CODEC ...]

# Examples
--allow-codecs hevc av1
--allow-codecs hevc h265 av1 h264
```

**Details:**

- **Type**: String choices
- **Choices**: `hevc`, `h265`, `av1`, `h264`, `vp9`, `mpeg4`, `mpeg2`
- **Multiple**: Yes
- **Default**: `["hevc", "h265", "av1"]`
- **Case Insensitive**: Yes

#### Filtering Options

##### `--include`

Include patterns for file matching.

```bash
--include PATTERN [PATTERN ...]

# Examples
--include "*.mkv" "*.mp4"
--include "*/Season*/*" "*/Movies/*"
```

**Details:**

- **Type**: Glob patterns
- **Multiple**: Yes
- **Applied**: Before scanning begins

##### `--exclude`

Exclude patterns for file matching.

```bash
--exclude PATTERN [PATTERN ...]

# Examples
--exclude "*.sample.*" "*trailer*"
--exclude "*/extras/*" "*/deleted/*"
```

**Details:**

- **Type**: Glob patterns
- **Multiple**: Yes
- **Applied**: After include patterns

##### `--problems-only`

Show only items with validation issues in reports.

```bash
--problems-only
```

**Details:**

- **Type**: Flag (boolean)
- **Default**: False
- **Effect**: Filters report content, not scan process

#### Performance Options

##### `--workers` / `-w`

Number of concurrent workers for parallel processing.

```bash
--workers INTEGER
-w INTEGER

# Examples
--workers 8
-w 4
```

**Details:**

- **Type**: Integer
- **Default**: 4
- **Range**: 1-32 (practical limit)
- **Recommendation**: CPU cores × 1.5

##### `--no-cache`

Disable caching system for fresh scan.

```bash
--no-cache
```

**Details:**

- **Type**: Flag (boolean)
- **Default**: False (caching enabled)
- **Effect**: Forces re-analysis of all files

#### Complete Example

```bash
media-audit scan \
  --roots "/mnt/movies" "/mnt/tv" "/mnt/anime" \
  --profiles plex jellyfin \
  --allow-codecs hevc av1 \
  --include "*.mkv" "*.mp4" \
  --exclude "*.sample.*" "*trailer*" \
  --workers 8 \
  --report full-audit.html \
  --json full-audit.json \
  --problems-only \
  --open
```

### `init-config`

Generate a sample configuration file.

```bash
media-audit init-config OUTPUT_PATH
```

#### Arguments

##### `OUTPUT_PATH`

Path where the configuration file will be created.

```bash
media-audit init-config config.yaml
media-audit init-config /etc/media-audit/config.yaml
```

**Details:**

- **Type**: Path (string)
- **Required**: Yes
- **Validation**: Parent directory must be writable
- **Overwrites**: Existing files without confirmation

#### Generated Configuration

The command generates a complete configuration file with:

```yaml
scan:
  root_paths:
    - D:/Media
    - E:/Media
  profiles:
    - plex
    - jellyfin
  allowed_codecs:
    - hevc
    - av1
  concurrent_workers: 4
  cache_enabled: true

report:
  output_path: report.html
  json_path: report.json
  auto_open: true
  show_thumbnails: true
  problems_only: false
```

#### Example

```bash
# Generate default configuration
media-audit init-config my-config.yaml

# Output
✓ Created sample configuration at my-config.yaml

Edit this file to customize your scan settings.
```

## Exit Codes

Media Audit uses standard Unix exit codes:

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Scan completed with no validation issues |
| 1 | Issues Found | Scan completed but validation issues were found |
| 2 | Usage Error | Command line arguments are invalid |
| 3 | Configuration Error | Configuration file is invalid or missing |
| 4 | Permission Error | Insufficient permissions for specified paths |
| 5 | Resource Error | Insufficient disk space or memory |

### Exit Code Examples

```bash
# Success - no issues
media-audit scan --roots /media && echo "Clean library!"

# Issues found - exit code 1
media-audit scan --roots /media || echo "Issues detected"

# Handle different exit codes
media-audit scan --roots /media
case $? in
  0) echo "✓ Library is clean" ;;
  1) echo "⚠ Issues found, check report" ;;
  2) echo "✗ Invalid command line options" ;;
  3) echo "✗ Configuration error" ;;
  *) echo "✗ Unexpected error" ;;
esac
```

## Environment Variables

### Configuration

#### `MEDIA_AUDIT_CONFIG`

Default configuration file path.

```bash
export MEDIA_AUDIT_CONFIG=/etc/media-audit/config.yaml
media-audit scan  # Uses config from environment variable
```

#### `MEDIA_AUDIT_CACHE_DIR`

Override default cache directory.

```bash
export MEDIA_AUDIT_CACHE_DIR=/fast/cache
media-audit scan --roots /media
```

#### `MEDIA_AUDIT_WORKERS`

Default number of workers.

```bash
export MEDIA_AUDIT_WORKERS=8
media-audit scan --roots /media  # Uses 8 workers by default
```

### Debugging

#### `MEDIA_AUDIT_DEBUG`

Enable debug logging.

```bash
export MEDIA_AUDIT_DEBUG=1
media-audit scan --roots /media  # Shows detailed logging
```

#### `MEDIA_AUDIT_VERBOSE`

Enable verbose output.

```bash
export MEDIA_AUDIT_VERBOSE=1
media-audit scan --roots /media
```

### Integration

#### `MEDIA_AUDIT_NO_COLOR`

Disable colored output (useful for CI/CD).

```bash
export MEDIA_AUDIT_NO_COLOR=1
media-audit scan --roots /media  # Plain text output
```

#### `MEDIA_AUDIT_BATCH_MODE`

Enable batch mode (no interactive prompts).

```bash
export MEDIA_AUDIT_BATCH_MODE=1
media-audit scan --roots /media
```

## Output Format

### Console Output

#### Progress Display

```text
📺 Media Audit Scanner

Scanning 2 root path(s)...

⠋ Discovering media in /mnt/movies... (Press ESC to cancel)
⠋ Movies: 150/150 - The Matrix (1999)
⠋ TV Series: 45/45 - Breaking Bad

┏━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Category      ┃ Count  ┃
┡━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Total Items   │    195 │
│ Movies        │    150 │
│ TV Series     │     45 │
│ Total Issues  │     23 │
│ Errors        │     12 │
│ Warnings      │     11 │
│ Scan Duration │  45.2s │
└───────────────┴────────┘

Sample Issues Found:

The Matrix (1999) (/mnt/movies/The Matrix (1999))
  ▸ Missing background/fanart image
  ▸ Video uses non-preferred codec: h264

Cache: 850 hits, 150 misses (85.0% hit rate)

✓ Generated HTML report: audit.html
✓ Generated JSON report: audit.json
```

#### Error Display

```text
✗ Error: No root paths specified. Use --roots or provide a config file.

✗ Error: Root path does not exist: /nonexistent/path

⚠ Warning: Unknown codec 'invalid', skipping

⚠ Warning: FFprobe not found, video analysis disabled
```

### Interactive Features

#### Keyboard Controls

- **ESC**: Cancel running scan
- **Ctrl+C**: Force quit (emergency stop)

#### Progress Indicators

- Spinner for discovery phase
- Progress bars for processing phases
- Real-time item counts and names

### Report Generation Messages

```text
Generating HTML report: audit.html
Generating JSON report: audit.json
```

## Scripting Examples

### Basic Automation

```bash
#!/bin/bash
# daily-audit.sh - Daily media library audit

MEDIA_ROOTS=("/mnt/movies" "/mnt/tv")
REPORT_DIR="/reports"
DATE=$(date +%Y%m%d)

media-audit scan \
  --roots "${MEDIA_ROOTS[@]}" \
  --report "$REPORT_DIR/audit-$DATE.html" \
  --json "$REPORT_DIR/audit-$DATE.json" \
  --problems-only

if [ $? -eq 1 ]; then
  echo "Issues found, sending notification..."
  # Send notification logic here
fi
```

### Advanced Scripting

```bash
#!/bin/bash
# conditional-audit.sh - Conditional auditing based on library changes

LIBRARY_PATH="/mnt/media"
CHECKSUM_FILE="$HOME/.media-audit-checksum"
CURRENT_CHECKSUM=$(find "$LIBRARY_PATH" -type f -name "*.mkv" -o -name "*.mp4" | xargs ls -la | sha256sum)

# Check if library has changed
if [ -f "$CHECKSUM_FILE" ]; then
  PREVIOUS_CHECKSUM=$(cat "$CHECKSUM_FILE")
  if [ "$CURRENT_CHECKSUM" = "$PREVIOUS_CHECKSUM" ]; then
    echo "No changes detected, skipping audit"
    exit 0
  fi
fi

echo "Library changes detected, running audit..."

# Run audit
media-audit scan \
  --roots "$LIBRARY_PATH" \
  --report "audit.html" \
  --json "audit.json"

# Update checksum
echo "$CURRENT_CHECKSUM" > "$CHECKSUM_FILE"
```

### PowerShell Examples

```powershell
# Windows PowerShell script
param(
    [string[]]$MediaRoots = @("D:\Movies", "D:\TV Shows"),
    [string]$ReportPath = "audit.html",
    [switch]$ProblemsOnly
)

$arguments = @("scan")
$MediaRoots | ForEach-Object { $arguments += "--roots"; $arguments += $_ }
$arguments += "--report", $ReportPath

if ($ProblemsOnly) {
    $arguments += "--problems-only"
}

# Run media-audit
$result = & media-audit $arguments

# Check exit code
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Media library is clean" -ForegroundColor Green
} elseif ($LASTEXITCODE -eq 1) {
    Write-Host "⚠ Issues found in media library" -ForegroundColor Yellow
    if (Test-Path $ReportPath) {
        Start-Process $ReportPath
    }
} else {
    Write-Host "✗ Scan failed with exit code $LASTEXITCODE" -ForegroundColor Red
}
```

## Configuration Integration

### Command Line Priority

Configuration sources in order of priority (highest to lowest):

1. **Command line arguments**
2. **Environment variables**
3. **Configuration file (`--config`)**
4. **Default configuration file** (`MEDIA_AUDIT_CONFIG`)
5. **Built-in defaults**

### Example Override Behavior

```yaml
# config.yaml
scan:
  concurrent_workers: 4
  profiles: ['plex']
```

```bash
# Command overrides config
media-audit scan \
  --config config.yaml \
  --workers 8 \           # Overrides config (4 → 8)
  --profiles jellyfin \   # Overrides config (plex → jellyfin)
  --roots /media          # Required (not in config)

# Result: 8 workers, jellyfin profile, /media root
```

## Error Handling

### Common Error Scenarios

#### Invalid Configuration

```bash
media-audit scan --config invalid.yaml
# Output: Error: Configuration file contains invalid YAML syntax
# Exit Code: 3
```

#### Permission Issues

```bash
media-audit scan --roots /protected/directory
# Output: Error: Permission denied accessing /protected/directory
# Exit Code: 4
```

#### Missing Dependencies

```bash
# When ffprobe is not available
media-audit scan --roots /media
# Output: Warning: FFprobe not found, video analysis disabled
# Continues with limited functionality
```

#### Disk Space Issues

```bash
media-audit scan --roots /media --report /full/disk/report.html
# Output: Error: Insufficient disk space for report generation
# Exit Code: 5
```

### Recovery Strategies

#### Graceful Degradation

- Missing FFprobe: Skip video analysis but continue with asset validation
- Cache issues: Disable cache and continue with direct scanning
- Permission errors: Skip inaccessible directories but process others

#### Error Messages

All error messages include:

- Clear description of the problem
- Suggested resolution steps
- Relevant file paths or configuration keys
- Links to documentation when applicable

## Integration Patterns

### CI/CD Integration

```yaml
# GitHub Actions
- name: Validate Media Library
  run: |
    media-audit scan \
      --roots /media \
      --json validation.json \
      --problems-only
  continue-on-error: true

- name: Process Results
  run: |
    if [ $? -eq 1 ]; then
      echo "validation_failed=true" >> $GITHUB_OUTPUT
      echo "Issues found in media library"
    fi
```

### Monitoring Integration

```bash
# Prometheus monitoring
ISSUES=$(media-audit scan --roots /media --json /tmp/audit.json >/dev/null 2>&1; jq '.scan_info.total_issues' /tmp/audit.json)
echo "media_audit_issues_total $ISSUES" | curl -X POST --data-binary @- http://pushgateway:9091/metrics/job/media_audit
```

### Backup Integration

```bash
# Run audit before backup
media-audit scan --roots /media --problems-only --json pre-backup-audit.json
if [ $? -eq 0 ]; then
  echo "Media library validated, starting backup..."
  # Backup commands here
else
  echo "Media library has issues, review before backup"
  exit 1
fi
```
