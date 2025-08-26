# Pattern Matching

Media Audit uses sophisticated pattern matching to identify media assets across different media server configurations. This guide explains how patterns work and how to customize them for your setup.

## Overview

Pattern matching in Media Audit identifies:

- **Posters** - Movie/series cover art
- **Backgrounds** - Fanart/backdrop images
- **Banners** - Series banner images (TV shows only)
- **Trailers** - Preview videos
- **Title Cards** - Episode thumbnails (TV episodes only)

## Default Patterns

### Plex Patterns

Media Audit includes comprehensive patterns for Plex Media Server:

```yaml
poster_patterns:
  - "^poster\\."      # poster.jpg, poster.png
  - "^folder\\."      # folder.jpg (alternative)
  - "^movie\\."       # movie.jpg (movies)
  - "^cover\\."       # cover.jpg
  - "^default\\."     # default.jpg
  - "^poster-\\d+\\." # poster-1.jpg, poster-2.jpg

background_patterns:
  - "^fanart\\."      # fanart.jpg, fanart.png
  - "^background\\."  # background.jpg
  - "^backdrop\\."    # backdrop.jpg
  - "^art\\."         # art.jpg
  - "-fanart\\."      # movie-fanart.jpg
  - "^fanart-\\d+\\." # fanart-1.jpg, fanart-2.jpg

banner_patterns:
  - "^banner\\."      # banner.jpg
  - "-banner\\."      # show-banner.jpg
  - "^banner-\\d+\\." # banner-1.jpg

trailer_patterns:
  - "-trailer\\."     # movie-trailer.mp4
  - "^trailer\\."     # trailer.mp4
  - "^trailers/.*"    # trailers/trailer1.mp4

title_card_patterns:
  - "^S\\d{2}E\\d{2}\\."      # S01E01.jpg
  - "^S\\d{2}E\\d{2}-thumb\\." # S01E01-thumb.jpg
```

### Jellyfin Patterns

Jellyfin-specific patterns with variations:

```yaml
poster_patterns:
  - "^poster\\."      # poster.jpg
  - "^folder\\."      # folder.jpg
  - "^cover\\."       # cover.jpg
  - "^poster-\\d+\\." # poster-1.jpg
  - "^poster\\d+\\."  # poster1.jpg (no dash)

background_patterns:
  - "^backdrop\\."    # backdrop.jpg
  - "^fanart\\."      # fanart.jpg
  - "^background\\."  # background.jpg
  - "^backdrop\\d+\\." # backdrop1.jpg
  - "^backdrop-\\d+\\." # backdrop-1.jpg

trailer_patterns:
  - "-trailer\\."     # movie-trailer.mp4
  - "^trailers/.*"    # trailers/ folder
  - ".*\\.trailer\\." # movie.trailer.mp4
```

### Emby Patterns

Emby server patterns including extrafanart support:

```yaml
background_patterns:
  - "^backdrop\\."      # backdrop.jpg
  - "^fanart\\."        # fanart.jpg
  - "^background\\."    # background.jpg
  - "^backdrop\\d+\\."  # backdrop1.jpg
  - "^backdrop-\\d+\\." # backdrop-1.jpg
  - "^extrafanart/.*"   # extrafanart/ folder
```

## Custom Patterns

### Creating Custom Pattern Files

Create your own pattern file for specialized setups:

```yaml
# custom-patterns.yaml
poster_patterns:
  - "^poster\\."
  - "^cover\\."
  - "^thumbnail\\."
  - "^movieposter\\."

background_patterns:
  - "^fanart\\."
  - "^backdrop\\."
  - "^wallpaper\\."
  - "^moviebackground\\."

banner_patterns:
  - "^banner\\."
  - "^logo\\."
  - "^clearlogo\\."

trailer_patterns:
  - "-trailer\\."
  - "^preview\\."
  - "^extras/trailers/.*"
  - "^clips/.*"

title_card_patterns:
  - "^S\\d{2}E\\d{2}\\."
  - "^Season\\d{2}Episode\\d{2}\\."
  - "^episode-S\\d{2}E\\d{2}\\."
```

### Using Custom Patterns

```bash
# Use custom patterns file
media-audit scan --roots "D:\Media" --patterns custom-patterns.yaml

# Or specify in configuration
media-audit scan --config config.yaml
```

In configuration file:

```yaml
scan:
  root_paths:
    - D:/Media
  patterns:
    poster_patterns:
      - "^poster\\."
      - "^custom-poster\\."
    background_patterns:
      - "^fanart\\."
      - "^custom-bg\\."
```

## Pattern Syntax

### Regex Fundamentals

Patterns use Python regex syntax with case-insensitive matching:

```yaml
# Basic patterns
"^poster\\."        # Starts with "poster."
"poster$"           # Ends with "poster"
".*poster.*"        # Contains "poster" anywhere
"poster\\d+"        # "poster" followed by digits (poster1, poster2)
"poster-\\d+\\."    # poster-1.jpg, poster-2.png
```

### Common Pattern Elements

| Element | Description | Example | Matches |
|---------|-------------|---------|---------|
| `^` | Start of filename | `^poster` | poster.jpg, posterHD.png |
| `$` | End of filename | `poster$` | movie-poster |
| `\\.` | Literal dot (escaped) | `poster\\.jpg` | poster.jpg only |
| `.*` | Any characters | `.*trailer.*` | movie-trailer.mp4 |
| `\\d+` | One or more digits | `poster\\d+` | poster1, poster123 |
| `\\d{2}` | Exactly 2 digits | `S\\d{2}` | S01, S10 |
| `[abc]` | Character class | `[Ss]eason` | Season, season |
| `(jpg\|png)` | Alternatives | `\\.(jpg\|png)$` | .jpg or .png |

### Advanced Pattern Examples

#### Multiple File Extensions

```yaml
poster_patterns:
  - "^poster\\.(jpg|png|webp)$"  # poster.jpg, poster.png, poster.webp
```

#### Year-Based Movie Patterns

```yaml
poster_patterns:
  - "^.*\\(\\d{4}\\).*poster\\."  # Movie (2023) poster.jpg
```

#### Season-Specific Patterns

```yaml
poster_patterns:
  - "^Season\\s*\\d{2}\\."        # Season 01.jpg, Season01.jpg
  - "^S\\d{2}\\."                 # S01.jpg
  - "^season\\d{2}poster\\."      # season01poster.jpg
```

#### Quality-Based Patterns

```yaml
background_patterns:
  - "^fanart.*4k\\."              # fanart-4k.jpg
  - "^backdrop.*uhd\\."           # backdrop-uhd.png
  - "^.*\\d+x\\d+.*fanart\\."     # 1920x1080-fanart.jpg
```

## Profile Combinations

### Using Multiple Profiles

Combine patterns from different servers:

```bash
# Use Plex and Jellyfin patterns
media-audit scan --roots "D:\Media" --profiles plex jellyfin

# Use all available patterns
media-audit scan --roots "D:\Media" --profiles all
```

### Profile Priority

When multiple profiles are specified, patterns are combined:

1. **Plex** patterns are added first
2. **Jellyfin** patterns are merged
3. **Emby** patterns are merged
4. **Duplicates** are removed automatically

## File Type Support

### Image Formats

Supported image extensions (case-insensitive):

- `.jpg` / `.jpeg`
- `.png`
- `.webp`
- `.tiff` / `.tif`
- `.bmp`

### Video Formats (Trailers)

Supported video extensions:

- `.mp4`
- `.mkv`
- `.avi`
- `.mov`
- `.wmv`
- `.m4v`

## Pattern Testing

### Dry Run Mode

Test patterns without generating full reports:

```bash
# Test pattern matching
media-audit scan --roots "D:\Test Movie" --report test.html
```

### Debug Pattern Matching

Enable verbose logging to see pattern matching:

```python
# Custom script for pattern testing
from media_audit.patterns import get_patterns
import re

# Load patterns
patterns = get_patterns(['plex'])
compiled = patterns.compile_patterns()

# Test file matching
filename = "poster.jpg"
for pattern in compiled.poster_re:
    if pattern.search(filename):
        print(f"✓ '{filename}' matches '{pattern.pattern}'")
```

## Real-World Examples

### Home Theater Setup

```yaml
# home-theater-patterns.yaml
poster_patterns:
  - "^poster\\."
  - "^folder\\."
  - "^cover\\."
  - "^movie-poster\\."
  - "^\\d{4}.*poster\\."  # 2023-Movie-poster.jpg

background_patterns:
  - "^fanart\\."
  - "^backdrop\\."
  - "^background\\."
  - "^movie-fanart\\."
  - "^\\d{4}.*fanart\\."  # 2023-Movie-fanart.jpg

trailer_patterns:
  - "-trailer\\."
  - "^trailer\\."
  - "^previews/.*"
  - "^extras/trailers/.*"
```

### Multi-Language Setup

```yaml
# multilang-patterns.yaml
poster_patterns:
  - "^poster\\."
  - "^poster-en\\."       # English posters
  - "^poster-fr\\."       # French posters
  - "^affiche\\."         # French term for poster

background_patterns:
  - "^fanart\\."
  - "^fanart-en\\."
  - "^fanart-fr\\."
  - "^fond\\."            # French term for background
```

### Archive/Collection Setup

```yaml
# archive-patterns.yaml
poster_patterns:
  - "^poster\\."
  - "^cover\\."
  - "^scan-front\\."      # Scanned covers
  - "^boxart\\."          # Box art

background_patterns:
  - "^fanart\\."
  - "^backdrop\\."
  - "^scan-back\\."       # Back covers
  - "^disc-art\\."        # Disc artwork

trailer_patterns:
  - "-trailer\\."
  - "^archive/trailers/.*"
  - "^restored/previews/.*"
```

## Troubleshooting Patterns

### Common Issues

#### Pattern Not Matching

```bash
# Check if regex is correct
python3 -c "
import re
pattern = r'^poster\\.'
filename = 'poster.jpg'
if re.search(pattern, filename, re.IGNORECASE):
    print('Match!')
else:
    print('No match')
"
```

#### Too Many False Positives

```yaml
# Make patterns more specific
poster_patterns:
  - "^poster\\.(jpg|png)$"  # Only exact matches
  # Instead of:
  - "^poster\\."            # Matches poster.anything
```

#### Missing File Extensions

```yaml
# Add all possible extensions
poster_patterns:
  - "^poster\\.(jpg|jpeg|png|webp|tiff|bmp)$"
```

### Pattern Validation

Test your patterns before deployment:

```python
# pattern-test.py
import re
from pathlib import Path

def test_patterns(directory, patterns):
    """Test patterns against actual files."""
    files = list(Path(directory).glob('*'))

    for pattern_str in patterns:
        pattern = re.compile(pattern_str, re.IGNORECASE)
        matches = [f.name for f in files if pattern.search(f.name)]
        print(f"Pattern '{pattern_str}': {matches}")

# Test your patterns
poster_patterns = ["^poster\\.", "^folder\\."]
test_patterns("/path/to/test/movie", poster_patterns)
```

## Best Practices

### Pattern Design

1. **Be Specific**: Use anchors (`^`, `$`) when possible
2. **Escape Dots**: Use `\\.` for literal dots in filenames
3. **Case Insensitive**: All patterns are automatically case-insensitive
4. **Test Thoroughly**: Validate patterns against real file structures

### Performance Considerations

1. **Simple Patterns First**: Put common patterns early in the list
2. **Avoid Greedy Patterns**: `.*` can be slow on large directories
3. **Use Anchors**: `^poster\\.` is faster than `.*poster\\..*`

### Maintenance

1. **Document Custom Patterns**: Comment complex regex patterns
2. **Version Control**: Keep pattern files in version control
3. **Regular Testing**: Test patterns against new file structures
4. **Profile Combinations**: Use standard profiles when possible

## Migration Guide

### From Plex to Jellyfin

```yaml
# Map Plex patterns to Jellyfin equivalents
# Plex: poster.jpg → Jellyfin: folder.jpg
# Both are supported, no migration needed

# Update configuration:
scan:
  profiles: ['jellyfin']  # Changed from ['plex']
```

### Adding Custom Patterns

```yaml
# Extend existing patterns instead of replacing
scan:
  patterns:
    poster_patterns:
      - "^poster\\."      # Keep standard
      - "^custom-art\\."  # Add custom
```

### Migrating from Legacy Tools

```yaml
# Convert from MediaElch patterns
poster_patterns:
  - "^poster\\."          # MediaElch default
  - "^folder\\."          # MediaElch folder.jpg
  - "^.*-poster\\."       # MediaElch movie-poster.jpg

# Convert from tinyMediaManager
background_patterns:
  - "^fanart\\."          # tMM default
  - "^.*-fanart\\."       # tMM movie-fanart.jpg
  - "^backdrop\\."        # tMM backdrop.jpg
```
