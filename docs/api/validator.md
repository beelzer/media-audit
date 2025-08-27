# Validator API Reference

This reference documents the validation system responsible for checking media items against configured rules and quality standards.

## Core Validator

### `MediaValidator`

Main validation class that applies rules to media items and generates validation issues.

```python
from media_audit.domain.validation import MediaValidator
from media_audit.infrastructure.config import ScanConfig

class MediaValidator:
    """Validates media items against configured rules."""

    def __init__(self, config: ScanConfig, cache: Any = None) -> None:
        """Initialize validator with configuration."""
```

#### Initialization

```python
# Create validator with scan configuration
config = ScanConfig(
    allowed_codecs=[CodecType.HEVC, CodecType.AV1],
    # ... other config options
)
validator = MediaValidator(config, cache=cache)
```

#### Properties

##### `config`

**Type**: `ScanConfig`
**Description**: Configuration containing validation rules and settings.

##### `allowed_codecs`

**Type**: `set[CodecType]`
**Description**: Set of acceptable video codecs derived from configuration.

##### `cache`

**Type**: `MediaCache | None`
**Description**: Optional caching system for video analysis results.

#### Core Methods

##### `validate()`

Main validation dispatcher that routes items to specific validators.

```python
def validate(self, item: MediaItem) -> None:
    """Validate a media item and add issues."""
```

**Process**:

1. Determines item type (`MovieItem`, `SeriesItem`, etc.)
2. Routes to appropriate specialized validator
3. Updates item's issues list in-place

**Usage**:

```python
# Validate any media item
validator.validate(movie_item)
validator.validate(series_item)

# Check results
if item.has_issues:
    for issue in item.issues:
        print(f"{issue.severity.value}: {issue.message}")
```

## Movie Validation

### `validate_movie()`

Comprehensive validation for movie items.

```python
def validate_movie(self, movie: MovieItem) -> None:
    """Validate a movie."""
```

#### Validation Rules

##### Required Assets

- **Poster Image**: `poster.jpg`, `folder.jpg`, `movie.jpg`
- **Background Image**: `fanart.jpg`, `background.jpg`, `backdrop.jpg`

##### Optional Assets

- **Trailer Video**: `*-trailer.mp4`, `Trailers/` directory

##### Video Requirements

- **Video File Present**: At least one video file must exist
- **Codec Compliance**: Video codec must be in allowed list
- **Analysis Success**: FFprobe must successfully analyze video

#### Example Validation Issues

```python
# Missing poster
ValidationIssue(
    category="assets",
    message="Missing poster image",
    severity=ValidationStatus.ERROR,
    details={"expected": ["poster.jpg", "folder.jpg", "movie.jpg"]}
)

# Missing background
ValidationIssue(
    category="assets",
    message="Missing background/fanart image",
    severity=ValidationStatus.ERROR,
    details={"expected": ["fanart.jpg", "background.jpg", "backdrop.jpg"]}
)

# Missing trailer (warning only)
ValidationIssue(
    category="assets",
    message="Missing trailer",
    severity=ValidationStatus.WARNING,
    details={"expected": ["*-trailer.mp4", "Trailers/"]}
)

# Codec issue
ValidationIssue(
    category="encoding",
    message="Video uses non-preferred codec: h264",
    severity=ValidationStatus.WARNING,
    details={
        "codec": "h264",
        "allowed": ["hevc", "av1"],
        "file": "movie.mkv"
    }
)
```

## TV Show Validation

### `validate_series()`

Validates TV series at the series level.

```python
def validate_series(self, series: SeriesItem) -> None:
    """Validate a TV series."""
```

#### Series-Level Rules

##### Required Assets

- **Series Poster**: `poster.jpg`, `folder.jpg`
- **Series Background**: `fanart.jpg`, `background.jpg`

##### Optional Assets

- **Series Banner**: `banner.jpg` (generates warning if missing)

##### Hierarchical Validation

- Automatically validates all seasons within the series
- Each season validates its episodes

#### Example Series Issues

```python
# Missing series poster
ValidationIssue(
    category="assets",
    message="Missing series poster",
    severity=ValidationStatus.ERROR,
    details={"expected": ["poster.jpg", "folder.jpg"]}
)

# Missing banner (optional)
ValidationIssue(
    category="assets",
    message="Missing series banner (optional)",
    severity=ValidationStatus.WARNING,
    details={"expected": ["banner.jpg"]}
)
```

### `validate_season()`

Validates individual TV seasons.

```python
def validate_season(self, season: SeasonItem) -> None:
    """Validate a TV season."""
```

#### Season-Level Rules

##### Optional Assets

- **Season Poster**: `SeasonXX.jpg` (e.g., `Season01.jpg`)

##### Episode Validation

- Automatically validates all episodes in the season

#### Example Season Issues

```python
# Missing season poster
ValidationIssue(
    category="assets",
    message="Missing poster for Season 1",
    severity=ValidationStatus.WARNING,
    details={"expected": ["Season01.jpg"]}
)
```

### `validate_episode()`

Validates individual TV episodes.

```python
def validate_episode(self, episode: EpisodeItem) -> None:
    """Validate a TV episode."""
```

#### Episode-Level Rules

##### Optional Assets

- **Title Card**: `S01E01.jpg` (matching episode filename)

##### Video Requirements

- **Video File Present**: Episode must have associated video file
- **Codec Compliance**: Same codec rules as movies

#### Example Episode Issues

```python
# Missing title card
ValidationIssue(
    category="assets",
    message="Missing title card for S01E01",
    severity=ValidationStatus.WARNING,
    details={"expected": ["S01E01.jpg"]}
)

# No video file
ValidationIssue(
    category="video",
    message="No video file found for episode",
    severity=ValidationStatus.ERROR
)
```

## Video Validation

### `_validate_video_encoding()`

Comprehensive video file validation.

```python
def _validate_video_encoding(self, item: MediaItem, video_info: VideoInfo) -> None:
    """Validate video encoding."""
```

#### Validation Process

1. **Probe Video**: Use FFprobe to analyze if not already done
2. **Check Codec**: Verify codec is in allowed list
3. **Generate Issues**: Create appropriate validation issues

#### Video Analysis Integration

```python
# Automatic video probing
if video_info.codec is None:
    try:
        probed_info = probe_video(video_info.path, cache=self.cache)
        video_info.codec = probed_info.codec
        video_info.resolution = probed_info.resolution
        video_info.duration = probed_info.duration
        video_info.bitrate = probed_info.bitrate
        video_info.size = probed_info.size
        video_info.raw_info = probed_info.raw_info
    except Exception as e:
        # Handle probe failures
        item.issues.append(
            ValidationIssue(
                category="video",
                message=f"Failed to probe video file: {e}",
                severity=ValidationStatus.ERROR,
                details={"file": str(video_info.path)}
            )
        )
```

#### Codec-Specific Validation

```python
# Non-preferred codec warning
if video_info.codec not in self.allowed_codecs:
    item.issues.append(
        ValidationIssue(
            category="encoding",
            message=f"Video uses non-preferred codec: {video_info.codec.value}",
            severity=ValidationStatus.WARNING,
            details={
                "codec": video_info.codec.value,
                "allowed": [c.value for c in self.allowed_codecs],
                "file": video_info.path.name
            }
        )
    )

# Special H.264 recommendation
if video_info.codec == CodecType.H264:
    item.issues.append(
        ValidationIssue(
            category="encoding",
            message="Consider re-encoding from H.264 to HEVC/AV1 for better compression",
            severity=ValidationStatus.WARNING,
            details={"file": video_info.path.name}
        )
    )
```

## Asset Validation

### Trailer Detection

#### `_has_trailer_folder()`

Checks for dedicated trailer directories.

```python
def _has_trailer_folder(self, path: Path) -> bool:
    """Check if path has a Trailers folder."""
```

**Process**:

1. Look for `Trailers/` subdirectory
2. Verify it contains video files
3. Supported video extensions: `.mp4`, `.mkv`, `.mov`, `.avi`

**Usage**:

```python
# Check during movie validation
if not movie.assets.trailers and not self._has_trailer_folder(movie.path):
    # Generate missing trailer warning
    pass
```

## Custom Validation

### Extending MediaValidator

```python
from media_audit.domain.validation import MediaValidator

class CustomValidator(MediaValidator):
    """Enhanced validator with custom rules."""

    def __init__(self, config: ScanConfig, custom_rules: dict = None, cache=None):
        super().__init__(config, cache)
        self.custom_rules = custom_rules or {}

    def validate_movie(self, movie: MovieItem) -> None:
        """Enhanced movie validation."""
        # Run standard validation
        super().validate_movie(movie)

        # Add custom validations
        self._validate_movie_naming(movie)
        self._validate_movie_quality(movie)
        self._validate_movie_size(movie)

    def _validate_movie_naming(self, movie: MovieItem) -> None:
        """Validate movie naming conventions."""
        if not self.custom_rules.get("enforce_naming", False):
            return

        # Check for (Year) format
        import re
        expected_pattern = r'^.+ \(\d{4}\)$'

        if not re.match(expected_pattern, movie.name):
            movie.issues.append(
                ValidationIssue(
                    category="naming",
                    message="Movie folder should follow 'Title (Year)' format",
                    severity=ValidationStatus.ERROR,
                    details={
                        "current": movie.name,
                        "expected": "Title (Year)"
                    }
                )
            )

    def _validate_movie_quality(self, movie: MovieItem) -> None:
        """Validate quality indicators."""
        if not movie.video_info or not movie.video_info.resolution:
            return

        width, height = movie.video_info.resolution

        # Check for quality in filename
        quality_indicators = {
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "1440p": (2560, 1440),
            "4K": (3840, 2160),
            "2160p": (3840, 2160)
        }

        expected_quality = None
        for quality, (q_width, q_height) in quality_indicators.items():
            if width >= q_width * 0.9 and height >= q_height * 0.9:
                expected_quality = quality
                break

        if expected_quality and expected_quality not in movie.path.name:
            movie.issues.append(
                ValidationIssue(
                    category="naming",
                    message=f"Filename should include quality indicator: {expected_quality}",
                    severity=ValidationStatus.WARNING,
                    details={
                        "resolution": f"{width}x{height}",
                        "expected_quality": expected_quality
                    }
                )
            )

    def _validate_movie_size(self, movie: MovieItem) -> None:
        """Validate file size appropriateness."""
        if not movie.video_info or not movie.video_info.size:
            return

        size_gb = movie.video_info.size / (1024 ** 3)

        # Size recommendations by resolution
        if movie.video_info.resolution:
            width, height = movie.video_info.resolution

            if height >= 2160:  # 4K
                min_size, max_size = 15, 80
                quality_name = "4K"
            elif height >= 1080:  # 1080p
                min_size, max_size = 3, 25
                quality_name = "1080p"
            else:
                return  # Skip validation for lower resolutions

            if size_gb < min_size:
                movie.issues.append(
                    ValidationIssue(
                        category="quality",
                        message=f"{quality_name} movie file seems small (< {min_size}GB), may be low quality",
                        severity=ValidationStatus.WARNING,
                        details={"size_gb": round(size_gb, 2)}
                    )
                )
            elif size_gb > max_size:
                movie.issues.append(
                    ValidationIssue(
                        category="quality",
                        message=f"{quality_name} movie file is very large (> {max_size}GB), consider compression",
                        severity=ValidationStatus.WARNING,
                        details={"size_gb": round(size_gb, 2)}
                    )
                )

# Usage
custom_rules = {
    "enforce_naming": True,
    "validate_quality": True,
    "validate_size": True
}

validator = CustomValidator(config, custom_rules, cache)
validator.validate(movie)
```

### Rule-Based Validation

```python
from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class ValidationRule:
    """Represents a single validation rule."""
    name: str
    category: str
    severity: ValidationStatus
    check_function: Callable[[MediaItem], bool]
    message_template: str
    details_function: Callable[[MediaItem], dict[str, Any]] = None

class RuleBasedValidator(MediaValidator):
    """Validator that uses configurable rules."""

    def __init__(self, config: ScanConfig, cache=None):
        super().__init__(config, cache)
        self.rules = []
        self._setup_default_rules()

    def add_rule(self, rule: ValidationRule) -> None:
        """Add custom validation rule."""
        self.rules.append(rule)

    def _setup_default_rules(self) -> None:
        """Setup default validation rules."""

        # Rule: Movies must have posters
        self.add_rule(ValidationRule(
            name="movie_poster_required",
            category="assets",
            severity=ValidationStatus.ERROR,
            check_function=lambda item: (
                isinstance(item, MovieItem) and
                not item.assets.posters
            ),
            message_template="Missing poster image",
            details_function=lambda item: {"expected": ["poster.jpg", "folder.jpg"]}
        ))

        # Rule: Large files should be HEVC/AV1
        self.add_rule(ValidationRule(
            name="large_files_modern_codec",
            category="encoding",
            severity=ValidationStatus.WARNING,
            check_function=lambda item: (
                item.video_info and
                item.video_info.size > 10 * 1024**3 and  # > 10GB
                item.video_info.codec not in {CodecType.HEVC, CodecType.H265, CodecType.AV1}
            ),
            message_template="Large file should use modern codec (HEVC/AV1)",
            details_function=lambda item: {
                "size_gb": round(item.video_info.size / (1024**3), 2),
                "current_codec": item.video_info.codec.value
            }
        ))

    def validate(self, item: MediaItem) -> None:
        """Validate item using rules."""
        # Run standard validation first
        super().validate(item)

        # Apply custom rules
        for rule in self.rules:
            if rule.check_function(item):
                details = {}
                if rule.details_function:
                    details = rule.details_function(item)

                issue = ValidationIssue(
                    category=rule.category,
                    message=rule.message_template,
                    severity=rule.severity,
                    details=details
                )
                item.issues.append(issue)

# Usage
validator = RuleBasedValidator(config)

# Add custom rule
custom_rule = ValidationRule(
    name="anime_episode_count",
    category="structure",
    severity=ValidationStatus.WARNING,
    check_function=lambda item: (
        isinstance(item, SeriesItem) and
        "anime" in item.metadata.get("genre", "").lower() and
        item.total_episodes > 100
    ),
    message_template="Anime series has unusually high episode count",
    details_function=lambda item: {"episode_count": item.total_episodes}
)

validator.add_rule(custom_rule)
```

## Validation Configuration

### Configuration-Driven Validation

```python
# Extended configuration for validation rules
@dataclass
class ValidationConfig:
    """Configuration for validation rules."""

    # Asset requirements
    require_posters: bool = True
    require_backgrounds: bool = True
    require_trailers: bool = False
    require_banners: bool = False
    require_title_cards: bool = False

    # Codec preferences
    allowed_codecs: list[CodecType] = field(default_factory=lambda: [CodecType.HEVC, CodecType.AV1])
    warn_h264: bool = True

    # Quality thresholds
    min_1080p_size_gb: float = 3.0
    max_1080p_size_gb: float = 25.0
    min_4k_size_gb: float = 15.0
    max_4k_size_gb: float = 80.0

    # Naming requirements
    enforce_year_format: bool = False
    require_quality_tag: bool = False

class ConfigurableValidator(MediaValidator):
    """Validator using detailed configuration."""

    def __init__(self, scan_config: ScanConfig, validation_config: ValidationConfig, cache=None):
        super().__init__(scan_config, cache)
        self.validation_config = validation_config

    def validate_movie(self, movie: MovieItem) -> None:
        """Validate movie with configurable rules."""

        # Asset validation based on config
        if self.validation_config.require_posters and not movie.assets.posters:
            movie.issues.append(
                ValidationIssue(
                    category="assets",
                    message="Missing required poster image",
                    severity=ValidationStatus.ERROR,
                    details={"expected": ["poster.jpg", "folder.jpg"]}
                )
            )

        if self.validation_config.require_backgrounds and not movie.assets.backgrounds:
            movie.issues.append(
                ValidationIssue(
                    category="assets",
                    message="Missing required background image",
                    severity=ValidationStatus.ERROR,
                    details={"expected": ["fanart.jpg", "background.jpg"]}
                )
            )

        trailer_severity = ValidationStatus.ERROR if self.validation_config.require_trailers else ValidationStatus.WARNING
        if not movie.assets.trailers and not self._has_trailer_folder(movie.path):
            movie.issues.append(
                ValidationIssue(
                    category="assets",
                    message="Missing trailer" if self.validation_config.require_trailers else "Missing trailer (optional)",
                    severity=trailer_severity,
                    details={"expected": ["*-trailer.mp4", "Trailers/"]}
                )
            )

        # Video validation
        if movie.video_info:
            self._validate_video_with_config(movie, movie.video_info)

    def _validate_video_with_config(self, item: MediaItem, video_info: VideoInfo) -> None:
        """Validate video with configuration."""

        # Codec validation
        if video_info.codec not in self.validation_config.allowed_codecs:
            item.issues.append(
                ValidationIssue(
                    category="encoding",
                    message=f"Video uses non-preferred codec: {video_info.codec.value}",
                    severity=ValidationStatus.WARNING,
                    details={
                        "codec": video_info.codec.value,
                        "allowed": [c.value for c in self.validation_config.allowed_codecs]
                    }
                )
            )

        # H.264 specific warning
        if self.validation_config.warn_h264 and video_info.codec == CodecType.H264:
            item.issues.append(
                ValidationIssue(
                    category="encoding",
                    message="Consider re-encoding from H.264 to HEVC/AV1",
                    severity=ValidationStatus.WARNING,
                    details={"current_codec": "h264"}
                )
            )

        # Size validation
        if video_info.size and video_info.resolution:
            self._validate_file_size(item, video_info)

    def _validate_file_size(self, item: MediaItem, video_info: VideoInfo) -> None:
        """Validate file size against thresholds."""
        size_gb = video_info.size / (1024 ** 3)
        width, height = video_info.resolution

        if height >= 2160:  # 4K
            min_size = self.validation_config.min_4k_size_gb
            max_size = self.validation_config.max_4k_size_gb
            quality = "4K"
        elif height >= 1080:  # 1080p
            min_size = self.validation_config.min_1080p_size_gb
            max_size = self.validation_config.max_1080p_size_gb
            quality = "1080p"
        else:
            return  # No validation for lower resolutions

        if size_gb < min_size:
            item.issues.append(
                ValidationIssue(
                    category="quality",
                    message=f"{quality} file seems small (< {min_size}GB), may be low quality",
                    severity=ValidationStatus.WARNING,
                    details={"size_gb": round(size_gb, 2), "min_expected": min_size}
                )
            )
        elif size_gb > max_size:
            item.issues.append(
                ValidationIssue(
                    category="quality",
                    message=f"{quality} file is very large (> {max_size}GB), consider compression",
                    severity=ValidationStatus.WARNING,
                    details={"size_gb": round(size_gb, 2), "max_expected": max_size}
                )
            )

# Usage
validation_config = ValidationConfig(
    require_posters=True,
    require_backgrounds=True,
    require_trailers=False,
    warn_h264=True,
    min_1080p_size_gb=2.0,  # More lenient
    max_4k_size_gb=100.0    # Allow larger 4K files
)

validator = ConfigurableValidator(scan_config, validation_config, cache)
```

## Performance Optimization

### Batch Validation

```python
class BatchValidator(MediaValidator):
    """Validator optimized for batch processing."""

    def validate_batch(self, items: list[MediaItem]) -> None:
        """Validate multiple items efficiently."""

        # Group items by type for optimized processing
        movies = [item for item in items if isinstance(item, MovieItem)]
        series = [item for item in items if isinstance(item, SeriesItem)]

        # Batch video analysis
        video_items = [(item, item.video_info) for item in items
                      if hasattr(item, 'video_info') and item.video_info]

        self._batch_video_analysis(video_items)

        # Validate in batches
        for movie in movies:
            self.validate_movie(movie)

        for series_item in series:
            self.validate_series(series_item)

    def _batch_video_analysis(self, video_items: list[tuple[MediaItem, VideoInfo]]) -> None:
        """Analyze multiple videos efficiently."""
        from concurrent.futures import ThreadPoolExecutor

        def analyze_video(item_video_pair):
            item, video_info = item_video_pair
            if video_info.codec is None:
                try:
                    from media_audit.infrastructure.probe import probe_video
                    probed = probe_video(video_info.path, cache=self.cache)
                    video_info.codec = probed.codec
                    video_info.resolution = probed.resolution
                    video_info.duration = probed.duration
                except Exception as e:
                    item.issues.append(
                        ValidationIssue(
                            category="video",
                            message=f"Failed to analyze video: {e}",
                            severity=ValidationStatus.ERROR
                        )
                    )

        # Analyze videos concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(analyze_video, video_items)
```

## Integration Examples

### Custom Media Server Validation

```python
class PlexValidator(MediaValidator):
    """Validator specific to Plex requirements."""

    def validate_movie(self, movie: MovieItem) -> None:
        """Validate movie for Plex compatibility."""
        super().validate_movie(movie)

        # Plex-specific validations
        self._validate_plex_naming(movie)
        self._validate_plex_assets(movie)

    def _validate_plex_naming(self, movie: MovieItem) -> None:
        """Validate Plex naming requirements."""
        # Plex prefers (Year) format
        if movie.year and f"({movie.year})" not in movie.path.name:
            movie.issues.append(
                ValidationIssue(
                    category="naming",
                    message="Plex prefers movie folders with (Year) format",
                    severity=ValidationStatus.WARNING,
                    details={"suggestion": f"{movie.name} ({movie.year})"}
                )
            )

    def _validate_plex_assets(self, movie: MovieItem) -> None:
        """Validate Plex asset preferences."""
        # Plex prefers poster.jpg over folder.jpg
        if movie.assets.posters:
            poster_names = [p.name for p in movie.assets.posters]
            if "poster.jpg" not in poster_names and "folder.jpg" in poster_names:
                movie.issues.append(
                    ValidationIssue(
                        category="assets",
                        message="Plex prefers poster.jpg over folder.jpg",
                        severity=ValidationStatus.WARNING,
                        details={"current": "folder.jpg", "preferred": "poster.jpg"}
                    )
                )

class JellyfinValidator(MediaValidator):
    """Validator specific to Jellyfin requirements."""

    def validate_episode(self, episode: EpisodeItem) -> None:
        """Validate episode for Jellyfin."""
        super().validate_episode(episode)

        # Jellyfin-specific episode naming
        self._validate_jellyfin_episode_naming(episode)

    def _validate_jellyfin_episode_naming(self, episode: EpisodeItem) -> None:
        """Validate Jellyfin episode naming preferences."""
        # Jellyfin handles various formats, but SxxExx is preferred
        episode_pattern = f"S{episode.season_number:02d}E{episode.episode_number:02d}"

        if episode_pattern not in episode.path.name:
            episode.issues.append(
                ValidationIssue(
                    category="naming",
                    message="Jellyfin prefers SxxExx episode naming format",
                    severity=ValidationStatus.WARNING,
                    details={"preferred": episode_pattern}
                )
            )
```

## Best Practices

### Validation Design

1. **Severity Levels**: Use appropriate severity for different types of issues
2. **Detailed Messages**: Provide clear, actionable error messages
3. **Context Information**: Include relevant details in issue metadata
4. **Performance**: Cache expensive operations like video analysis

### Rule Organization

1. **Separation of Concerns**: Separate different types of validation logic
2. **Configuration**: Make validation rules configurable
3. **Extensibility**: Design for easy addition of new validation rules
4. **Testing**: Thoroughly test validation logic with real-world data

### Error Handling

1. **Graceful Degradation**: Continue validation even when individual checks fail
2. **Clear Errors**: Provide specific error messages for debugging
3. **Resource Management**: Handle file access errors appropriately
4. **Logging**: Log validation issues for monitoring and debugging
