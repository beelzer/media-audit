# Development Setup

This guide walks through setting up a development environment for Media Audit, including tools, dependencies, and workflow setup.

## Prerequisites

### System Requirements

- **Python**: 3.13 or higher
- **FFmpeg**: Required for video analysis (includes FFprobe)
- **Git**: For version control
- **Modern Terminal**: PowerShell 7+ (Windows) or Bash (Unix-like)

### Platform-Specific Setup

#### Windows

```powershell
# Install Python 3.13 (if not already installed)
winget install Python.Python.3.13

# Install FFmpeg
winget install Gyan.FFmpeg
# Or using Chocolatey
choco install ffmpeg

# Install uv (recommended Python package manager)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Verify installations
python --version     # Should show Python 3.13+
ffprobe -version    # Should show FFmpeg version
uv --version        # Should show uv version
```

#### macOS

```bash
# Install Python 3.13 using Homebrew
brew install python@3.13

# Install FFmpeg
brew install ffmpeg

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installations
python3.13 --version
ffprobe -version
uv --version
```

#### Linux (Ubuntu/Debian)

```bash
# Install Python 3.13
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev

# Install FFmpeg
sudo apt install ffmpeg

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installations
python3.13 --version
ffprobe -version
uv --version
```

#### Linux (CentOS/RHEL/Fedora)

```bash
# Install Python 3.13 (may require EPEL on older versions)
sudo dnf install python3.13 python3.13-devel

# Install FFmpeg
sudo dnf install ffmpeg ffmpeg-devel

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Project Setup

### 1. Clone Repository

```bash
# Clone the repository
git clone https://github.com/beelzer/media-audit.git
cd media-audit

# If you plan to contribute, fork first and clone your fork
git clone https://github.com/YOUR-USERNAME/media-audit.git
cd media-audit

# Add upstream remote
git remote add upstream https://github.com/beelzer/media-audit.git
```

### 2. Development Environment Setup

#### Using uv (Recommended)

```bash
# Create virtual environment and install dependencies
uv venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix-like systems:
source .venv/bin/activate

# Install project in development mode with all dependencies
uv pip install -e ".[dev,test,docs]"

# Verify installation
media-audit --version
```

#### Using Traditional pip/venv

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix-like systems:
source .venv/bin/activate

# Upgrade pip and install build tools
pip install --upgrade pip setuptools wheel

# Install project in development mode
pip install -e ".[dev,test,docs]"
```

### 3. Pre-commit Setup

Media Audit uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks on all files (first time setup)
pre-commit run --all-files

# Test pre-commit setup
git add .
git commit -m "Test commit"  # Should run all hooks
```

### 4. Verify Setup

```bash
# Run basic functionality test
media-audit scan --help

# Run test suite
pytest

# Run linting
ruff check src tests

# Run type checking
mypy src

# Run formatting check
ruff format --check src tests
```

## Development Dependencies

### Core Dependencies

The project's dependencies are defined in `pyproject.toml`:

```toml
[project]
dependencies = [
    "click>=8.1.0",
    "pyyaml>=6.0",
    "rich>=13.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "pre-commit>=3.0.0",
]

test = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "pytest-asyncio>=0.21.0",
]

docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0",
    "mkdocs-mermaid2-plugin>=1.1.0",
]
```

### Development Tools Overview

#### Code Quality Tools

- **Ruff**: Fast Python linter and formatter
  - Replaces flake8, isort, black, and many other tools
  - Configured in `pyproject.toml`
  - Runs automatically in pre-commit hooks

- **MyPy**: Static type checker
  - Ensures type safety throughout the codebase
  - Configured for strict type checking
  - Catches type-related errors before runtime

- **Pre-commit**: Git hook framework
  - Runs quality checks before each commit
  - Prevents committing broken or poorly formatted code
  - Configured in `.pre-commit-config.yaml`

#### Testing Tools

- **Pytest**: Testing framework
  - Supports fixtures, parametrization, and plugins
  - Configured for test discovery and coverage

- **Pytest-cov**: Coverage reporting
  - Measures code coverage during tests
  - Generates HTML and terminal reports

- **Pytest-mock**: Mocking utilities
  - Simplifies mocking in tests
  - Built on top of unittest.mock

#### Documentation Tools

- **MkDocs**: Documentation site generator
  - Converts Markdown to static HTML
  - Supports themes and plugins

- **Material for MkDocs**: Modern documentation theme
  - Responsive design with search
  - Syntax highlighting and navigation

## IDE Configuration

### Visual Studio Code

Recommended extensions and settings:

#### Extensions

```json
{
    "recommendations": [
        "ms-python.python",
        "ms-python.mypy-type-checker",
        "charliermarsh.ruff",
        "ms-python.pytest",
        "yzhang.markdown-all-in-one",
        "bierner.markdown-mermaid"
    ]
}
```

#### Settings (`.vscode/settings.json`)

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.formatting.provider": "none",
    "python.analysis.typeCheckingMode": "strict",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll": true,
            "source.organizeImports": true
        }
    },
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".coverage": true,
        ".pytest_cache": true,
        ".mypy_cache": true,
        ".ruff_cache": true
    }
}
```

### PyCharm/IntelliJ

1. **Open Project**: Open the media-audit directory
2. **Set Python Interpreter**:
   - File → Settings → Project → Python Interpreter
   - Add Interpreter → Existing Environment
   - Select `.venv/bin/python` (or `.venv\Scripts\python.exe` on Windows)
3. **Enable Type Checking**:
   - Install MyPy plugin
   - Enable "Type checking" in Python inspection settings
4. **Configure Code Style**:
   - Import code style settings from `pyproject.toml`
   - Enable "Reformat code" on commit

### Vim/Neovim

Example configuration for Python development:

```lua
-- Using lazy.nvim plugin manager
return {
    -- LSP Configuration
    {
        "neovim/nvim-lspconfig",
        config = function()
            local lspconfig = require('lspconfig')

            -- Python LSP (Pyright)
            lspconfig.pyright.setup{
                settings = {
                    python = {
                        analysis = {
                            typeCheckingMode = "strict",
                            useLibraryCodeForTypes = true
                        }
                    }
                }
            }

            -- Ruff LSP
            lspconfig.ruff_lsp.setup{}
        end
    },

    -- Formatting
    {
        "stevearc/conform.nvim",
        config = function()
            require("conform").setup({
                formatters_by_ft = {
                    python = { "ruff_format" },
                },
                format_on_save = {
                    timeout_ms = 500,
                    lsp_fallback = true,
                },
            })
        end
    }
}
```

## Environment Configuration

### Environment Variables

Create a `.env` file for development configuration:

```bash
# Development environment variables
MEDIA_AUDIT_DEBUG=1
MEDIA_AUDIT_CACHE_DIR=.dev-cache
MEDIA_AUDIT_LOG_LEVEL=DEBUG

# Test media paths (adjust for your system)
TEST_MEDIA_PATH=/path/to/test/media
SAMPLE_MOVIE_PATH=/path/to/sample/movie
SAMPLE_TV_PATH=/path/to/sample/tv

# Development database (if applicable)
DATABASE_URL=sqlite:///dev.db
```

### Configuration Files

#### Development Configuration (`dev-config.yaml`)

```yaml
scan:
  root_paths:
    - "./test-data/movies"
    - "./test-data/tv"
  profiles: ["all"]
  allowed_codecs: ["hevc", "h265", "av1", "h264"]  # Allow all for testing
  concurrent_workers: 2
  cache_enabled: true
  cache_dir: ".dev-cache"

report:
  output_path: "dev-audit.html"
  json_path: "dev-audit.json"
  auto_open: true
  problems_only: false
  show_thumbnails: true
```

#### Test Configuration (`test-config.yaml`)

```yaml
scan:
  root_paths:
    - "./tests/fixtures/movies"
    - "./tests/fixtures/tv"
  profiles: ["all"]
  concurrent_workers: 1  # Single threaded for consistent tests
  cache_enabled: false   # Disable caching in tests

report:
  output_path: "test-output.html"
  json_path: "test-output.json"
  auto_open: false
  problems_only: false
```

## Test Data Setup

### Creating Test Media Structure

```bash
# Create test directory structure
mkdir -p test-data/{movies,tv}

# Example movie structure
mkdir -p "test-data/movies/The Matrix (1999)"
touch "test-data/movies/The Matrix (1999)/The Matrix (1999).mkv"
touch "test-data/movies/The Matrix (1999)/poster.jpg"
touch "test-data/movies/The Matrix (1999)/fanart.jpg"

# Example TV structure
mkdir -p "test-data/tv/Breaking Bad/Season 01"
touch "test-data/tv/Breaking Bad/poster.jpg"
touch "test-data/tv/Breaking Bad/fanart.jpg"
touch "test-data/tv/Breaking Bad/Season01.jpg"
touch "test-data/tv/Breaking Bad/Season 01/S01E01.mkv"
touch "test-data/tv/Breaking Bad/Season 01/S01E01.jpg"

# Create sample video files (for testing without actual media)
# These are just empty files for structure testing
echo "fake video data" > "test-data/movies/The Matrix (1999)/The Matrix (1999).mkv"
echo "fake video data" > "test-data/tv/Breaking Bad/Season 01/S01E01.mkv"
```

### Test Fixtures

The test suite includes fixtures for various scenarios:

```python
# tests/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def sample_movie_dir(tmp_path):
    """Create sample movie directory structure."""
    movie_dir = tmp_path / "The Matrix (1999)"
    movie_dir.mkdir()

    # Create video file
    video_file = movie_dir / "The Matrix (1999).mkv"
    video_file.write_text("fake video content")

    # Create assets
    (movie_dir / "poster.jpg").write_bytes(b"fake image")
    (movie_dir / "fanart.jpg").write_bytes(b"fake image")

    return movie_dir

@pytest.fixture
def sample_tv_dir(tmp_path):
    """Create sample TV show directory structure."""
    series_dir = tmp_path / "Breaking Bad"
    series_dir.mkdir()

    # Series assets
    (series_dir / "poster.jpg").write_bytes(b"fake image")
    (series_dir / "fanart.jpg").write_bytes(b"fake image")

    # Season directory
    season_dir = series_dir / "Season 01"
    season_dir.mkdir()

    # Season assets
    (series_dir / "Season01.jpg").write_bytes(b"fake image")

    # Episode
    episode_file = season_dir / "S01E01.mkv"
    episode_file.write_text("fake video content")
    (season_dir / "S01E01.jpg").write_bytes(b"fake image")

    return series_dir
```

## Development Workflow

### Daily Development

```bash
# Start of day - sync with upstream
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/new-feature

# Make changes...
# Run tests frequently
pytest tests/

# Run type checking
mypy src

# Run linting and formatting
ruff check src tests
ruff format src tests

# Commit changes (pre-commit hooks will run)
git add .
git commit -m "feat: add new feature"

# Push to your fork
git push origin feature/new-feature
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_scanner.py

# Run tests matching pattern
pytest tests/ -k "test_movie"

# Run tests in parallel (if pytest-xdist installed)
pytest -n auto

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x
```

### Code Quality Checks

```bash
# Run all quality checks
make check  # If Makefile exists

# Or run individually:
ruff check src tests          # Linting
ruff format --check src tests # Formatting check
mypy src                      # Type checking
pytest                        # Tests
```

### Documentation Development

```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build

# Deploy documentation (maintainers only)
mkdocs gh-deploy
```

## Troubleshooting

### Common Issues

#### Import Errors

```bash
# Problem: Import errors when running tests or scripts
# Solution: Ensure project is installed in development mode
uv pip install -e .

# Or reinstall completely
uv pip uninstall media-audit
uv pip install -e ".[dev,test]"
```

#### FFprobe Not Found

```bash
# Problem: FFprobe not found in PATH
# Solution: Verify FFmpeg installation
ffprobe -version

# On Windows, ensure FFmpeg is in PATH
# On macOS: brew install ffmpeg
# On Linux: sudo apt install ffmpeg
```

#### Pre-commit Hook Failures

```bash
# Problem: Pre-commit hooks failing
# Solution: Run hooks manually to see specific errors
pre-commit run --all-files

# Update hooks to latest versions
pre-commit autoupdate

# Skip hooks temporarily (for emergency commits only)
git commit -m "message" --no-verify
```

#### Virtual Environment Issues

```bash
# Problem: Virtual environment not working correctly
# Solution: Recreate virtual environment
rm -rf .venv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -e ".[dev,test]"
```

#### Type Checking Errors

```bash
# Problem: MyPy type checking errors
# Solution: Install type stubs for dependencies
uv pip install types-PyYAML types-requests

# Check MyPy configuration
mypy --config-file pyproject.toml src
```

### Getting Help

1. **Check Documentation**: Review this setup guide and other docs
2. **Search Issues**: Look through GitHub issues for similar problems
3. **Ask Questions**: Open a GitHub discussion or issue
4. **Debug Mode**: Run with debug logging enabled:

   ```bash
   export MEDIA_AUDIT_DEBUG=1
   media-audit scan --roots test-data
   ```

### Performance Debugging

```bash
# Profile code execution
python -m cProfile -o profile.prof -m media_audit scan --roots test-data

# Analyze profile
python -c "
import pstats
p = pstats.Stats('profile.prof')
p.sort_stats('cumulative').print_stats(20)
"

# Memory profiling (if memory_profiler installed)
mprof run media-audit scan --roots test-data
mprof plot
```

## Next Steps

After completing the development setup:

1. **Read the Contributing Guidelines**: Review `docs/contributing/guidelines.md`
2. **Understand the Testing Strategy**: Check `docs/contributing/testing.md`
3. **Explore the Architecture**: Study `docs/architecture/overview.md`
4. **Look at Open Issues**: Find beginner-friendly issues on GitHub
5. **Join the Community**: Participate in discussions and code reviews

The development environment is now ready for contributing to Media Audit!
