# Media Audit 📺

[![CI](https://github.com/beelzer/media-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/beelzer/media-audit/actions/workflows/ci.yml)
[![Docs](https://github.com/beelzer/media-audit/actions/workflows/docs.yml/badge.svg)](https://github.com/beelzer/media-audit/actions/workflows/docs.yml)
[![codecov](https://codecov.io/gh/beelzer/media-audit/graph/badge.svg)](https://codecov.io/gh/beelzer/media-audit)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![Style: Ruff](https://img.shields.io/badge/Style-Ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](http://mypy-lang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/badge/uv-managed-blue)](https://github.com/astral-sh/uv)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

A powerful CLI tool for auditing and validating media libraries. Scans your media collection, extracts metadata using FFprobe, validates file integrity and modern video encoding standards, and generates beautiful HTML or JSON reports.

## ✨ Features

### 🎬 **Smart Media Detection**

- Automatic parsing of movie and TV show filenames
- Pattern matching for various naming conventions
- Season/Episode detection for TV shows
- Quality detection (720p, 1080p, 4K, etc.)
- Source detection (BluRay, WEB-DL, HDTV, etc.)

### 📺 **Media Server Support**

- **Plex**: Full pattern support for Plex Media Server
- **Jellyfin**: Compatible with Jellyfin organization
- **Emby**: Supports Emby folder structures
- Custom patterns via YAML configuration

### 🎥 **Deep Media Analysis**

- FFprobe integration for technical metadata extraction
- Video codec detection (H.264, H.265/HEVC, AV1, etc.)
- Audio codec detection (AAC, AC3, DTS, TrueHD, etc.)
- Resolution and bitrate analysis
- Duration and file size tracking
- Subtitle stream detection

### 📊 **Beautiful Reports**

- Interactive HTML with search/sort/filter
- Responsive design with modern UI
- JSON export for automation
- Auto-open in browser option
- Summary statistics dashboard
- Problems-only view for quick issue identification

### 🔧 **Flexible Configuration**

- YAML-based configuration
- Multiple media server profiles (Plex, Jellyfin, Emby)
- Customizable file patterns
- Concurrent scanning support
- Smart caching for faster scans

## 🖥️ Platform Support

Media-audit runs on all major platforms:

- **Windows**: Windows 10/11 (x64)
- **macOS**: Intel and Apple Silicon (M1/M2/M3)
- **Linux**: x86_64 and ARM64 (including Raspberry Pi)

### ARM Architecture Support

Full native support for ARM-based systems:

- Apple Silicon Macs (M1/M2/M3)
- Raspberry Pi 4/5
- AWS Graviton instances
- Other ARM64/ARMv7 Linux devices

See [ARM Setup Guide](docs/getting-started/arm-setup.md) for platform-specific instructions.

## 📦 Installation

### System Requirements

- Python 3.13 or higher
- FFmpeg/FFprobe (for media analysis)
- 2GB+ RAM recommended
- 100MB disk space for application

### From Source (Currently Required)

> **Note**: Package is not yet published to PyPI. Please install from source for now.

```bash
# Clone repository
git clone https://github.com/beelzer/media-audit.git
cd media-audit

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

### Future Installation (Once Published)

```bash
# Will be available via uv
uv tool install media-audit

# Or via pipx
pipx install media-audit
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
media-audit scan -r /media --report report.html --open

# Scan multiple roots with specific profiles
media-audit scan \
  -r /movies -r /tvshows \
  -p plex -p jellyfin \
  --report audit.html \
  --json audit.json \
  --open

# Show only problems in report
media-audit scan -r /media --problems-only --report issues.html

# Use custom configuration file
media-audit scan --config config.yaml
```

## ⚙️ Configuration

Create a configuration file for repeated use:

```bash
# Generate sample config
media-audit init-config
```

Example `config.yaml`:

```yaml
scan:
  root_paths:
    - /media/Movies
    - /media/TVShows
  profiles:
    - plex
    - jellyfin
  allowed_codecs:
    - HEVC
    - H265
    - AV1
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
  show_thumbnails: true
```

## 📁 Supported Media Structures

### Movies

```text
Movies/
├── The Matrix (1999)/
│   └── The Matrix (1999).mkv
├── Inception (2010)/
│   └── Inception (2010) - 1080p BluRay.mkv
└── Collections/
    └── Marvel/
        └── Iron Man (2008).mkv
```

### TV Shows

```text
TV Shows/
└── Breaking Bad/
    ├── Season 01/
    │   ├── S01E01 - Pilot.mkv
    │   ├── S01E02 - Cat's in the Bag.mkv
    │   └── Breaking Bad - S01E03.mkv
    └── Season 02/
        ├── Breaking Bad - 2x01.mkv
        └── Breaking Bad - 2x02.mkv
```

## 🎯 Media Server Profiles

The tool includes preset patterns for popular media servers:

| Server | Movie Pattern | TV Pattern | Episode Pattern |
|--------|--------------|------------|----------------|
| **Plex** | `Title (Year)` | `Show/Season ##/` | `S##E##` |
| **Jellyfin** | `Title (Year)` | `Show/Season ##/` | `S##E##`, `#x##` |
| **Emby** | `Title (Year)` | `Show/Season ##/` | `S##E##`, `#x##` |

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
media-audit init-config [OPTIONS]

Options:
  --output PATH              Output path for config file (default: config.yaml)
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

# Install pre-commit hooks
uv run pre-commit install

# Run pre-commit hooks on all files
uv run pre-commit run --all-files
```

### Running Tests

```bash
# Run all tests
uv run pytest tests/

# Run with coverage
uv run pytest tests/ --cov=src/media_audit --cov-report=html

# Run with coverage and generate multiple reports
uv run pytest tests/ --cov=src/media_audit --cov-report=term-missing --cov-report=html --cov-report=xml

# Run specific test file
uv run pytest tests/test_scanner.py

# Run with verbose output
uv run pytest tests/ -v
```

### Code Coverage

This project uses [Codecov](https://codecov.io) for tracking test coverage. Coverage reports are automatically generated during CI runs.

To view local coverage:

```bash
# Generate HTML coverage report
uv run pytest tests/ --cov=src/media_audit --cov-report=html

# Open coverage report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

Coverage goals:

- Overall project coverage: >80%
- New code coverage: >80%
- Critical modules (scanner, validator): >90%

### Code Quality

```bash
# Run linting
uv run ruff check src tests

# Run formatting
uv run ruff format src tests

# Run type checking
uv run mypy src

# Run security checks
uv run bandit -r src

# Run all pre-commit hooks
uv run pre-commit run --all-files
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
- ✅ GitHub Actions workflow linting (actionlint)
- ✅ Link checking for documentation

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

- All tests pass (`uv run pytest tests/`)
- Pre-commit hooks pass (`uv run pre-commit run --all-files`)
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
