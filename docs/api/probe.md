# FFprobe API Reference

This reference documents the FFprobe integration system for analyzing video files and extracting technical metadata.

## Core Functions

### `probe_video()`

Main function for analyzing video files using FFprobe.

```python
from media_audit.probe import probe_video
from pathlib import Path

def probe_video(
    file_path: Path,
    cache: MediaCache | None = None,
    timeout: int = 60
) -> VideoInfo:
    """Probe video file and return detailed information."""
```

#### Parameters

##### `file_path`

**Type**: `Path`
**Description**: Path to video file to analyze.
**Requirements**: File must exist and be readable.

##### `cache`

**Type**: `MediaCache | None`
**Default**: `None`
**Description**: Optional cache for storing/retrieving probe results.

##### `timeout`

**Type**: `int`
**Default**: `60`
**Description**: Maximum time in seconds to wait for FFprobe execution.

#### Returns

Returns a `VideoInfo` object containing:

- **codec**: Detected video codec
- **resolution**: Video dimensions (width, height)
- **duration**: Video length in seconds
- **bitrate**: Video bitrate in bits per second
- **size**: File size in bytes
- **raw_info**: Complete FFprobe JSON output

#### Usage Examples

```python
from pathlib import Path
from media_audit.probe import probe_video

# Basic video probing
video_path = Path("/movies/The Matrix (1999)/The Matrix (1999).mkv")
video_info = probe_video(video_path)

print(f"Codec: {video_info.codec.value}")
print(f"Resolution: {video_info.resolution[0]}x{video_info.resolution[1]}")
print(f"Duration: {video_info.duration / 60:.1f} minutes")
print(f"Bitrate: {video_info.bitrate / 1_000_000:.1f} Mbps")
print(f"File size: {video_info.size / 1024**3:.2f} GB")

# With caching
from media_audit.cache import MediaCache

cache = MediaCache()
video_info = probe_video(video_path, cache=cache)

# Subsequent calls use cached results
cached_info = probe_video(video_path, cache=cache)  # Faster
```

## FFprobe Integration

### Command Execution

The probe system executes FFprobe as a subprocess with structured output:

```python
def _execute_ffprobe(file_path: Path, timeout: int = 60) -> dict:
    """Execute FFprobe and return JSON results."""

    cmd = [
        'ffprobe',
        '-v', 'quiet',           # Suppress verbose output
        '-print_format', 'json', # JSON output format
        '-show_format',          # Show container format info
        '-show_streams',         # Show stream info
        str(file_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )
        return json.loads(result.stdout)

    except subprocess.TimeoutExpired:
        raise ProbeError(f"FFprobe timeout after {timeout}s: {file_path}")
    except subprocess.CalledProcessError as e:
        raise ProbeError(f"FFprobe failed: {e.stderr}")
    except json.JSONDecodeError as e:
        raise ProbeError(f"Invalid JSON from FFprobe: {e}")
```

### Data Extraction

#### Codec Detection

```python
def _extract_codec(streams: list[dict]) -> CodecType:
    """Extract video codec from stream information."""

    # Find primary video stream
    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    if not video_streams:
        return CodecType.OTHER

    # Use first video stream (primary)
    primary_stream = video_streams[0]
    codec_name = primary_stream.get('codec_name', '').lower()

    # Map codec names to enum values
    codec_mapping = {
        'hevc': CodecType.HEVC,
        'h265': CodecType.H265,
        'av1': CodecType.AV1,
        'h264': CodecType.H264,
        'avc': CodecType.H264,
        'vp9': CodecType.VP9,
        'mpeg4': CodecType.MPEG4,
        'mpeg2video': CodecType.MPEG2,
    }

    return codec_mapping.get(codec_name, CodecType.OTHER)
```

#### Resolution Extraction

```python
def _extract_resolution(streams: list[dict]) -> tuple[int, int] | None:
    """Extract video resolution from streams."""

    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    if not video_streams:
        return None

    stream = video_streams[0]
    width = stream.get('width')
    height = stream.get('height')

    if width and height:
        return (int(width), int(height))

    return None
```

#### Duration and Bitrate

```python
def _extract_duration(format_info: dict, streams: list[dict]) -> float | None:
    """Extract duration from format or stream info."""

    # Try format duration first (more reliable)
    if 'duration' in format_info:
        try:
            return float(format_info['duration'])
        except (ValueError, TypeError):
            pass

    # Fallback to video stream duration
    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    if video_streams and 'duration' in video_streams[0]:
        try:
            return float(video_streams[0]['duration'])
        except (ValueError, TypeError):
            pass

    return None

def _extract_bitrate(format_info: dict, streams: list[dict]) -> int | None:
    """Extract bitrate from format or stream info."""

    # Try format bitrate first
    if 'bit_rate' in format_info:
        try:
            return int(format_info['bit_rate'])
        except (ValueError, TypeError):
            pass

    # Calculate from video stream bitrate
    video_streams = [s for s in streams if s.get('codec_type') == 'video']
    if video_streams and 'bit_rate' in video_streams[0]:
        try:
            return int(video_streams[0]['bit_rate'])
        except (ValueError, TypeError):
            pass

    return None
```

## Error Handling

### Exception Types

```python
class ProbeError(Exception):
    """Base exception for probe operations."""
    pass

class FFprobeNotFoundError(ProbeError):
    """FFprobe executable not found."""
    pass

class VideoAnalysisError(ProbeError):
    """Failed to analyze video file."""
    pass

class UnsupportedFormatError(ProbeError):
    """Video format not supported."""
    pass
```

### Error Handling Examples

```python
from media_audit.probe import probe_video, ProbeError, FFprobeNotFoundError

try:
    video_info = probe_video(video_path)
    print(f"Successfully analyzed: {video_info.codec}")

except FFprobeNotFoundError:
    print("FFprobe not installed or not in PATH")
    print("Install FFmpeg: https://ffmpeg.org/download.html")

except ProbeError as e:
    print(f"Failed to analyze video: {e}")
    # Continue without video info or mark as error

except Exception as e:
    print(f"Unexpected error: {e}")
    # Log error and continue
```

### Graceful Degradation

```python
def safe_probe_video(file_path: Path, cache=None) -> VideoInfo | None:
    """Safely probe video with error handling."""

    try:
        return probe_video(file_path, cache=cache)

    except FFprobeNotFoundError:
        # FFprobe not available - skip video analysis
        return VideoInfo(
            path=file_path,
            size=file_path.stat().st_size if file_path.exists() else 0
        )

    except ProbeError:
        # Probe failed - return basic info
        return VideoInfo(
            path=file_path,
            codec=CodecType.OTHER,
            size=file_path.stat().st_size if file_path.exists() else 0
        )

    except Exception:
        # Unexpected error - return None
        return None
```

## Performance Optimization

### Caching Integration

```python
def probe_video_cached(file_path: Path, cache: MediaCache) -> VideoInfo:
    """Probe video with intelligent caching."""

    # Check cache first
    cached_data = cache.get_probe_data(file_path)
    if cached_data:
        return _deserialize_video_info(cached_data)

    # Probe video
    video_info = _probe_video_direct(file_path)

    # Cache results
    cache_data = _serialize_video_info(video_info)
    cache.set_probe_data(file_path, cache_data)

    return video_info

def _serialize_video_info(video_info: VideoInfo) -> dict:
    """Serialize VideoInfo for caching."""
    return {
        "codec": video_info.codec.value if video_info.codec else None,
        "resolution": video_info.resolution,
        "duration": video_info.duration,
        "bitrate": video_info.bitrate,
        "size": video_info.size,
        "raw_info": video_info.raw_info
    }

def _deserialize_video_info(data: dict) -> VideoInfo:
    """Deserialize cached video info."""
    return VideoInfo(
        path=Path(data["path"]),
        codec=CodecType(data["codec"]) if data["codec"] else None,
        resolution=tuple(data["resolution"]) if data["resolution"] else None,
        duration=data["duration"],
        bitrate=data["bitrate"],
        size=data["size"],
        raw_info=data.get("raw_info", {})
    )
```

### Batch Processing

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator

def probe_videos_batch(
    video_paths: list[Path],
    cache: MediaCache = None,
    max_workers: int = 4
) -> Iterator[tuple[Path, VideoInfo | None]]:
    """Probe multiple videos concurrently."""

    def probe_single(path: Path) -> tuple[Path, VideoInfo | None]:
        try:
            video_info = probe_video(path, cache=cache)
            return (path, video_info)
        except Exception as e:
            print(f"Failed to probe {path}: {e}")
            return (path, None)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_path = {
            executor.submit(probe_single, path): path
            for path in video_paths
        }

        # Yield results as they complete
        for future in as_completed(future_to_path):
            yield future.result()

# Usage
video_files = [
    Path("/movies/Movie1/movie1.mkv"),
    Path("/movies/Movie2/movie2.mkv"),
    Path("/movies/Movie3/movie3.mkv")
]

results = {}
for path, video_info in probe_videos_batch(video_files):
    results[path] = video_info

print(f"Successfully probed {len([r for r in results.values() if r])} videos")
```

## Advanced Usage

### Custom Analysis

```python
class DetailedVideoAnalyzer:
    """Enhanced video analyzer with additional metrics."""

    def __init__(self, cache: MediaCache = None):
        self.cache = cache

    def analyze_video(self, file_path: Path) -> dict:
        """Perform detailed video analysis."""

        # Basic probe
        video_info = probe_video(file_path, cache=self.cache)

        # Enhanced analysis
        analysis = {
            "basic_info": video_info,
            "quality_score": self.calculate_quality_score(video_info),
            "encoding_efficiency": self.calculate_encoding_efficiency(video_info),
            "recommendations": self.generate_recommendations(video_info)
        }

        return analysis

    def calculate_quality_score(self, video_info: VideoInfo) -> float:
        """Calculate quality score (0-100)."""
        score = 50.0  # Base score

        # Resolution scoring
        if video_info.resolution:
            width, height = video_info.resolution
            if height >= 2160:      # 4K
                score += 25
            elif height >= 1080:    # 1080p
                score += 15
            elif height >= 720:     # 720p
                score += 5

        # Codec scoring
        if video_info.codec:
            codec_scores = {
                CodecType.AV1: 25,
                CodecType.HEVC: 20,
                CodecType.H265: 20,
                CodecType.VP9: 15,
                CodecType.H264: 10,
                CodecType.MPEG4: 5
            }
            score += codec_scores.get(video_info.codec, 0)

        # Bitrate scoring (appropriate for resolution)
        if video_info.bitrate and video_info.resolution:
            optimal_bitrate = self.get_optimal_bitrate(video_info.resolution)
            bitrate_ratio = video_info.bitrate / optimal_bitrate

            if 0.8 <= bitrate_ratio <= 1.2:  # Within 20% of optimal
                score += 10
            elif 0.5 <= bitrate_ratio <= 2.0:  # Reasonable range
                score += 5

        return min(100.0, max(0.0, score))

    def calculate_encoding_efficiency(self, video_info: VideoInfo) -> dict:
        """Calculate encoding efficiency metrics."""

        if not all([video_info.size, video_info.duration, video_info.resolution]):
            return {"error": "Insufficient data for efficiency calculation"}

        # Bits per pixel per second
        width, height = video_info.resolution
        pixels = width * height
        bpps = video_info.bitrate / (pixels * 30)  # Assume 30fps average

        # Size efficiency (MB per minute)
        size_mb = video_info.size / (1024 ** 2)
        duration_minutes = video_info.duration / 60
        mb_per_minute = size_mb / duration_minutes if duration_minutes > 0 else 0

        return {
            "bits_per_pixel_per_second": round(bpps, 4),
            "mb_per_minute": round(mb_per_minute, 2),
            "compression_ratio": self.estimate_compression_ratio(video_info)
        }

    def generate_recommendations(self, video_info: VideoInfo) -> list[str]:
        """Generate encoding recommendations."""
        recommendations = []

        # Codec recommendations
        if video_info.codec == CodecType.H264:
            recommendations.append("Consider re-encoding to HEVC or AV1 for better compression")

        # Resolution-based recommendations
        if video_info.resolution:
            width, height = video_info.resolution
            if height < 720:
                recommendations.append("Low resolution content - consider upscaling or replacing")

        # Bitrate recommendations
        if video_info.bitrate and video_info.resolution:
            optimal_bitrate = self.get_optimal_bitrate(video_info.resolution)
            if video_info.bitrate < optimal_bitrate * 0.5:
                recommendations.append("Bitrate may be too low - quality could be poor")
            elif video_info.bitrate > optimal_bitrate * 2:
                recommendations.append("Bitrate may be unnecessarily high - file size could be reduced")

        # Size recommendations
        if video_info.size and video_info.duration:
            size_gb = video_info.size / (1024 ** 3)
            hours = video_info.duration / 3600
            gb_per_hour = size_gb / hours if hours > 0 else 0

            if gb_per_hour > 15:  # High bitrate content
                recommendations.append("Large file size - consider compression if quality allows")

        return recommendations

    def get_optimal_bitrate(self, resolution: tuple[int, int]) -> int:
        """Get optimal bitrate for resolution."""
        width, height = resolution

        if height >= 2160:      # 4K
            return 25_000_000   # 25 Mbps
        elif height >= 1080:    # 1080p
            return 8_000_000    # 8 Mbps
        elif height >= 720:     # 720p
            return 5_000_000    # 5 Mbps
        else:                   # Lower resolutions
            return 2_000_000    # 2 Mbps

# Usage
analyzer = DetailedVideoAnalyzer(cache)
analysis = analyzer.analyze_video(Path("/movies/movie.mkv"))

print(f"Quality Score: {analysis['quality_score']}/100")
print(f"Encoding Efficiency: {analysis['encoding_efficiency']}")
for rec in analysis['recommendations']:
    print(f"• {rec}")
```

### Stream Analysis

```python
def analyze_all_streams(file_path: Path) -> dict:
    """Analyze all streams in video file."""

    ffprobe_data = _execute_ffprobe(file_path)
    streams = ffprobe_data.get('streams', [])

    analysis = {
        "video_streams": [],
        "audio_streams": [],
        "subtitle_streams": [],
        "other_streams": []
    }

    for stream in streams:
        stream_type = stream.get('codec_type', 'unknown')
        stream_info = {
            "index": stream.get('index'),
            "codec": stream.get('codec_name'),
            "codec_long_name": stream.get('codec_long_name')
        }

        if stream_type == 'video':
            stream_info.update({
                "width": stream.get('width'),
                "height": stream.get('height'),
                "fps": stream.get('r_frame_rate'),
                "bitrate": stream.get('bit_rate'),
                "pixel_format": stream.get('pix_fmt')
            })
            analysis["video_streams"].append(stream_info)

        elif stream_type == 'audio':
            stream_info.update({
                "channels": stream.get('channels'),
                "channel_layout": stream.get('channel_layout'),
                "sample_rate": stream.get('sample_rate'),
                "bitrate": stream.get('bit_rate'),
                "language": stream.get('tags', {}).get('language')
            })
            analysis["audio_streams"].append(stream_info)

        elif stream_type == 'subtitle':
            stream_info.update({
                "language": stream.get('tags', {}).get('language'),
                "title": stream.get('tags', {}).get('title')
            })
            analysis["subtitle_streams"].append(stream_info)

        else:
            analysis["other_streams"].append(stream_info)

    return analysis

# Usage
stream_analysis = analyze_all_streams(Path("/movies/movie.mkv"))

print(f"Video streams: {len(stream_analysis['video_streams'])}")
print(f"Audio streams: {len(stream_analysis['audio_streams'])}")
print(f"Subtitle streams: {len(stream_analysis['subtitle_streams'])}")

# Show audio languages
for audio_stream in stream_analysis['audio_streams']:
    lang = audio_stream.get('language', 'Unknown')
    codec = audio_stream.get('codec', 'Unknown')
    print(f"Audio: {lang} ({codec})")
```

## Installation and Setup

### FFmpeg Installation

#### Windows

```bash
# Using Chocolatey
choco install ffmpeg

# Using Winget
winget install Gyan.FFmpeg

# Manual installation
# Download from https://ffmpeg.org/download.html#build-windows
# Add to PATH environment variable
```

#### macOS

```bash
# Using Homebrew
brew install ffmpeg

# Using MacPorts
sudo port install ffmpeg
```

#### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install ffmpeg

# CentOS/RHEL/Fedora
sudo yum install ffmpeg  # or dnf install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg
```

### Verification

```python
def verify_ffprobe_installation() -> bool:
    """Verify FFprobe is available and working."""

    try:
        result = subprocess.run(
            ['ffprobe', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"FFprobe available: {version_line}")
            return True
        else:
            print("FFprobe found but returned error")
            return False

    except FileNotFoundError:
        print("FFprobe not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("FFprobe timeout during version check")
        return False
    except Exception as e:
        print(f"Error checking FFprobe: {e}")
        return False

# Check installation
if verify_ffprobe_installation():
    print("✓ FFprobe is ready for use")
else:
    print("✗ Please install FFmpeg/FFprobe")
```

## Best Practices

### Performance

1. **Use Caching**: Always use caching for repeated analysis
2. **Batch Processing**: Process multiple files concurrently when possible
3. **Timeout Management**: Set appropriate timeouts for large files
4. **Resource Limits**: Limit concurrent FFprobe processes

### Error Handling

1. **Graceful Degradation**: Continue processing even if some files fail
2. **Detailed Logging**: Log probe failures for debugging
3. **Recovery Strategies**: Retry on transient failures
4. **User Feedback**: Provide clear error messages to users

### Data Management

1. **Cache Validation**: Ensure cached data is still valid
2. **Schema Evolution**: Handle changes in probe data structure
3. **Storage Efficiency**: Use appropriate serialization formats
4. **Cleanup**: Regularly clean old cache entries
