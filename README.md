# Media Audit 📺

A comprehensive CLI tool for auditing media libraries with beautiful HTML reports. Validates movies and TV shows for proper folder structure, required assets (posters, backgrounds, trailers), and modern video encoding standards.

## Features

- 🎬 **Movie Validation**
  - Checks for poster, background/fanart, and trailer files
  - Validates folder structure: `Movies/Title (YYYY)/`
  - Detects multiple poster/background variants

- 📺 **TV Show Validation**
  - Series-level: poster, background, optional banner
  - Season-level: season posters (SeasonXX.jpg)
  - Episode-level: video files and title cards
  - Smart episode detection (S01E01, 1x01 formats)

- 🎥 **Video Encoding Checks**
  - Validates modern codecs (HEVC/H.265, AV1)
  - Flags legacy H.264 content for re-encoding
  - Uses ffprobe for accurate codec detection

- 📊 **Beautiful Reports**
  - Interactive HTML with search/sort/filter
  - Responsive design with fixed header
  - JSON export for automation
  - Auto-opens in browser

- 🔧 **Flexible Configuration**
  - YAML-based configuration
  - Multiple media server profiles (Plex, Jellyfin, Emby)
  - Customizable file patterns
  - Concurrent scanning support

## Installation

### Using uv (Recommended)

```bash
# Install for development
uv pip install -e .

# Install as a tool
uv tool install media-audit
```

### Using pipx

```bash
pipx install media-audit
```

### Using pip

```bash
pip install media-audit
```

## Quick Start

```bash
# Basic scan with HTML report
media-audit scan --roots "D:\Media" --report report.html --open

# Scan multiple roots with specific profiles
media-audit scan \
  --roots "D:\Movies" "E:\TV Shows" \
  --profiles plex jellyfin \
  --report audit.html \
  --json audit.json \
  --open

# Show only problems in report
media-audit scan --roots /media --problems-only --report issues.html

# Use custom configuration file
media-audit scan --config config.yaml
```

## Configuration

Create a configuration file for repeated use:

```bash
# Generate sample config
media-audit init-config config.yaml
```

Example `config.yaml`:

```yaml
scan:
  root_paths:
    - D:/Media/Movies
    - D:/Media/TV Shows
  profiles:
    - plex
    - jellyfin
  allowed_codecs:
    - hevc
    - av1
  concurrent_workers: 4
  cache_enabled: true

report:
  output_path: media-audit.html
  json_path: media-audit.json
  auto_open: true
  problems_only: false
```

## Expected Structure

### Movies
```
Movies/
├── The Matrix (1999)/
│   ├── The Matrix (1999).mkv
│   ├── poster.jpg
│   ├── fanart.jpg
│   └── The Matrix (1999)-trailer.mp4
└── Inception (2010)/
    ├── Inception (2010).mkv
    ├── folder.jpg
    ├── backdrop.jpg
    └── Trailers/
        └── trailer1.mp4
```

### TV Shows
```
TV Shows/
└── Breaking Bad/
    ├── poster.jpg
    ├── fanart.jpg
    ├── banner.jpg
    ├── Season01.jpg
    └── Season 01/
        ├── S01E01.mkv
        ├── S01E01.jpg
        ├── S01E02.mkv
        └── S01E02.jpg
```

## Media Server Profiles

The tool includes preset patterns for popular media servers:

- **Plex**: `poster.jpg`, `fanart.jpg`, `*-trailer.mp4`
- **Jellyfin**: `folder.jpg`, `backdrop.jpg`, `*.trailer.mp4`
- **Emby**: `folder.jpg`, `backdrop.jpg`, `extrafanart/`

## Command Options

```bash
media-audit scan [OPTIONS]

Options:
  -r, --roots PATH           Root directories to scan (multiple)
  -p, --profiles TEXT        Media server profiles (plex/jellyfin/emby/all)
  -o, --report PATH          HTML report output path
  -j, --json PATH            JSON report output path
  -O, --open                 Open HTML report after generation
  --allow-codecs TEXT        Allowed video codecs
  --include TEXT             Include patterns for scanning
  --exclude TEXT             Exclude patterns for scanning
  --config PATH              Configuration file path
  -w, --workers INTEGER      Number of concurrent workers (default: 4)
  --no-cache                 Disable caching
  --problems-only            Show only items with problems
```

## Requirements

- Python 3.13+
- ffmpeg/ffprobe (for video analysis)

## Development

```bash
# Clone repository
git clone https://github.com/beelzer/media-audit.git
cd media-audit

# Install with dev dependencies
uv pip install -e .[dev]

# Set up pre-commit hooks
pre-commit install
pre-commit run --all-files  # Run on all files once

# Run tests
pytest tests/

# Run linting
ruff check src tests

# Run type checking
mypy src

# Format code
ruff format src tests
```

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. The hooks will run automatically on `git commit`. Included checks:

- Code formatting with ruff
- Linting and style checks
- Type checking with mypy
- Security scanning with bandit
- Secret detection
- YAML/JSON formatting
- Python 3.13+ syntax upgrades

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
