# Installation

Media Audit requires Python 3.13 or higher and FFmpeg for media analysis.

## Prerequisites

### Python 3.13+

Media Audit requires Python 3.13 or newer. Check your Python version:

```bash
python --version
```

If you need to install or upgrade Python, visit [python.org](https://www.python.org/downloads/).

### FFmpeg

FFmpeg is required for extracting technical metadata from media files.

=== "Linux"

    ```bash
    # Ubuntu/Debian
    sudo apt update && sudo apt install ffmpeg

    # Fedora
    sudo dnf install ffmpeg

    # Arch Linux
    sudo pacman -S ffmpeg
    ```

=== "macOS"

    ```bash
    # Using Homebrew
    brew install ffmpeg

    # Using MacPorts
    sudo port install ffmpeg
    ```

=== "Windows"

    ```bash
    # Using Chocolatey
    choco install ffmpeg

    # Using Scoop
    scoop install ffmpeg
    ```

    Or download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

Verify FFmpeg installation:

```bash
ffmpeg -version
```

## Installation Methods

### Using pip (Recommended)

Install Media Audit from PyPI:

```bash
pip install media-audit
```

For the latest development version:

```bash
pip install git+https://github.com/beelzer/media-audit.git
```

### Using pipx (Isolated Environment)

[pipx](https://pipx.pypa.io/) installs Media Audit in an isolated environment:

```bash
pipx install media-audit
```

### Using uv (Fast Python Package Manager)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer:

```bash
uv pip install media-audit
```

### From Source

Clone the repository and install in development mode:

```bash
git clone https://github.com/beelzer/media-audit.git
cd media-audit
pip install -e .
```

For development with all dependencies:

```bash
pip install -e .[dev,docs]
```

## Verify Installation

After installation, verify Media Audit is working:

```bash
media-audit --version
```

You should see output like:

```
media-audit, version 0.1.0
```

Test with a simple scan:

```bash
media-audit scan --help
```

## Docker Installation

A Docker image is available for containerized deployments:

```bash
docker pull ghcr.io/beelzer/media-audit:latest
```

Run with Docker:

```bash
docker run -v /path/to/media:/media:ro \
           -v $(pwd):/output \
           ghcr.io/beelzer/media-audit:latest \
           scan /media --output /output/report.html
```

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  media-audit:
    image: ghcr.io/beelzer/media-audit:latest
    volumes:
      - /path/to/media:/media:ro
      - ./reports:/output
      - ./config.yaml:/config/config.yaml:ro
    command: scan --config /config/config.yaml
```

Run with:

```bash
docker-compose run media-audit
```

## Platform-Specific Notes

### Windows

On Windows, you may need to:

1. **Add Python to PATH** during installation
2. **Use `python -m pip`** instead of `pip` if pip is not in PATH
3. **Run as Administrator** for system-wide installation
4. **Install Visual C++ Build Tools** if you encounter compilation errors

### macOS

On macOS with Apple Silicon (M1/M2):

- Ensure you're using native ARM64 Python for best performance
- FFmpeg installed via Homebrew will automatically use the correct architecture

### Linux

On Linux systems:

- You may need to use `pip3` instead of `pip`
- For system-wide installation, consider using `--user` flag or virtual environments
- Some distributions may require additional development packages for compilation

## Troubleshooting

### FFmpeg Not Found

If Media Audit reports FFmpeg is not found:

1. Ensure FFmpeg is installed (see Prerequisites)
2. Verify FFmpeg is in your system PATH:
   ```bash
   which ffmpeg  # Linux/macOS
   where ffmpeg  # Windows
   ```
3. If using Docker, FFmpeg is included in the image

### Permission Errors

If you encounter permission errors during installation:

```bash
# Install for current user only
pip install --user media-audit

# Or use a virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows
pip install media-audit
```

### Import Errors

If you get import errors after installation:

1. Ensure you're using the correct Python version (3.13+)
2. Check if Media Audit is installed in the active environment:
   ```bash
   pip show media-audit
   ```
3. Try reinstalling with dependencies:
   ```bash
   pip install --upgrade --force-reinstall media-audit
   ```

## Next Steps

Once installed, proceed to:

- [Quick Start](quick-start.md) - Get up and running quickly
- [Configuration](configuration.md) - Customize Media Audit for your needs
- [Basic Usage](../user-guide/usage.md) - Learn all available commands and options