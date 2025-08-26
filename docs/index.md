# Media Audit

[![CI](https://github.com/beelzer/media-audit/actions/workflows/ci.yml/badge.svg)](https://github.com/beelzer/media-audit/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Media Audit** is a powerful command-line tool for auditing and validating media libraries. It scans your media collection, extracts metadata, validates file integrity, and generates beautiful HTML or JSON reports.

## Key Features

### 🎬 Smart Media Detection

- **Automatic parsing** of movie and TV show filenames
- **Pattern matching** for various naming conventions
- **Season/Episode detection** for TV shows
- **Quality detection** (720p, 1080p, 4K, etc.)
- **Source detection** (BluRay, WEB-DL, HDTV, etc.)

### 🔍 Deep Media Analysis

- **FFprobe integration** for technical metadata extraction
- **Video codec** detection (H.264, H.265/HEVC, AV1, etc.)
- **Audio codec** detection (AAC, AC3, DTS, TrueHD, etc.)
- **Resolution** and bitrate analysis
- **Duration** and file size tracking
- **Subtitle** stream detection

### ✅ Comprehensive Validation

- **File integrity** checking
- **Missing episode** detection
- **Duplicate** identification
- **Quality consistency** validation
- **Naming convention** compliance
- **Customizable validation rules**

### 📊 Beautiful Reports

- **Interactive HTML reports** with filtering and sorting
- **JSON export** for programmatic processing
- **Summary statistics** and insights
- **Issue highlighting** with severity levels
- **Performance metrics** and scan times

### ⚡ Performance & Efficiency

- **Intelligent caching** system to speed up repeated scans
- **Parallel processing** support
- **Configurable scan depth** and filters
- **Memory-efficient** streaming for large libraries

## Quick Example

```bash
# Scan a media library and generate an HTML report
media-audit scan /path/to/media --output report.html

# Scan with specific file types
media-audit scan /path/to/media --extensions .mkv .mp4 --output report.html

# Use a configuration file for complex setups
media-audit scan --config config.yaml

# Generate a JSON report for automation
media-audit scan /path/to/media --output report.json --format json
```

## Example Output

Media Audit generates comprehensive reports that help you understand and improve your media library:

```text
📊 Scan Summary
──────────────────────────────────────
Total Files Scanned: 1,247
Movies: 342
TV Episodes: 905
Total Size: 2.4 TB
Scan Duration: 3m 42s

✅ Validation Results
──────────────────────────────────────
✓ 1,189 files passed all checks
⚠ 43 files have warnings
✗ 15 files have errors

Issues Found:
• 8 duplicate files detected
• 12 files with invalid naming
• 7 episodes missing from series
• 23 files with low quality
```

## Why Media Audit?

### For Home Media Servers

- Ensure your Plex/Jellyfin/Emby library is properly organized
- Identify missing episodes in your TV show collections
- Find duplicate movies taking up space
- Verify all files follow consistent naming conventions

### For Content Creators

- Validate video encoding settings across projects
- Ensure consistent quality standards
- Track media assets and their technical specifications
- Generate reports for clients or team members

### For Archivists

- Document technical metadata for preservation
- Verify file integrity over time
- Track storage usage and compression efficiency
- Maintain quality standards for digitization projects

## Getting Started

Ready to audit your media library? Check out the [Installation Guide](getting-started/installation.md) to get started, or jump straight to the [Quick Start](getting-started/quick-start.md) for common use cases.

## Documentation

- **[Getting Started](getting-started/installation.md)** - Installation and basic setup
- **[User Guide](user-guide/usage.md)** - Detailed usage instructions and examples
- **[Configuration](getting-started/configuration.md)** - Customize Media Audit for your needs
- **[API Reference](api/cli.md)** - Complete API documentation
- **[Architecture](architecture/overview.md)** - Technical details and design decisions
- **[Contributing](contributing/setup.md)** - Help improve Media Audit

## License

Media Audit is open source software licensed under the [MIT License](https://github.com/beelzer/media-audit/blob/main/LICENSE).
