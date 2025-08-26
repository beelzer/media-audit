# Quick Start

Get up and running with Media Audit in minutes! This guide covers the most common use cases.

## Basic Scan

The simplest way to scan a media library:

```bash
media-audit scan /path/to/media
```

This will:
- Scan all media files recursively
- Extract metadata using FFprobe
- Generate an HTML report (`media-audit-report.html`)
- Display a summary in the terminal

## Common Use Cases

### Scan Movies Directory

```bash
media-audit scan ~/Movies --output movies-report.html
```

### Scan TV Shows with Episode Validation

```bash
media-audit scan ~/TVShows --media-type tv --validate-episodes
```

### Scan Specific File Types

```bash
media-audit scan /media --extensions .mkv .mp4 .avi
```

### Generate JSON Report for Automation

```bash
media-audit scan /media --format json --output report.json
```

### Quick Scan (Skip FFprobe)

```bash
media-audit scan /media --no-probe
```

## Using Configuration Files

For complex setups, use a configuration file:

1. Create `config.yaml`:

```yaml
# Paths to scan
paths:
  - /media/Movies
  - /media/TVShows

# Output settings
output:
  path: ./reports/media-audit.html
  format: html
  
# File extensions to include
extensions:
  - .mkv
  - .mp4
  - .avi

# Validation rules
validation:
  check_duplicates: true
  check_quality: true
  min_quality: 720p
  
# Performance
cache:
  enabled: true
  ttl: 604800  # 1 week
```

2. Run with config:

```bash
media-audit scan --config config.yaml
```

## Interactive Mode

Use interactive mode for guided scanning:

```bash
media-audit scan --interactive
```

This will prompt you for:
- Directory to scan
- File types to include
- Validation options
- Output format and location

## Real-World Examples

### Find Duplicate Movies

```bash
media-audit scan ~/Movies --check-duplicates --output duplicates.html
```

### Audit Video Quality

```bash
media-audit scan /media --min-quality 1080p --format json | jq '.issues.low_quality'
```

### TV Show Completeness Check

```bash
media-audit scan "/media/TV Shows/The Office" --media-type tv --validate-episodes
```

### Generate Weekly Reports

Add to crontab:

```bash
0 2 * * 0 media-audit scan /media --config ~/media-audit.yaml --output ~/reports/weekly-$(date +\%Y\%m\%d).html
```

## Understanding the Output

### Terminal Output

```
🎬 Media Audit v0.1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📂 Scanning: /media/Movies
Progress: 100%|████████████| 342/342 [03:42<00:00]

📊 Scan Summary
──────────────────────────────────────
Files Scanned:     342
Total Size:        1.2 TB
Scan Duration:     3m 42s

✅ Validation Results
──────────────────────────────────────
✓ 325 files passed
⚠ 12 files have warnings  
✗ 5 files have errors

Top Issues:
• 3 duplicate files
• 5 files below quality threshold
• 4 files with invalid naming

📄 Report saved to: movies-report.html
```

### HTML Report Features

The generated HTML report includes:

1. **Summary Dashboard**
   - Total files and size
   - Media type breakdown
   - Quality distribution
   - Issue statistics

2. **File Listing**
   - Sortable columns
   - Filterable by type/quality/status
   - Detailed metadata on hover
   - Direct file links

3. **Issues Section**
   - Categorized by severity
   - Actionable recommendations
   - Bulk operations support

4. **Statistics**
   - Quality distribution charts
   - Codec usage graphs
   - File size histograms
   - Bitrate analysis

## Tips for Large Libraries

### Use Caching

Enable caching to speed up repeated scans:

```bash
media-audit scan /media --cache --cache-ttl 86400
```

### Parallel Processing

Increase worker threads for faster scanning:

```bash
media-audit scan /media --workers 8
```

### Incremental Scanning

Scan only new or modified files:

```bash
media-audit scan /media --since "2024-01-01"
```

### Filter by Size

Skip small files that might be samples:

```bash
media-audit scan /media --min-size 100MB
```

## Common Patterns

### CI/CD Integration

```yaml
# .github/workflows/media-audit.yml
name: Media Library Audit

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Media Audit
        run: pip install media-audit
      - name: Run Audit
        run: media-audit scan /media --config config.yaml
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: media-report
          path: media-audit-report.html
```

### Shell Aliases

Add to `~/.bashrc` or `~/.zshrc`:

```bash
alias audit-movies='media-audit scan ~/Movies --output ~/reports/movies-$(date +%Y%m%d).html'
alias audit-tv='media-audit scan ~/TVShows --media-type tv --validate-episodes'
alias audit-all='media-audit scan --config ~/.config/media-audit/config.yaml'
```

## Next Steps

- Learn about [Configuration](configuration.md) options
- Explore [Advanced Usage](../user-guide/advanced.md)
- Understand [Patterns & Matching](../user-guide/patterns.md)
- Read about [Report Formats](../user-guide/reports.md)