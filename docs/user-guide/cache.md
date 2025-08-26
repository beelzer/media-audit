# Cache Management

Media Audit uses intelligent caching to dramatically improve scan performance on subsequent runs. This guide explains how the caching system works and how to manage it effectively.

## Overview

The caching system stores:

- **FFprobe Results**: Video file analysis data (codec, resolution, duration)
- **Directory Scans**: Media item parsing results
- **File Metadata**: Modification times and sizes for cache validation

## Cache Benefits

### Performance Improvements

- **Initial Scan**: Full analysis of all media files
- **Subsequent Scans**: Only re-analyzes changed files
- **Speed Increase**: 80-95% faster scans on unchanged libraries
- **Resource Savings**: Reduced CPU and disk I/O usage

### Typical Performance Gains

```bash
# First scan (no cache)
media-audit scan --roots "D:\Movies" --report audit.html
# Duration: 15 minutes for 1000 movies

# Second scan (with cache)
media-audit scan --roots "D:\Movies" --report audit.html
# Duration: 2-3 minutes for same 1000 movies
```

## Cache Architecture

### Cache Types

#### FFprobe Cache

- **Purpose**: Stores video analysis results
- **Location**: `~/.cache/media-audit/probe/`
- **Format**: Binary pickle files
- **Validation**: File size and modification time

#### Scan Cache

- **Purpose**: Stores parsed media item data
- **Location**: `~/.cache/media-audit/scan/`
- **Format**: JSON files
- **Validation**: Directory modification time

#### Memory Cache

- **Purpose**: In-session caching for repeated operations
- **Location**: RAM during scan execution
- **Lifetime**: Single scan session

### Cache Structure

```text
~/.cache/media-audit/
├── probe/                   # FFprobe results
│   ├── a1b2c3d4.pkl        # Video file analysis
│   ├── e5f6g7h8.pkl        # Another video file
│   └── ...
├── scan/                    # Media item parsing
│   ├── movie_1a2b3c.json   # Movie directory scan
│   ├── series_4d5e6f.json  # TV series scan
│   └── ...
└── schema_version.txt       # Cache schema version
```

## Cache Configuration

### Default Settings

```yaml
# config.yaml
scan:
  cache_enabled: true                    # Enable caching
  cache_dir: ~/.cache/media-audit       # Default location
  concurrent_workers: 4                  # Affects cache performance
```

### Custom Cache Directory

```yaml
scan:
  cache_dir: /custom/cache/path         # Custom location
  cache_enabled: true
```

### Disable Caching

```bash
# Disable cache for single scan
media-audit scan --roots "D:\Media" --no-cache

# Or in configuration
scan:
  cache_enabled: false
```

## Cache Validation

### File-Level Validation

The cache automatically validates entries by checking:

1. **File Existence**: Target file still exists
2. **File Size**: Size hasn't changed
3. **Modification Time**: File hasn't been modified
4. **Schema Version**: Cache format is current

### Directory-Level Validation

For directory-based caches:

1. **Directory Existence**: Directory still exists
2. **Content Changes**: Files added/removed/modified
3. **Structure Changes**: Subdirectory changes

### Example Validation Logic

```python
def is_cache_valid(entry, file_path):
    """Check if cache entry is still valid."""
    if not file_path.exists():
        return False

    try:
        stat = file_path.stat()
        return (stat.st_mtime == entry.file_mtime and
                stat.st_size == entry.file_size)
    except OSError:
        return False
```

## Cache Operations

### Viewing Cache Status

```bash
# Check cache statistics in scan output
media-audit scan --roots "D:\Media" --report audit.html
# Output includes: Cache: 850 hits, 150 misses (85.0% hit rate)
```

### Manual Cache Management

#### Clear All Cache

```bash
# Clear cache before scan
media-audit scan --roots "D:\Media" --no-cache
```

#### Clear Cache Programmatically

```python
# clear-cache.py
from pathlib import Path
import shutil

cache_dir = Path.home() / ".cache" / "media-audit"
if cache_dir.exists():
    shutil.rmtree(cache_dir)
    print("Cache cleared successfully")
```

#### Selective Cache Clearing

```python
# clear-probe-cache.py
from pathlib import Path

# Clear only FFprobe cache
probe_cache = Path.home() / ".cache" / "media-audit" / "probe"
if probe_cache.exists():
    for cache_file in probe_cache.glob("*.pkl"):
        cache_file.unlink()
    print("FFprobe cache cleared")
```

### Cache Statistics

#### Viewing Detailed Statistics

```python
# cache-stats.py
from media_audit.cache import MediaCache
from pathlib import Path

cache = MediaCache(Path.home() / ".cache" / "media-audit")
stats = cache.get_stats()

print(f"Cache Statistics:")
print(f"  Total requests: {stats['total']}")
print(f"  Cache hits: {stats['hits']}")
print(f"  Cache misses: {stats['misses']}")
print(f"  Hit rate: {stats['hit_rate']:.1f}%")
print(f"  Memory entries: {stats['memory_entries']}")
print(f"  Probe cache files: {stats['probe_cache_files']}")
print(f"  Scan cache files: {stats['scan_cache_files']}")
```

## Cache Invalidation

### Automatic Invalidation

The cache automatically invalidates when:

1. **Files Change**: Video files are modified or replaced
2. **Directory Changes**: Files added/removed from media directories
3. **Schema Updates**: Media Audit model structures change
4. **Time-based**: Cache entries older than configured TTL (if set)

### Manual Invalidation

#### Force Fresh Scan

```bash
# Scan without using cache (cache is still updated)
media-audit scan --roots "D:\Media" --no-cache --report fresh-scan.html
```

#### Clear Cache Before Scan

```bash
# Clear cache and perform fresh scan
rm -rf ~/.cache/media-audit/
media-audit scan --roots "D:\Media" --report fresh-scan.html
```

### Selective Invalidation

```python
# invalidate-movie.py
from pathlib import Path
import hashlib

def invalidate_movie_cache(movie_path):
    """Invalidate cache for specific movie."""
    cache_dir = Path.home() / ".cache" / "media-audit"

    # Generate cache key for movie
    key_str = f"media:movie:{Path(movie_path).absolute()}"
    key = hashlib.md5(key_str.encode(), usedforsecurity=False).hexdigest()

    # Remove cache files
    (cache_dir / "scan" / f"{key}.json").unlink(missing_ok=True)

    # Also invalidate video cache if needed
    video_files = list(Path(movie_path).glob("*.mkv"))  # Adjust pattern
    for video in video_files:
        video_key_str = f"probe:{video.absolute()}"
        video_key = hashlib.md5(video_key_str.encode(), usedforsecurity=False).hexdigest()
        (cache_dir / "probe" / f"{video_key}.pkl").unlink(missing_ok=True)

# Usage
invalidate_movie_cache("/path/to/Movie (2023)")
```

## Schema Management

### Schema Versioning

Media Audit uses automatic schema versioning to ensure cache compatibility:

```python
# Generated from model definitions
CACHE_SCHEMA_VERSION = "2.0.0"

def generate_schema_hash():
    """Generate hash of current model schemas."""
    from media_audit.models import MovieItem, SeriesItem, VideoInfo
    # ... generates hash from model field definitions
    return schema_hash
```

### Schema Migration

When models change, cache is automatically cleared:

```bash
# On schema change, you'll see:
Cache schema changed, clearing old cache data...
```

### Version History

- **v1.0.0**: Initial cache implementation
- **v1.1.0**: Added directory-level caching
- **v2.0.0**: Enhanced video info structure
- **Current**: Auto-generated from models

## Performance Optimization

### Cache Performance Tips

#### 1. Use Appropriate Worker Count

```yaml
scan:
  concurrent_workers: 8  # Adjust based on CPU cores
```

#### 2. Optimize Cache Location

```yaml
scan:
  cache_dir: /fast/ssd/cache  # Use fast storage
```

#### 3. Regular Cache Maintenance

```bash
# Periodic cache cleanup (remove old entries)
find ~/.cache/media-audit -name "*.pkl" -mtime +30 -delete
find ~/.cache/media-audit -name "*.json" -mtime +30 -delete
```

#### 4. Monitor Cache Hit Rates

```bash
# Good hit rate: >80% for established libraries
# Low hit rate: <50% indicates frequent file changes
```

### Large Library Optimization

For libraries with >10,000 items:

```yaml
scan:
  concurrent_workers: 12     # Higher worker count
  cache_enabled: true        # Essential for performance
  cache_dir: /nvme/cache     # Use fastest storage
```

### Network Storage Considerations

```yaml
# For network-attached storage
scan:
  concurrent_workers: 4      # Lower to reduce network load
  cache_dir: /local/cache    # Keep cache local
```

## Troubleshooting

### Common Issues

#### Cache Not Working

```bash
# Check cache directory permissions
ls -la ~/.cache/media-audit/

# Verify cache is enabled
grep cache_enabled config.yaml
```

#### Low Hit Rate

```bash
# Possible causes:
# 1. Frequently changing files
# 2. Cache directory on slow storage
# 3. Insufficient disk space
# 4. Permission issues

# Check disk space
df -h ~/.cache/media-audit/
```

#### Cache Corruption

```bash
# Symptoms: Errors during scan, unexpected results
# Solution: Clear cache and rescan
rm -rf ~/.cache/media-audit/
media-audit scan --roots "D:\Media"
```

### Debugging Cache Issues

#### Enable Debug Logging

```python
# debug-cache.py
import logging
from media_audit.cache import MediaCache

logging.basicConfig(level=logging.DEBUG)
cache = MediaCache(enabled=True)

# Test cache operations
test_file = Path("/path/to/test.mkv")
result = cache.get_probe_data(test_file)
print(f"Cache result: {result}")
```

#### Monitor Cache Operations

```bash
# Watch cache directory during scan
watch -n 1 'ls -la ~/.cache/media-audit/probe/ | wc -l'

# Monitor cache file creation
inotifywait -mr ~/.cache/media-audit/ -e create -e modify
```

### Cache Recovery

#### Backup Cache

```bash
# Before major changes, backup cache
tar -czf media-audit-cache-backup.tar.gz ~/.cache/media-audit/
```

#### Restore Cache

```bash
# Restore from backup
rm -rf ~/.cache/media-audit/
tar -xzf media-audit-cache-backup.tar.gz -C ~/
```

#### Partial Recovery

```python
# recover-cache.py
from pathlib import Path
import pickle
import json

def recover_valid_cache_entries(cache_dir):
    """Recover valid cache entries after corruption."""
    probe_dir = cache_dir / "probe"
    scan_dir = cache_dir / "scan"

    valid_count = 0
    invalid_count = 0

    # Check probe cache files
    for cache_file in probe_dir.glob("*.pkl"):
        try:
            with open(cache_file, 'rb') as f:
                pickle.load(f)  # Test if file is readable
            valid_count += 1
        except Exception:
            cache_file.unlink()  # Remove corrupted file
            invalid_count += 1

    # Check scan cache files
    for cache_file in scan_dir.glob("*.json"):
        try:
            with open(cache_file) as f:
                json.load(f)  # Test if file is readable
            valid_count += 1
        except Exception:
            cache_file.unlink()  # Remove corrupted file
            invalid_count += 1

    print(f"Recovery complete: {valid_count} valid, {invalid_count} corrupted files removed")

# Usage
cache_dir = Path.home() / ".cache" / "media-audit"
recover_valid_cache_entries(cache_dir)
```

## Best Practices

### Cache Management

1. **Enable by Default**: Keep caching enabled for regular use
2. **Monitor Hit Rates**: Aim for >80% hit rate on established libraries
3. **Regular Maintenance**: Clean old cache entries periodically
4. **Backup Important Cache**: For large libraries, consider backing up cache

### Development and Testing

1. **Disable for Testing**: Use `--no-cache` when testing changes
2. **Clear After Updates**: Clear cache after Media Audit upgrades
3. **Separate Test Cache**: Use different cache directories for testing

### Production Deployment

1. **Fast Storage**: Place cache on fastest available storage
2. **Monitoring**: Include cache hit rates in monitoring
3. **Disk Space**: Monitor cache directory disk usage
4. **Permissions**: Ensure proper cache directory permissions

### Troubleshooting Workflow

1. **Check Hit Rate**: Low rate indicates issues
2. **Verify Permissions**: Ensure cache directory is writable
3. **Clear and Retry**: When in doubt, clear cache and retry
4. **Monitor Growth**: Watch cache size over time

## Advanced Usage

### Custom Cache Implementation

```python
# custom-cache.py
from media_audit.cache import MediaCache
from pathlib import Path
import redis  # Example: Redis-backed cache

class RedisMediaCache(MediaCache):
    """Redis-backed cache implementation."""

    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        super().__init__(enabled=True)

    def get_probe_data(self, file_path):
        """Get probe data from Redis."""
        key = self._get_file_key(file_path, "probe")
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return None

    def set_probe_data(self, file_path, data):
        """Store probe data in Redis."""
        key = self._get_file_key(file_path, "probe")
        self.redis.setex(key, 86400, json.dumps(data))  # 24h TTL
```

### Cache Analytics

```python
# cache-analytics.py
from pathlib import Path
import json
import pickle
from collections import defaultdict
import time

def analyze_cache_usage(cache_dir):
    """Analyze cache usage patterns."""
    probe_dir = cache_dir / "probe"
    scan_dir = cache_dir / "scan"

    stats = {
        'total_size': 0,
        'file_count': 0,
        'age_distribution': defaultdict(int),
        'size_distribution': defaultdict(int)
    }

    current_time = time.time()

    # Analyze probe cache
    for cache_file in probe_dir.glob("*.pkl"):
        size = cache_file.stat().st_size
        age_days = (current_time - cache_file.stat().st_mtime) / 86400

        stats['total_size'] += size
        stats['file_count'] += 1
        stats['age_distribution'][int(age_days)] += 1
        stats['size_distribution'][size // 1024] += 1  # KB buckets

    print(f"Cache Analysis:")
    print(f"  Total files: {stats['file_count']}")
    print(f"  Total size: {stats['total_size'] / 1024 / 1024:.1f} MB")
    print(f"  Average file size: {stats['total_size'] / stats['file_count'] / 1024:.1f} KB")

    # Age distribution
    print(f"  Age distribution (days):")
    for age in sorted(stats['age_distribution'].keys()):
        count = stats['age_distribution'][age]
        print(f"    {age}: {count} files")

# Usage
cache_dir = Path.home() / ".cache" / "media-audit"
analyze_cache_usage(cache_dir)
```
