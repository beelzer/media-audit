# Quick Start

Get up and running with Media Audit in minutes! This guide covers the most common use cases.

## Basic Scan

The simplest way to scan your current directory:

```bash
media-audit scan
```

To scan specific directories:

```bash
media-audit scan -r /path/to/media
```

This will:

- Scan all media files recursively
- Extract metadata using FFprobe
- Generate an HTML report (`media-audit-report.html`)
- Display a summary in the terminal

## Common Use Cases

### Scan Movies Directory

```bash
media-audit scan -r ~/Movies --report movies-report.html
```

### Scan TV Shows

```bash
media-audit scan -r ~/TVShows --profiles jellyfin
```

### Scan Multiple Directories

```bash
media-audit scan -r ~/Movies -r ~/TVShows -r ~/Documentaries
```

### Generate JSON Report for Automation

```bash
media-audit scan -r /media --json report.json
```

### Quick Scan Without Cache

```bash
media-audit scan -r /media --no-cache
```

### Show Only Problems

```bash
media-audit scan -r /media --problems-only
```

## Using Media Server Profiles

Media Audit understands different media server organization patterns:

### Plex Media Server

```bash
media-audit scan -r "/var/lib/plexmediaserver/Library" --profiles plex
```

### Jellyfin

```bash
media-audit scan -r /media --profiles jellyfin
```

### Multiple Profiles

```bash
media-audit scan -r /media --profiles plex --profiles jellyfin
```

## Working with Codecs

By default, Media Audit checks for modern codecs (HEVC, H265, AV1). You can customize this:

### Allow Only Specific Codecs

```bash
media-audit scan --allow-codecs H264 --allow-codecs HEVC
```

### Check for Legacy Codecs

```bash
media-audit scan --allow-codecs MPEG4 --allow-codecs VP8
```

## Performance Tuning

### Adjust Worker Threads

```bash
# For fast SSD storage
media-audit scan -r /media --workers 8

# For network storage
media-audit scan -r /mnt/nas --workers 2
```

### Enable Verbose Output

```bash
media-audit scan -r /media --verbose
```

### Debug Mode

```bash
media-audit scan -r /media --debug --log-file scan.log
```

## Using Configuration Files

### Generate Sample Configuration

```bash
media-audit init-config
```

This creates a `config.yaml` file you can customize.

### Use Configuration File

```bash
media-audit scan --config config.yaml
```

### Override Configuration

```bash
media-audit scan --config config.yaml --workers 16 --no-cache
```

## Report Options

### Auto-Open Report

```bash
media-audit scan -r /media --open
```

### Generate Both HTML and JSON

```bash
media-audit scan -r /media --report report.html --json report.json
```

### Custom Report Location

```bash
media-audit scan -r /media --report ~/Desktop/media-report.html
```

## Filtering Files

### Include Specific Patterns

```bash
media-audit scan --include "*.mkv" --include "*.mp4"
```

### Exclude Patterns

```bash
media-audit scan --exclude "*sample*" --exclude "*trailer*"
```

### Custom Pattern File

```bash
media-audit scan --patterns custom-patterns.yaml
```

## Complete Example

Here's a comprehensive scan command:

```bash
media-audit scan \
  --roots /media/Movies \
  --roots /media/TVShows \
  --profiles plex \
  --allow-codecs HEVC \
  --allow-codecs AV1 \
  --exclude "*sample*" \
  --workers 8 \
  --report full-scan.html \
  --json full-scan.json \
  --problems-only \
  --open \
  --verbose
```

## What's Next?

- Learn about [Configuration](configuration.md) options
- Understand [Media Patterns](../user-guide/patterns.md)
- Explore [Report Features](../user-guide/reports.md)
- Read the [User Guide](../user-guide/usage.md)

## Getting Help

```bash
# Show general help
media-audit --help

# Show scan command help
media-audit scan --help

# Show version
media-audit --version
```
