# Usage Guide

This comprehensive guide covers all aspects of using Media Audit to scan and validate your media library.

## Basic Usage

### Quick Start

The simplest way to run Media Audit is with basic command-line arguments:

```bash
# Scan a single directory and generate HTML report
media-audit scan --roots "D:\Movies" --report audit.html --open

# Scan multiple directories
media-audit scan --roots "D:\Movies" "E:\TV Shows" --report audit.html
```

### Using Configuration Files

For repeated scans or complex setups, use configuration files:

```bash
# Generate sample configuration
media-audit init-config config.yaml

# Run scan with configuration
media-audit scan --config config.yaml
```

## Command Line Options

### Core Options

| Option | Short | Description | Example |
|--------|-------|-------------|---------|
| `--roots` | `-r` | Root directories to scan (multiple allowed) | `--roots "D:\Movies" "E:\TV"` |
| `--config` | `-c` | Path to configuration file | `--config myconfig.yaml` |
| `--report` | `-o` | HTML report output path | `--report audit.html` |
| `--json` | `-j` | JSON report output path | `--json audit.json` |
| `--open` | `-O` | Auto-open HTML report in browser | `--open` |

### Media Server Profiles

```bash
# Use specific media server profiles
media-audit scan --roots "D:\Media" --profiles plex jellyfin

# Use all patterns (default)
media-audit scan --roots "D:\Media" --profiles all
```

Available profiles:
- `plex` - Plex Media Server patterns
- `jellyfin` - Jellyfin patterns  
- `emby` - Emby patterns
- `all` - Combined patterns from all servers

### Video Codec Options

```bash
# Allow specific codecs only
media-audit scan --roots "D:\Movies" --allow-codecs hevc av1

# Multiple codec specification
media-audit scan --roots "D:\Movies" --allow-codecs hevc h265 av1
```

Supported codecs:
- `hevc` / `h265` - High Efficiency Video Codec
- `av1` - AOMedia Video 1
- `h264` - H.264/AVC (flagged for re-encoding)
- `vp9` - VP9
- `mpeg4` - MPEG-4
- `mpeg2` - MPEG-2

### Performance Options

```bash
# Control concurrent processing
media-audit scan --roots "D:\Media" --workers 8

# Disable caching for fresh scan
media-audit scan --roots "D:\Media" --no-cache
```

### Filtering Options

```bash
# Show only items with problems
media-audit scan --roots "D:\Media" --problems-only --report issues.html

# Include/exclude patterns
media-audit scan --roots "D:\Media" \
  --include "*.mkv" "*.mp4" \
  --exclude "*.sample.*" "*trailer*"
```

## Directory Structure Requirements

### Movies

Media Audit expects movies to follow this structure:

```
Movies/
├── The Matrix (1999)/
│   ├── The Matrix (1999).mkv          # Main video file
│   ├── poster.jpg                     # Movie poster
│   ├── fanart.jpg                     # Background image
│   └── The Matrix (1999)-trailer.mp4  # Trailer (optional)
└── Inception (2010)/
    ├── Inception (2010).mkv
    ├── folder.jpg                     # Alternative poster name
    ├── backdrop.jpg                   # Alternative background name
    └── Trailers/                      # Alternative trailer location
        └── trailer1.mp4
```

**Key Requirements:**
- Movie folder format: `Title (Year)/`
- Video file should match folder name
- At least one poster file (poster.jpg, folder.jpg, movie.jpg, etc.)
- At least one background file (fanart.jpg, background.jpg, backdrop.jpg, etc.)
- Trailers are optional but recommended

### TV Shows

TV shows require more complex structure:

```
TV Shows/
└── Breaking Bad/
    ├── poster.jpg                     # Series poster
    ├── fanart.jpg                     # Series background
    ├── banner.jpg                     # Series banner (optional)
    ├── Season01.jpg                   # Season 1 poster
    ├── Season02.jpg                   # Season 2 poster
    ├── Season 01/                     # Season folder
    │   ├── S01E01.mkv                 # Episode video
    │   ├── S01E01.jpg                 # Episode title card
    │   ├── S01E02.mkv
    │   └── S01E02.jpg
    └── Season 02/
        ├── S02E01.mkv
        ├── S02E01.jpg
        ├── S02E02.mkv
        └── S02E02.jpg
```

**Key Requirements:**
- Series-level: poster, background (banner optional)
- Season posters: `SeasonXX.jpg` format
- Episode naming: `S01E01.mkv` format
- Episode title cards: matching episode filename with .jpg extension

## Advanced Usage Examples

### Complex Multi-Root Scan

```bash
media-audit scan \
  --roots "/mnt/movies" "/mnt/tv" "/mnt/anime" \
  --profiles plex jellyfin \
  --allow-codecs hevc av1 \
  --workers 6 \
  --report full-audit.html \
  --json full-audit.json \
  --open
```

### Focused Problem Detection

```bash
# Find only encoding issues
media-audit scan \
  --roots "D:\Media" \
  --allow-codecs hevc av1 \
  --problems-only \
  --report encoding-issues.html

# Find only missing assets
media-audit scan \
  --roots "D:\Media" \
  --allow-codecs h264 hevc av1 \  # Allow all codecs
  --problems-only \
  --report missing-assets.html
```

### Custom Pattern Matching

```bash
# Use custom patterns file
media-audit scan \
  --roots "D:\Media" \
  --patterns custom-patterns.yaml \
  --report custom-scan.html
```

Create `custom-patterns.yaml`:

```yaml
poster_patterns:
  - "^poster\\."
  - "^cover\\."
  - "^movie-poster\\."

background_patterns:
  - "^fanart\\."
  - "^background\\."
  - "^movie-fanart\\."

trailer_patterns:
  - "-trailer\\."
  - "^extras/trailers/.*"
```

## Output and Reports

### HTML Reports

The HTML report provides an interactive interface with:

- **Search and Filter**: Find specific movies/shows quickly
- **Sort Options**: Sort by name, status, issues count
- **Issue Categories**: Group by asset, encoding, or structure issues
- **Responsive Design**: Works on desktop and mobile
- **Auto-refresh**: Updates when you fix issues

### JSON Reports

JSON reports are perfect for automation and integration:

```bash
# Generate JSON for CI/CD pipeline
media-audit scan --roots "D:\Media" --json audit.json

# Parse results programmatically
python -c "
import json
with open('audit.json') as f:
    data = json.load(f)
    print(f'Total issues: {data[\"total_issues\"]}')
    print(f'Movies with issues: {len([m for m in data[\"movies\"] if m[\"issues\"]])}')
"
```

## Exit Codes

Media Audit uses standard exit codes for automation:

- `0` - Success (no issues found)
- `1` - Issues found (warnings or errors)
- `2` - Command line argument errors
- `3` - Configuration errors

Example usage in scripts:

```bash
#!/bin/bash
media-audit scan --roots "D:\Media" --problems-only --report issues.html

if [ $? -eq 0 ]; then
    echo "✓ No issues found!"
else
    echo "⚠ Issues detected. Check issues.html"
    open issues.html
fi
```

## Troubleshooting

### Common Issues

#### FFprobe Not Found
```bash
# Install ffmpeg on Ubuntu/Debian
sudo apt install ffmpeg

# Install on macOS with Homebrew
brew install ffmpeg

# Install on Windows with Chocolatey
choco install ffmpeg
```

#### Permission Errors
```bash
# Run with appropriate permissions
sudo media-audit scan --roots "/media"

# Or fix directory permissions
chmod -R 755 /path/to/media
```

#### Large Library Performance
```bash
# Increase workers for better performance
media-audit scan --roots "D:\Media" --workers 8

# Use caching for subsequent runs (default)
media-audit scan --roots "D:\Media"  # Uses cache

# Force fresh scan if needed
media-audit scan --roots "D:\Media" --no-cache
```

### Getting Help

```bash
# Show help for main command
media-audit --help

# Show help for scan command
media-audit scan --help

# Show version
media-audit --version
```

## Integration Examples

### CI/CD Pipeline

```yaml
# .github/workflows/media-validation.yml
name: Media Library Validation
on:
  schedule:
    - cron: '0 2 * * 0'  # Weekly on Sunday

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install media-audit
        run: pip install media-audit
      
      - name: Validate media library
        run: |
          media-audit scan \
            --roots "/media" \
            --json validation-results.json \
            --report validation-report.html
      
      - name: Upload reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: validation-reports
          path: |
            validation-results.json
            validation-report.html
```

### Cron Job

```bash
# Add to crontab for weekly validation
0 2 * * 0 /usr/local/bin/media-audit scan --roots /media --problems-only --report /var/log/media-issues.html
```

### Python Integration

```python
import subprocess
import json

def validate_media(path):
    """Run media validation and return results."""
    result = subprocess.run([
        'media-audit', 'scan',
        '--roots', path,
        '--json', 'results.json'
    ], capture_output=True, text=True)
    
    if result.returncode in [0, 1]:  # Success or issues found
        with open('results.json') as f:
            return json.load(f)
    else:
        raise Exception(f"Validation failed: {result.stderr}")

# Usage
results = validate_media('/path/to/media')
print(f"Found {results['total_issues']} issues")
```