# Component Details

This document provides detailed information about each component in the Media Audit system, including their interfaces, responsibilities, and implementation details.

## Core Components

### Command Line Interface (CLI)

#### Location: `src/media_audit/cli.py`

**Purpose**: Primary entry point for user interactions with the system.

**Key Classes**:
- Main CLI function with Click decorators
- Command handlers for `scan` and `init-config`

**Responsibilities**:
- Parse command-line arguments and options
- Load and validate configuration files
- Initialize and orchestrate the scanning process
- Display progress information and results
- Handle user interruptions (ESC key, Ctrl+C)
- Generate appropriate exit codes for automation

**Interface Design**:
```python
@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option()
def cli(ctx: click.Context) -> None:
    """Media Audit - Scan and validate your media library."""

@cli.command()
@click.option("--roots", "-r", multiple=True)
@click.option("--config", "-c", type=click.Path(exists=True, path_type=Path))
# ... other options
def scan(/* parameters */) -> None:
    """Scan media libraries and generate reports."""
```

**Key Features**:
- **Rich Console Integration**: Uses Rich library for beautiful progress bars and output formatting
- **Keyboard Monitoring**: Cross-platform ESC key detection for scan cancellation
- **Error Handling**: Comprehensive error handling with appropriate exit codes
- **Configuration Override**: Command-line options override configuration file values

**Usage Patterns**:
```python
# Basic usage
media-audit scan --roots "/media" --report audit.html

# Advanced usage with configuration
media-audit scan --config production.yaml --workers 8 --open
```

---

### Configuration System

#### Location: `src/media_audit/config.py`

**Purpose**: Centralized configuration management with validation and type safety.

**Key Classes**:
```python
@dataclass
class ScanConfig:
    """Configuration for media scanning."""
    root_paths: list[Path]
    profiles: list[str]
    allowed_codecs: list[CodecType]
    concurrent_workers: int
    cache_enabled: bool
    # ... other fields

@dataclass  
class ReportConfig:
    """Configuration for report generation."""
    output_path: Path | None
    json_path: Path | None
    auto_open: bool
    # ... other fields

@dataclass
class Config:
    """Main configuration container."""
    scan: ScanConfig
    report: ReportConfig
```

**Responsibilities**:
- Load configuration from YAML files
- Validate configuration values and types
- Provide default values for missing options
- Convert between different data formats (strings to Paths, etc.)
- Handle environment variable expansion

**Configuration Hierarchy**:
1. Command-line arguments (highest priority)
2. Environment variables
3. Configuration file (`--config` option)
4. Default configuration file locations
5. Built-in defaults (lowest priority)

**Validation Features**:
- Type checking with dataclass field types
- Path existence validation
- Enum value validation for constrained choices
- Range validation for numeric values

**Example Configuration**:
```yaml
scan:
  root_paths:
    - "/mnt/movies"
    - "/mnt/tv"
  profiles: ["plex", "jellyfin"]
  allowed_codecs: ["hevc", "av1"]
  concurrent_workers: 8
  cache_enabled: true

report:
  output_path: "daily-audit.html"
  json_path: "daily-audit.json"
  auto_open: false
  problems_only: true
```

---

### Media Scanner

#### Location: `src/media_audit/scanner/scanner.py`

**Purpose**: Orchestrates the entire media scanning process with concurrent processing and progress tracking.

**Key Classes**:
```python
class MediaScanner:
    """Scans media libraries and validates content."""
    
    def __init__(self, config: ScanConfig):
        self.config = config
        self.cache = MediaCache(...)
        self.movie_parser = MovieParser(...)
        self.tv_parser = TVParser(...)
        self.validator = MediaValidator(...)
```

**Responsibilities**:
- Discover media directories in configured root paths
- Coordinate concurrent processing of media items
- Manage progress reporting and user interaction
- Handle scan cancellation and cleanup
- Collect and aggregate scan results
- Integrate with caching system for performance

**Scanning Strategy**:
1. **Directory Discovery**: Identify Movies/, TV Shows/, and mixed content directories
2. **Content Type Detection**: Determine whether directories contain movies or TV shows
3. **Concurrent Processing**: Use ThreadPoolExecutor for parallel processing
4. **Progress Tracking**: Real-time progress updates with Rich progress bars
5. **Error Collection**: Collect but don't stop on individual item failures

**Threading Architecture**:
```python
def _scan_movies(self, movies_dir: Path, result: ScanResult) -> None:
    if self.config.concurrent_workers > 1:
        with ThreadPoolExecutor(max_workers=self.config.concurrent_workers) as executor:
            futures = {}
            for movie_dir in movie_dirs:
                future = executor.submit(self._process_movie, movie_dir)
                futures[future] = movie_dir
            
            for future in as_completed(futures):
                movie = future.result()
                if movie:
                    result.movies.append(movie)
```

**Cancellation Handling**:
- Cross-platform keyboard monitoring (ESC key)
- Thread-safe cancellation flags
- Graceful shutdown of worker threads
- Partial results preservation

**Performance Optimization**:
- Configurable worker thread count
- Cache integration at multiple levels
- Memory-efficient processing
- Batch processing for large libraries

---

### Content Parsers

#### Location: `src/media_audit/parsers/`

**Purpose**: Extract structured information from media directory hierarchies and files.

#### Base Parser

**File**: `src/media_audit/parsers/base.py`

```python
class BaseParser(ABC):
    """Abstract base class for media parsers."""
    
    def __init__(self, patterns: CompiledPatterns, cache: MediaCache | None = None):
        self.patterns = patterns
        self.cache = cache
    
    @abstractmethod
    def parse(self, directory: Path) -> MediaItem | None:
        """Parse directory and return media item."""
        pass
```

**Common Functionality**:
- Asset discovery using regex patterns
- Video file identification
- Metadata extraction from filenames
- Caching integration
- Error handling and recovery

#### Movie Parser

**File**: `src/media_audit/parsers/movie.py`

**Responsibilities**:
- Identify movie directories by structure and naming
- Extract movie metadata (title, year, quality, source, etc.)
- Find and categorize assets (posters, backgrounds, trailers)
- Identify primary video file
- Create complete `MovieItem` objects

**Movie Detection Logic**:
```python
def is_movie_directory(self, directory: Path) -> bool:
    """Check if directory represents a movie."""
    # 1. Contains video files
    video_files = self.find_video_files(directory)
    if not video_files:
        return False
    
    # 2. Directory name matches movie patterns
    movie_patterns = [
        r'^(.+?)\s*\((\d{4})\).*$',  # Movie (Year)
        r'^(.+?)\s*\.(\d{4})\..*$',   # Movie.Year.
        # ... other patterns
    ]
    
    # 3. No season/episode structure
    return not self._has_tv_structure(directory)
```

**Metadata Extraction**:
- **Title and Year**: Extracted from directory name using regex patterns
- **Quality**: Resolution indicators (1080p, 4K, etc.)
- **Source**: Media source (BluRay, WEBDL, WEBRip, etc.)
- **Codec**: Video codec information from filename
- **Release Group**: Release group identification

#### TV Parser

**File**: `src/media_audit/parsers/tv.py`

**Responsibilities**:
- Identify TV series directories by season/episode structure
- Parse hierarchical TV content (series → seasons → episodes)
- Extract episode-specific information (season/episode numbers, titles)
- Handle various episode naming conventions
- Create complete `SeriesItem` hierarchies

**TV Show Detection Logic**:
```python
def is_tv_directory(self, directory: Path) -> bool:
    """Check if directory represents a TV show."""
    # Look for season directories
    season_patterns = [
        r'^Season\s*(\d+)$',
        r'^S(\d+)$',
        r'^(\d+)$',
    ]
    
    for item in directory.iterdir():
        if item.is_dir():
            for pattern in season_patterns:
                if re.match(pattern, item.name, re.IGNORECASE):
                    return True
    return False
```

**Hierarchical Processing**:
1. **Series Level**: Extract series metadata and assets
2. **Season Level**: Identify seasons, extract season-specific assets
3. **Episode Level**: Parse individual episodes, extract video info and assets

**Episode Naming Support**:
- `S01E01` format (standard)
- `1x01` format (alternative)
- `Season 1 Episode 1` format (verbose)
- Various separators and padding

---

### Validation Engine

#### Location: `src/media_audit/validator.py`

**Purpose**: Apply quality rules and standards to media items, generating actionable validation issues.

**Key Classes**:
```python
class MediaValidator:
    """Validates media items against configured rules."""
    
    def __init__(self, config: ScanConfig, cache: MediaCache | None = None):
        self.config = config
        self.allowed_codecs = set(config.allowed_codecs)
        self.cache = cache
```

**Validation Hierarchy**:
- **Movie Validation**: Asset requirements, video standards
- **Series Validation**: Series-level assets, hierarchical validation
- **Season Validation**: Season-specific requirements
- **Episode Validation**: Episode assets and video standards

**Validation Rules**:

1. **Asset Validation**:
   - Required assets: posters, backgrounds
   - Optional assets: trailers, banners, title cards
   - Multiple asset support (poster1.jpg, poster2.jpg)

2. **Video Validation**:
   - Codec compliance checking
   - Video file presence validation
   - FFprobe integration for technical analysis

3. **Structural Validation**:
   - Directory naming conventions
   - File organization standards
   - Hierarchical consistency (TV shows)

**Issue Generation**:
```python
@dataclass
class ValidationIssue:
    category: str               # "assets", "encoding", "structure"
    message: str               # Human-readable description
    severity: ValidationStatus  # ERROR, WARNING, VALID
    details: dict[str, Any]    # Additional context
```

**Performance Optimizations**:
- Video analysis caching
- Batch validation support
- Early exit for valid items
- Configurable rule sets

---

### FFprobe Integration

#### Location: `src/media_audit/probe/ffprobe.py`

**Purpose**: Analyze video files using FFmpeg's FFprobe tool to extract technical metadata.

**Key Functions**:
```python
def probe_video(
    file_path: Path,
    cache: MediaCache | None = None,
    timeout: int = 60
) -> VideoInfo:
    """Probe video file and return detailed information."""
```

**Responsibilities**:
- Execute FFprobe subprocess with proper error handling
- Parse JSON output and normalize data
- Extract video codec, resolution, duration, bitrate
- Handle various video formats and edge cases
- Integrate with caching system for performance

**Data Extraction Process**:
1. **Command Execution**: Run FFprobe with JSON output format
2. **JSON Parsing**: Parse structured FFprobe output
3. **Data Normalization**: Convert to standard internal formats
4. **Error Handling**: Graceful handling of analysis failures

**Codec Detection**:
```python
def _extract_codec(streams: list[dict]) -> CodecType:
    """Extract video codec from stream information."""
    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    if not video_streams:
        return CodecType.OTHER
    
    codec_name = video_streams[0].get('codec_name', '').lower()
    
    # Map codec names to enum values
    codec_mapping = {
        'hevc': CodecType.HEVC,
        'h265': CodecType.H265,
        'av1': CodecType.AV1,
        'h264': CodecType.H264,
        # ... more mappings
    }
    
    return codec_mapping.get(codec_name, CodecType.OTHER)
```

**Error Handling Strategies**:
- **Timeout Management**: Configurable timeouts for large files
- **Subprocess Errors**: Handle FFprobe execution failures
- **JSON Parsing**: Handle malformed or unexpected output
- **Missing Dependencies**: Graceful degradation when FFprobe unavailable

**Performance Considerations**:
- **Caching**: Cache probe results with file validation
- **Concurrent Execution**: Thread-safe probe operations
- **Resource Limits**: Prevent excessive resource usage
- **Batch Processing**: Efficient processing of multiple files

---

### Caching System

#### Location: `src/media_audit/cache.py`

**Purpose**: Provide intelligent caching to dramatically improve scan performance on subsequent runs.

**Key Classes**:
```python
class MediaCache:
    """Cache for media scan results."""
    
    def __init__(self, cache_dir: Path | None = None, enabled: bool = True):
        self.enabled = enabled
        self.cache_dir = cache_dir
        self.schema_version = generate_schema_hash()
        # ... initialization
```

**Cache Architecture**:

1. **FFprobe Cache** (`probe/` directory):
   - **Format**: Binary pickle files for performance
   - **Content**: Complete FFprobe JSON output and parsed data
   - **Validation**: File size and modification time checking
   - **Naming**: Hash-based filenames for collision avoidance

2. **Scan Cache** (`scan/` directory):
   - **Format**: JSON files for debugging and interoperability
   - **Content**: Parsed media item data (without video analysis)
   - **Validation**: Directory modification time checking
   - **Naming**: Content-type prefixed hash filenames

3. **Memory Cache**:
   - **Purpose**: In-session caching for repeated operations
   - **Lifetime**: Single scan session
   - **Benefits**: Eliminates duplicate parsing within single scan

**Cache Validation**:
```python
def _is_cache_valid(self, entry: CacheEntry, file_path: Path) -> bool:
    """Check if cache entry is still valid."""
    if not file_path.exists():
        return False
    
    # Check schema version compatibility
    if hasattr(entry, 'schema_version') and entry.schema_version != self.schema_version:
        return False
    
    # Check file modification
    try:
        stat = file_path.stat()
        return not (stat.st_mtime != entry.file_mtime or stat.st_size != entry.file_size)
    except OSError:
        return False
```

**Schema Management**:
- **Automatic Versioning**: Generate version hash from data model definitions
- **Migration Handling**: Clear incompatible cache automatically
- **Version Tracking**: Store schema version with each cache entry

**Performance Features**:
- **Statistics Tracking**: Hit/miss ratios and performance metrics
- **Cleanup Utilities**: Remove stale or invalid cache entries
- **Storage Optimization**: Efficient serialization formats

---

### Pattern Matching System

#### Location: `src/media_audit/patterns.py`

**Purpose**: Provide flexible, media server-specific file pattern recognition for asset discovery.

**Key Classes**:
```python
@dataclass
class MediaPatterns:
    """Collection of patterns for matching media files."""
    poster_patterns: list[str]
    background_patterns: list[str]
    banner_patterns: list[str]
    trailer_patterns: list[str]
    title_card_patterns: list[str]

@dataclass
class CompiledPatterns:
    """Compiled regex patterns for efficient matching."""
    poster_re: list[Pattern[str]]
    background_re: list[Pattern[str]]
    # ... other compiled patterns
```

**Supported Media Servers**:

1. **Plex Patterns**:
   ```python
   PLEX_PATTERNS = MediaPatterns(
       poster_patterns=[
           r"^poster\.",
           r"^folder\.",
           r"^movie\.",
           r"^poster-\d+\.",
       ],
       background_patterns=[
           r"^fanart\.",
           r"^background\.",
           r"-fanart\.",
       ],
       # ... more patterns
   )
   ```

2. **Jellyfin Patterns**:
   - Similar structure with Jellyfin-specific naming conventions
   - Support for numbered variants (backdrop1.jpg, backdrop2.jpg)

3. **Emby Patterns**:
   - Emby-specific patterns including extrafanart/ directory support

**Pattern Compilation**:
- Regex patterns compiled once for performance
- Case-insensitive matching by default
- Pattern optimization and ordering

**Usage in Parsers**:
```python
def find_assets(self, directory: Path) -> MediaAssets:
    """Find all assets in directory using configured patterns."""
    assets = MediaAssets()
    
    for file_path in directory.iterdir():
        if not file_path.is_file():
            continue
        
        filename = file_path.name
        
        # Check each pattern type
        for pattern in self.patterns.poster_re:
            if pattern.search(filename):
                assets.posters.append(file_path)
                break  # First match wins
    
    return assets
```

---

### Report Generators

#### Location: `src/media_audit/report/`

**Purpose**: Generate user-friendly reports in various formats from scan results.

#### HTML Report Generator

**File**: `src/media_audit/report/html.py`

**Responsibilities**:
- Generate interactive HTML reports with embedded CSS/JavaScript
- Create responsive design that works on desktop and mobile
- Implement search, filter, and sort functionality
- Support thumbnail display with Base64 encoding
- Handle large datasets efficiently

**Key Features**:
- **Interactive Elements**:
  - Search box for real-time filtering
  - Status filter dropdown (all, errors only, warnings only)
  - Sort options (name, status, issue count)
- **Visual Design**:
  - Fixed header for navigation
  - Color-coded status indicators
  - Responsive grid layouts
  - Print-friendly styling
- **Performance**:
  - Embedded resources (no external dependencies)
  - Efficient DOM manipulation
  - Lazy loading for large libraries

**Report Structure**:
```html
<!DOCTYPE html>
<html>
<head>
    <style>/* Embedded CSS */</style>
</head>
<body>
    <header class="fixed-header">
        <!-- Controls and navigation -->
    </header>
    <main>
        <section class="summary">
            <!-- Scan statistics -->
        </section>
        <section class="movies">
            <!-- Movie items -->
        </section>
        <section class="series">
            <!-- TV series items -->
        </section>
    </main>
    <script>/* Interactive JavaScript */</script>
</body>
</html>
```

#### JSON Report Generator

**File**: `src/media_audit/report/json.py`

**Responsibilities**:
- Serialize complete scan results to structured JSON
- Ensure data integrity and type consistency
- Support automation and integration use cases
- Provide machine-readable format for APIs

**JSON Schema Design**:
- **Hierarchical Structure**: Maintains parent-child relationships
- **Complete Data**: All scan results and metadata included
- **Type Safety**: Consistent data types throughout
- **Extensibility**: Schema designed for future enhancements

**Serialization Features**:
- Path objects converted to strings
- Enum values converted to string representations
- Datetime objects converted to ISO format
- Binary data excluded (suitable for JSON)

---

### Data Models

#### Location: `src/media_audit/models.py`

**Purpose**: Provide type-safe, structured representation of all media library data.

**Core Model Hierarchy**:
```python
MediaItem (Abstract Base)
├── MovieItem
└── SeriesItem
    └── seasons: list[SeasonItem]
        └── episodes: list[EpisodeItem]
```

**Key Models**:

1. **MediaItem** (Base Class):
   ```python
   @dataclass
   class MediaItem:
       path: Path
       name: str
       type: MediaType
       assets: MediaAssets
       issues: list[ValidationIssue]
       metadata: dict[str, Any]
   ```

2. **MovieItem**:
   ```python
   @dataclass
   class MovieItem(MediaItem):
       year: int | None = None
       video_info: VideoInfo | None = None
       imdb_id: str | None = None
       tmdb_id: str | None = None
       release_group: str | None = None
       quality: str | None = None
       source: str | None = None
   ```

3. **VideoInfo**:
   ```python
   @dataclass
   class VideoInfo:
       path: Path
       codec: CodecType | None = None
       resolution: tuple[int, int] | None = None
       duration: float | None = None
       bitrate: int | None = None
       size: int = 0
       raw_info: dict[str, Any] = field(default_factory=dict)
   ```

**Design Principles**:
- **Immutability**: Models treated as immutable after creation
- **Type Safety**: Full type hints for IDE support and validation
- **Extensibility**: Metadata dictionary for additional fields
- **Relationships**: Clear parent-child relationships maintained

**Automatic Properties**:
- **Status Calculation**: Derived from validation issues
- **Statistics**: Automatic counts and aggregations
- **Validation**: Built-in data consistency checks

---

## Component Interactions

### Parser-Cache Integration

```python
def parse(self, directory: Path) -> MovieItem | None:
    """Parse directory with caching support."""
    
    # Check cache first
    if self.cache:
        cached_data = self.cache.get_media_item(directory, "movie")
        if cached_data:
            return self.deserialize_movie(cached_data)
    
    # Parse directory
    movie = self._parse_directory(directory)
    
    # Cache result
    if self.cache and movie:
        serialized = self.serialize_movie(movie)
        self.cache.set_media_item(directory, "movie", serialized)
    
    return movie
```

### Validator-Probe Integration

```python
def _validate_video_encoding(self, item: MediaItem, video_info: VideoInfo) -> None:
    """Validate video encoding with probe integration."""
    
    # Probe video if not already done
    if video_info.codec is None:
        try:
            probed_info = probe_video(video_info.path, cache=self.cache)
            # Update video_info with probed data
            video_info.codec = probed_info.codec
            video_info.resolution = probed_info.resolution
            # ... other fields
        except Exception as e:
            # Handle probe failure
            item.issues.append(ValidationIssue(
                category="video",
                message=f"Failed to probe video file: {e}",
                severity=ValidationStatus.ERROR
            ))
            return
    
    # Continue with validation using probed data
    if video_info.codec not in self.allowed_codecs:
        # Generate codec issue
        pass
```

### Scanner-Reporter Integration

```python
def scan(self) -> ScanResult:
    """Perform scan and return results."""
    
    # ... scanning logic ...
    
    result = ScanResult(
        scan_time=datetime.now(),
        duration=time.time() - start_time,
        root_paths=self.config.root_paths,
        movies=movies,
        series=series,
        errors=errors
    )
    
    return result

# In CLI
result = scanner.scan()

# Generate reports
if config.report.output_path:
    html_generator = HTMLReportGenerator()
    html_generator.generate(result, config.report.output_path, config.report.problems_only)

if config.report.json_path:
    json_generator = JSONReportGenerator()
    json_generator.generate(result, config.report.json_path)
```

## Performance Characteristics

### Time Complexity

- **Directory Traversal**: O(n) where n is number of directories
- **Pattern Matching**: O(p×f) where p is patterns, f is files per directory
- **Video Analysis**: O(v×t) where v is video files, t is probe time per file
- **Validation**: O(i×r) where i is items, r is rules per item

### Space Complexity

- **Memory Usage**: O(i) where i is total items (linear with library size)
- **Cache Storage**: O(v+i) where v is video files, i is items
- **Report Size**: O(i×d) where i is items, d is data per item

### Scalability Limits

- **Maximum Items**: Limited by available memory (typically 100k+ items)
- **Concurrent Workers**: Limited by I/O capacity (typically 4-16 workers)
- **Cache Size**: Limited by disk space (typically 1-10GB for large libraries)

## Error Handling Strategies

### Graceful Degradation

1. **Missing FFprobe**: Continue with limited video analysis
2. **Permission Errors**: Skip inaccessible files, continue processing
3. **Corrupt Files**: Log errors, continue with remaining files
4. **Cache Failures**: Disable caching, continue with direct processing

### Error Recovery

1. **Partial Results**: Return results even with some failures
2. **Retry Logic**: Retry transient failures (network issues, etc.)
3. **Fallback Behavior**: Use alternative approaches when primary fails
4. **User Notification**: Clear error messages with suggested actions

### Monitoring and Debugging

1. **Structured Logging**: Consistent log format with context
2. **Error Aggregation**: Collect related errors for analysis
3. **Performance Metrics**: Track timing and resource usage
4. **Health Checks**: Verify system components are working

This detailed component documentation provides the foundation for understanding, maintaining, and extending the Media Audit system.