# Media Audit 📺

[![CI](https://github.com/beelzer/media-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/beelzer/media-audit/actions/workflows/ci.yml)
[![Docs](https://github.com/beelzer/media-audit/actions/workflows/docs.yml/badge.svg)](https://github.com/beelzer/media-audit/actions/workflows/docs.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](http://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/badge/uv-managed-blue)](https://github.com/astral-sh/uv)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

A comprehensive CLI tool for auditing media libraries with beautiful HTML reports. Validates movies and TV shows for proper folder structure, required assets (posters, backgrounds, trailers), and modern video encoding standards.

## ✨ Features

### 🎬 **Movie Validation**

- Checks for poster, background/fanart, and trailer files
- Validates folder structure: `Movies/Title (YYYY)/`
- Detects multiple poster/background variants
- Supports collection organization

### 📺 **TV Show Validation**

- **Series-level**: poster, background, optional banner
- **Season-level**: season posters (SeasonXX.jpg)
- **Episode-level**: video files and title cards
- Smart episode detection (S01E01, 1x01 formats)

### 🎥 **Video Encoding Checks**

- Validates modern codecs (HEVC/H.265, AV1)
- Flags legacy H.264 content for re-encoding
- Uses FFprobe for accurate codec detection
- Detailed bitrate and resolution analysis

### 📊 **Beautiful Reports**

- Interactive HTML with search/sort/filter
- Responsive design with fixed header
- JSON export for automation
- Auto-opens in browser
- Summary statistics dashboard

### 🔧 **Flexible Configuration**

- YAML-based configuration
- Multiple media server profiles (Plex, Jellyfin, Emby)
- Customizable file patterns
- Concurrent scanning support
- Smart caching for faster scans

## 📦 Installation

### Using uv (Recommended)

```bash
# Install as a tool (recommended)
uv tool install media-audit

# Or install in current environment
uv pip install media-audit
```

### Using pipx

```bash
pipx install media-audit
```

### Using pip

```bash
pip install media-audit
```

### From Source

```bash
# Clone repository
git clone https://github.com/beelzer/media-audit.git
cd media-audit

# Install with uv
uv pip install -e .

# Or with pip
pip install -e .
```

## 🚀 Quick Start

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

## ⚙️ Configuration

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
  include_patterns:
    - "*.mkv"
    - "*.mp4"
  exclude_patterns:
    - "*sample*"
    - "*.txt"

report:
  output_path: media-audit.html
  json_path: media-audit.json
  auto_open: true
  problems_only: false
  include_summary: true
```

## 📁 Expected Structure

### Movies

```text
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

```text
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

## 🎯 Media Server Profiles

The tool includes preset patterns for popular media servers:

| Server | Poster | Background | Trailer | Notes |
|--------|--------|------------|---------|-------|
| **Plex** | `poster.jpg` | `fanart.jpg` | `*-trailer.mp4` | Also supports `folder.jpg` |
| **Jellyfin** | `folder.jpg` | `backdrop.jpg` | `*.trailer.mp4` | Flexible naming |
| **Emby** | `folder.jpg` | `backdrop.jpg` | in `Trailers/` | Supports `extrafanart/` |

## 📋 Command Reference

### Scan Command

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
  --verbose                  Enable verbose output
  --help                     Show this message and exit
```

### Init Config Command

```bash
media-audit init-config [OPTIONS] OUTPUT_PATH

Options:
  --full                     Generate full config with all options
  --help                     Show this message and exit
```

## 🛠️ Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/beelzer/media-audit.git
cd media-audit

# Install with dev dependencies using uv
uv sync --all-extras

# Set up pre-commit hooks
pre-commit install
pre-commit run --all-files  # Run on all files once
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/media_audit --cov-report=html

# Run specific test file
pytest tests/test_scanner.py

# Run with verbose output
pytest tests/ -v
```

### Code Quality

```bash
# Run linting
ruff check src tests

# Run formatting
ruff format src tests

# Run type checking
mypy src

# Run security checks
bandit -r src

# Run all pre-commit hooks
pre-commit run --all-files
```

### Pre-commit Hooks

This project uses pre-commit hooks to ensure code quality. The hooks will run automatically on `git commit`. Included checks:

- ✅ Code formatting with ruff
- ✅ Linting and style checks
- ✅ Type checking with mypy
- ✅ Security scanning with bandit
- ✅ Secret detection
- ✅ YAML/JSON formatting
- ✅ Python 3.13+ syntax upgrades
- ✅ Markdown linting
- ✅ Spell checking

### Building Documentation

```bash
# Install docs dependencies
uv sync --extra docs

# Serve docs locally
uv run mkdocs serve

# Build static docs
uv run mkdocs build
```

## 📋 Requirements

- **Python**: 3.13 or higher
- **FFmpeg/FFprobe**: Required for video analysis
  - Windows: `winget install FFmpeg` or download from [FFmpeg.org](https://ffmpeg.org)
  - macOS: `brew install ffmpeg`
  - Linux: `apt install ffmpeg` or `yum install ffmpeg`

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please ensure:

- All tests pass (`pytest tests/`)
- Pre-commit hooks pass (`pre-commit run --all-files`)
- Code is properly typed (mypy checks pass)
- Documentation is updated if needed

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Typer](https://typer.tiangolo.com/) for the CLI interface
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [Jinja2](https://jinja.palletsprojects.com/) for HTML report generation
- [FFmpeg](https://ffmpeg.org/) for video analysis

## 📞 Support

- **Documentation**: [GitHub Pages](https://beelzer.github.io/media-audit/)
- **Repository**: [GitHub](https://github.com/beelzer/media-audit)

---

Made with ❤️ for the media server community
