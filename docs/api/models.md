# Data Models API Reference

This reference documents the data models used throughout Media Audit, including their structure, relationships, and usage patterns.

## Core Models

### `MediaItem`

Base class for all media items in the system.

```python
from media_audit.models import MediaItem, MediaType, ValidationStatus

@dataclass
class MediaItem:
    path: Path                              # Filesystem path to item
    name: str                              # Display name
    type: MediaType                        # Item type (movie, series, etc.)
    assets: MediaAssets                    # Associated media assets
    issues: list[ValidationIssue]          # Validation issues
    metadata: dict[str, Any]               # Additional metadata
```

#### Properties

##### `status`
**Type**: `ValidationStatus`  
**Description**: Overall validation status derived from issues.

```python
@property
def status(self) -> ValidationStatus:
    """Get overall validation status."""
    if any(issue.severity == ValidationStatus.ERROR for issue in self.issues):
        return ValidationStatus.ERROR
    if any(issue.severity == ValidationStatus.WARNING for issue in self.issues):
        return ValidationStatus.WARNING
    return ValidationStatus.VALID
```

**Values**:
- `ValidationStatus.VALID`: No issues found
- `ValidationStatus.WARNING`: Non-critical issues present  
- `ValidationStatus.ERROR`: Critical issues requiring attention

##### `has_issues`
**Type**: `bool`  
**Description**: Quick check for any validation issues.

```python
@property  
def has_issues(self) -> bool:
    """Check if item has any issues."""
    return len(self.issues) > 0
```

#### Usage Examples

```python
# Check item status
if item.status == ValidationStatus.ERROR:
    print(f"Critical issues in {item.name}")

# Iterate through issues  
for issue in item.issues:
    print(f"{issue.severity}: {issue.message}")

# Check for specific issue categories
asset_issues = [i for i in item.issues if i.category == "assets"]
encoding_issues = [i for i in item.issues if i.category == "encoding"]
```

## Media Types

### `MediaType`

Enumeration of supported media content types.

```python
from enum import Enum, auto

class MediaType(Enum):
    MOVIE = auto()
    TV_SERIES = auto() 
    TV_SEASON = auto()
    TV_EPISODE = auto()
```

### `MovieItem`

Represents a movie with associated metadata and assets.

```python
@dataclass
class MovieItem(MediaItem):
    year: int | None = None                # Release year
    video_info: VideoInfo | None = None    # Video file information
    imdb_id: str | None = None            # IMDb identifier
    tmdb_id: str | None = None            # The Movie Database ID
    release_group: str | None = None       # Release group name
    quality: str | None = None            # Quality indicator (1080p, 4K, etc.)
    source: str | None = None             # Source type (BluRay, WEBDL, etc.)
```

#### Automatic Fields
- `type`: Automatically set to `MediaType.MOVIE`

#### Usage Examples

```python
# Create movie item
movie = MovieItem(
    path=Path("/movies/The Matrix (1999)"),
    name="The Matrix",
    year=1999,
    quality="1080p",
    source="BluRay"
)

# Access movie-specific fields
print(f"{movie.name} ({movie.year})")
print(f"Quality: {movie.quality}")
print(f"Source: {movie.source}")

# Check video information
if movie.video_info:
    print(f"Codec: {movie.video_info.codec.value}")
    print(f"Resolution: {movie.video_info.resolution}")
```

### `SeriesItem`

Represents a TV series with seasons and episodes.

```python
@dataclass
class SeriesItem(MediaItem):
    seasons: list[SeasonItem] = field(default_factory=list)    # Season list
    total_episodes: int = 0                                    # Total episode count
    imdb_id: str | None = None                                # IMDb identifier
    tvdb_id: str | None = None                                # TheTVDB identifier
    tmdb_id: str | None = None                                # The Movie Database ID
```

#### Automatic Fields
- `type`: Automatically set to `MediaType.TV_SERIES`
- `total_episodes`: Automatically updated when seasons are modified

#### Methods

##### `update_episode_count()`
Updates the total episode count from all seasons.

```python
def update_episode_count(self) -> None:
    """Update total episode count."""
    self.total_episodes = sum(len(season.episodes) for season in self.seasons)
```

#### Usage Examples

```python
# Create series
series = SeriesItem(
    path=Path("/tv/Breaking Bad"),
    name="Breaking Bad"
)

# Add seasons
season1 = SeasonItem(season_number=1, name="Season 1")
season2 = SeasonItem(season_number=2, name="Season 2")
series.seasons = [season1, season2]
series.update_episode_count()

# Access series information
print(f"{series.name}: {series.total_episodes} episodes across {len(series.seasons)} seasons")

# Iterate through seasons and episodes
for season in series.seasons:
    print(f"Season {season.season_number}: {len(season.episodes)} episodes")
    for episode in season.episodes:
        print(f"  S{episode.season_number:02d}E{episode.episode_number:02d}: {episode.name}")
```

### `SeasonItem`

Represents a TV season within a series.

```python
@dataclass
class SeasonItem(MediaItem):
    season_number: int = 0                           # Season number (1-based)
    episodes: list[EpisodeItem] = field(default_factory=list)  # Episode list
```

#### Automatic Fields
- `type`: Automatically set to `MediaType.TV_SEASON`

#### Usage Examples

```python
# Create season
season = SeasonItem(
    path=Path("/tv/Breaking Bad/Season 01"),
    name="Season 1",
    season_number=1
)

# Add episodes
episode1 = EpisodeItem(season_number=1, episode_number=1, name="Pilot")
episode2 = EpisodeItem(season_number=1, episode_number=2, name="Cat's in the Bag...")
season.episodes = [episode1, episode2]

# Check season assets
if not season.assets.posters:
    print(f"Season {season.season_number} missing poster")
```

### `EpisodeItem`

Represents a single TV episode.

```python
@dataclass
class EpisodeItem(MediaItem):
    season_number: int = 0                    # Season number
    episode_number: int = 0                   # Episode number (1-based)
    episode_title: str | None = None          # Episode title
    video_info: VideoInfo | None = None       # Video file information
    release_group: str | None = None          # Release group name
    quality: str | None = None               # Quality indicator
    source: str | None = None                # Source type
```

#### Automatic Fields
- `type`: Automatically set to `MediaType.TV_EPISODE`

#### Usage Examples

```python
# Create episode
episode = EpisodeItem(
    path=Path("/tv/Breaking Bad/Season 01/S01E01.mkv"),
    name="S01E01 - Pilot",
    season_number=1,
    episode_number=1,
    episode_title="Pilot",
    quality="1080p",
    source="WEBDL"
)

# Format episode identifier
episode_id = f"S{episode.season_number:02d}E{episode.episode_number:02d}"
print(f"{episode_id}: {episode.episode_title}")

# Check for title card
if not episode.assets.title_cards:
    print(f"Episode {episode_id} missing title card")
```

## Asset Models

### `MediaAssets`

Container for all media assets associated with an item.

```python
@dataclass
class MediaAssets:
    posters: list[Path] = field(default_factory=list)        # Poster images
    backgrounds: list[Path] = field(default_factory=list)    # Background/fanart images
    banners: list[Path] = field(default_factory=list)        # Banner images (TV shows)
    trailers: list[Path] = field(default_factory=list)       # Trailer videos
    title_cards: list[Path] = field(default_factory=list)    # Episode thumbnails
```

#### Usage Examples

```python
# Create assets
assets = MediaAssets(
    posters=[Path("poster.jpg"), Path("folder.jpg")],
    backgrounds=[Path("fanart.jpg")],
    trailers=[Path("trailer.mp4")]
)

# Check asset availability
has_poster = bool(assets.posters)
has_background = bool(assets.backgrounds)
has_trailer = bool(assets.trailers)

# Count total assets
total_assets = (len(assets.posters) + len(assets.backgrounds) + 
                len(assets.banners) + len(assets.trailers) + 
                len(assets.title_cards))

# Get first poster (if available)
primary_poster = assets.posters[0] if assets.posters else None
```

## Video Information

### `VideoInfo`

Contains detailed information about video files.

```python
@dataclass
class VideoInfo:
    path: Path                              # Path to video file
    codec: CodecType | None = None         # Video codec
    resolution: tuple[int, int] | None = None    # Width x Height
    duration: float | None = None          # Duration in seconds
    bitrate: int | None = None            # Bitrate in bits per second
    size: int = 0                         # File size in bytes
    raw_info: dict[str, Any] = field(default_factory=dict)  # Raw FFprobe data
```

#### Usage Examples

```python
# Create video info
video_info = VideoInfo(
    path=Path("/movies/Movie.mkv"),
    codec=CodecType.HEVC,
    resolution=(1920, 1080),
    duration=7260.5,  # 2 hours, 1 minute
    bitrate=8500000,  # 8.5 Mbps
    size=7500000000   # 7.5 GB
)

# Format information for display
duration_minutes = video_info.duration / 60 if video_info.duration else 0
size_gb = video_info.size / (1024**3)
bitrate_mbps = video_info.bitrate / 1_000_000 if video_info.bitrate else 0

print(f"Codec: {video_info.codec.value}")
print(f"Resolution: {video_info.resolution[0]}x{video_info.resolution[1]}")
print(f"Duration: {duration_minutes:.1f} minutes")
print(f"Size: {size_gb:.2f} GB")
print(f"Bitrate: {bitrate_mbps:.1f} Mbps")
```

### `CodecType`

Enumeration of supported video codecs.

```python
class CodecType(Enum):
    HEVC = "hevc"          # H.265/HEVC
    H265 = "h265"          # Alternative H.265 name
    AV1 = "av1"            # AOMedia Video 1
    H264 = "h264"          # H.264/AVC
    VP9 = "vp9"            # VP9
    MPEG4 = "mpeg4"        # MPEG-4
    MPEG2 = "mpeg2"        # MPEG-2
    OTHER = "other"        # Unknown/other codecs
```

#### Usage Examples

```python
# Check codec type
if video_info.codec == CodecType.H264:
    print("Consider re-encoding to HEVC for better compression")

# Codec compatibility check
modern_codecs = {CodecType.HEVC, CodecType.H265, CodecType.AV1}
is_modern = video_info.codec in modern_codecs

# Codec name for display
codec_name = video_info.codec.value.upper() if video_info.codec else "Unknown"
```

## Validation Models

### `ValidationStatus`

Enumeration of validation statuses.

```python
class ValidationStatus(Enum):
    VALID = "valid"        # No issues found
    WARNING = "warning"    # Non-critical issues
    ERROR = "error"        # Critical issues
```

### `ValidationIssue`

Represents a single validation issue found during scanning.

```python
@dataclass
class ValidationIssue:
    category: str                          # Issue category
    message: str                          # Human-readable description
    severity: ValidationStatus            # Issue severity
    details: dict[str, Any] = field(default_factory=dict)  # Additional details
```

#### Common Categories
- `"assets"` - Missing or invalid assets
- `"encoding"` - Video encoding issues
- `"structure"` - Directory/file structure issues
- `"naming"` - Naming convention violations
- `"quality"` - Quality-related issues

#### Usage Examples

```python
# Create validation issues
missing_poster = ValidationIssue(
    category="assets",
    message="Missing poster image",
    severity=ValidationStatus.ERROR,
    details={"expected": ["poster.jpg", "folder.jpg"]}
)

codec_warning = ValidationIssue(
    category="encoding", 
    message="Video uses non-preferred codec: h264",
    severity=ValidationStatus.WARNING,
    details={"codec": "h264", "file": "movie.mkv"}
)

# Filter issues by category
asset_issues = [issue for issue in item.issues if issue.category == "assets"]
error_issues = [issue for issue in item.issues if issue.severity == ValidationStatus.ERROR]

# Format issue for display
def format_issue(issue: ValidationIssue) -> str:
    severity_icon = {"error": "❌", "warning": "⚠️", "valid": "✅"}
    icon = severity_icon.get(issue.severity.value, "?")
    return f"{icon} {issue.message}"
```

## Scan Results

### `ScanResult`

Container for complete scan results and statistics.

```python
@dataclass
class ScanResult:
    scan_time: datetime                    # When scan was performed
    duration: float                        # Scan duration in seconds
    root_paths: list[Path]                # Scanned root paths
    movies: list[MovieItem] = field(default_factory=list)      # Movie results
    series: list[SeriesItem] = field(default_factory=list)     # TV series results
    total_items: int = 0                  # Total item count
    total_issues: int = 0                 # Total issue count
    errors: list[str] = field(default_factory=list)           # Scan errors
```

#### Automatic Updates
Statistics are automatically updated when the object is created or modified.

#### Methods

##### `update_stats()`
Recalculates total items and issues from current data.

```python
def update_stats(self) -> None:
    """Update scan statistics."""
    self.total_items = len(self.movies) + len(self.series)
    self.total_issues = (
        sum(len(movie.issues) for movie in self.movies) +
        sum(len(series.issues) for series in self.series) +
        sum(len(season.issues) for series in self.series for season in series.seasons) +
        sum(len(episode.issues) for series in self.series 
            for season in series.seasons for episode in season.episodes)
    )
```

##### `get_items_with_issues()`
Returns all items that have validation issues.

```python
def get_items_with_issues(self) -> list[MediaItem]:
    """Get all items with validation issues."""
    items = []
    
    # Add movies with issues
    for movie in self.movies:
        if movie.has_issues:
            items.append(movie)
    
    # Add series, seasons, and episodes with issues
    for series in self.series:
        if series.has_issues:
            items.append(series)
        for season in series.seasons:
            if season.has_issues:
                items.append(season)
            for episode in season.episodes:
                if episode.has_issues:
                    items.append(episode)
    
    return items
```

#### Usage Examples

```python
# Analyze scan results
result = scanner.scan()

print(f"Scan completed in {result.duration:.2f} seconds")
print(f"Found {result.total_items} items with {result.total_issues} issues")

# Calculate statistics
movies_with_issues = sum(1 for movie in result.movies if movie.has_issues)
series_with_issues = sum(1 for series in result.series if series.has_issues)

print(f"Movies with issues: {movies_with_issues}/{len(result.movies)}")
print(f"Series with issues: {series_with_issues}/{len(result.series)}")

# Get issue breakdown by severity
error_count = 0
warning_count = 0

for item in result.get_items_with_issues():
    for issue in item.issues:
        if issue.severity == ValidationStatus.ERROR:
            error_count += 1
        elif issue.severity == ValidationStatus.WARNING:
            warning_count += 1

print(f"Errors: {error_count}, Warnings: {warning_count}")
```

## Model Relationships

### Hierarchy Structure

```
ScanResult
├── movies: list[MovieItem]
│   ├── assets: MediaAssets
│   ├── video_info: VideoInfo
│   └── issues: list[ValidationIssue]
│
└── series: list[SeriesItem]
    ├── assets: MediaAssets
    ├── issues: list[ValidationIssue]
    └── seasons: list[SeasonItem]
        ├── assets: MediaAssets
        ├── issues: list[ValidationIssue]
        └── episodes: list[EpisodeItem]
            ├── assets: MediaAssets
            ├── video_info: VideoInfo
            └── issues: list[ValidationIssue]
```

### Navigation Examples

```python
# Navigate through hierarchy
for series in result.series:
    print(f"Series: {series.name}")
    
    for season in series.seasons:
        print(f"  Season {season.season_number}: {len(season.episodes)} episodes")
        
        for episode in season.episodes:
            episode_id = f"S{episode.season_number:02d}E{episode.episode_number:02d}"
            status_icon = "❌" if episode.has_issues else "✅"
            print(f"    {status_icon} {episode_id}: {episode.name}")

# Find all H.264 videos across all content
h264_videos = []

# Check movies
for movie in result.movies:
    if movie.video_info and movie.video_info.codec == CodecType.H264:
        h264_videos.append(movie.video_info.path)

# Check TV episodes  
for series in result.series:
    for season in series.seasons:
        for episode in season.episodes:
            if episode.video_info and episode.video_info.codec == CodecType.H264:
                h264_videos.append(episode.video_info.path)

print(f"Found {len(h264_videos)} H.264 videos for re-encoding")
```

## Model Serialization

### JSON Serialization

Models can be serialized to JSON for reports and data exchange:

```python
import json
from pathlib import Path

def serialize_media_item(item: MediaItem) -> dict:
    """Serialize MediaItem to dictionary."""
    return {
        "name": item.name,
        "path": str(item.path),
        "type": item.type.name.lower(),
        "status": item.status.value,
        "assets": {
            "posters": [str(p) for p in item.assets.posters],
            "backgrounds": [str(p) for p in item.assets.backgrounds],
            "banners": [str(p) for p in item.assets.banners],
            "trailers": [str(p) for p in item.assets.trailers],
            "title_cards": [str(p) for p in item.assets.title_cards]
        },
        "issues": [
            {
                "category": issue.category,
                "message": issue.message,
                "severity": issue.severity.value,
                "details": issue.details
            }
            for issue in item.issues
        ],
        "metadata": item.metadata
    }

# Serialize movie with video info
def serialize_movie(movie: MovieItem) -> dict:
    """Serialize MovieItem to dictionary."""
    data = serialize_media_item(movie)
    data.update({
        "year": movie.year,
        "imdb_id": movie.imdb_id,
        "tmdb_id": movie.tmdb_id,
        "quality": movie.quality,
        "source": movie.source,
        "release_group": movie.release_group
    })
    
    if movie.video_info:
        data["video_info"] = {
            "path": str(movie.video_info.path),
            "codec": movie.video_info.codec.value if movie.video_info.codec else None,
            "resolution": movie.video_info.resolution,
            "duration": movie.video_info.duration,
            "bitrate": movie.video_info.bitrate,
            "size": movie.video_info.size
        }
    
    return data

# Usage
movie_data = serialize_movie(movie)
with open("movie.json", "w") as f:
    json.dump(movie_data, f, indent=2)
```

### Deserialization

```python
def deserialize_movie(data: dict) -> MovieItem:
    """Deserialize dictionary to MovieItem."""
    
    # Create assets
    assets = MediaAssets(
        posters=[Path(p) for p in data.get("assets", {}).get("posters", [])],
        backgrounds=[Path(p) for p in data.get("assets", {}).get("backgrounds", [])],
        banners=[Path(p) for p in data.get("assets", {}).get("banners", [])],
        trailers=[Path(p) for p in data.get("assets", {}).get("trailers", [])],
        title_cards=[Path(p) for p in data.get("assets", {}).get("title_cards", [])]
    )
    
    # Create validation issues
    issues = []
    for issue_data in data.get("issues", []):
        issue = ValidationIssue(
            category=issue_data["category"],
            message=issue_data["message"],
            severity=ValidationStatus(issue_data["severity"]),
            details=issue_data.get("details", {})
        )
        issues.append(issue)
    
    # Create video info if present
    video_info = None
    if "video_info" in data and data["video_info"]:
        vi_data = data["video_info"]
        video_info = VideoInfo(
            path=Path(vi_data["path"]),
            codec=CodecType(vi_data["codec"]) if vi_data.get("codec") else None,
            resolution=tuple(vi_data["resolution"]) if vi_data.get("resolution") else None,
            duration=vi_data.get("duration"),
            bitrate=vi_data.get("bitrate"),
            size=vi_data.get("size", 0)
        )
    
    # Create movie
    movie = MovieItem(
        path=Path(data["path"]),
        name=data["name"],
        assets=assets,
        issues=issues,
        metadata=data.get("metadata", {}),
        year=data.get("year"),
        imdb_id=data.get("imdb_id"),
        tmdb_id=data.get("tmdb_id"),
        quality=data.get("quality"),
        source=data.get("source"),
        release_group=data.get("release_group"),
        video_info=video_info
    )
    
    return movie

# Usage
with open("movie.json") as f:
    movie_data = json.load(f)
movie = deserialize_movie(movie_data)
```

## Best Practices

### Model Usage

1. **Immutability**: Treat models as immutable after creation when possible
2. **Validation**: Validate data when creating models programmatically
3. **Type Hints**: Use proper type hints for better IDE support
4. **Error Handling**: Handle missing or invalid data gracefully

### Performance Considerations

1. **Lazy Loading**: Load video info only when needed
2. **Memory Management**: Clear large objects when no longer needed
3. **Batch Processing**: Process models in batches for large libraries
4. **Caching**: Use caching for expensive operations

### Data Integrity

1. **Path Validation**: Ensure all paths are valid and accessible
2. **Consistency Checks**: Validate relationships between models
3. **Schema Versioning**: Handle model changes gracefully
4. **Backup**: Maintain backups of important scan results