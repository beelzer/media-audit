# Advanced Usage

This guide covers advanced Media Audit usage scenarios, integration patterns, automation strategies, and power-user techniques.

## Advanced Configuration

### Complex Multi-Environment Setup

```yaml
# production-config.yaml
scan:
  root_paths:
    - /mnt/movies-4k
    - /mnt/movies-hd  
    - /mnt/tv-shows
    - /mnt/anime
  profiles: ['plex', 'jellyfin']
  allowed_codecs: ['hevc', 'av1']
  concurrent_workers: 16
  cache_enabled: true
  cache_dir: /nvme/media-audit-cache
  include_patterns:
    - "*.mkv"
    - "*.mp4" 
    - "*.m4v"
  exclude_patterns:
    - "*.sample.*"
    - "*trailer*"
    - "*/extras/*"
    - "*/deleted/*"

report:
  output_path: /reports/daily-audit.html
  json_path: /reports/daily-audit.json
  auto_open: false
  problems_only: true
  show_thumbnails: false  # Faster generation for automated reports
```

### Environment-Specific Configurations

```bash
# Different configs for different environments
media-audit scan --config config-dev.yaml     # Development
media-audit scan --config config-staging.yaml # Staging  
media-audit scan --config config-prod.yaml    # Production
```

## Automation and Integration

### CI/CD Pipeline Integration

#### GitHub Actions
```yaml
# .github/workflows/media-validation.yml
name: Media Library Validation

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  push:
    paths:
      - 'media/**'
  workflow_dispatch:

jobs:
  validate-media:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v4
      
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.13'
        
    - name: Install Media Audit
      run: |
        pip install media-audit
        
    - name: Mount Media Storage
      run: |
        # Mount network storage or configure access
        sudo mkdir -p /mnt/media
        sudo mount -t nfs ${{ secrets.NFS_SERVER }}:/media /mnt/media
        
    - name: Run Media Validation
      run: |
        media-audit scan \
          --roots /mnt/media/Movies /mnt/media/TV \
          --json validation-results.json \
          --report validation-report.html \
          --problems-only
          
    - name: Parse Results
      id: results
      run: |
        ISSUES=$(jq '.scan_info.total_issues' validation-results.json)
        echo "issues=$ISSUES" >> $GITHUB_OUTPUT
        
    - name: Create Issue on Failures
      if: steps.results.outputs.issues > 0
      uses: actions/github-script@v7
      with:
        script: |
          const fs = require('fs');
          const results = JSON.parse(fs.readFileSync('validation-results.json'));
          
          const issues = results.movies
            .filter(m => m.issues.length > 0)
            .slice(0, 10)  // First 10 issues
            .map(m => `- **${m.name}**: ${m.issues.map(i => i.message).join(', ')}`)
            .join('\n');
            
          github.rest.issues.create({
            owner: context.repo.owner,
            repo: context.repo.repo,
            title: `Media Validation Failed: ${results.scan_info.total_issues} issues found`,
            body: `## Media Library Issues\n\n${issues}\n\n[View full report](${process.env.GITHUB_SERVER_URL}/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId})`
          });
          
    - name: Upload Reports
      uses: actions/upload-artifact@v4
      if: always()
      with:
        name: media-validation-reports
        path: |
          validation-results.json
          validation-report.html
        retention-days: 30
```

#### Jenkins Pipeline
```groovy
// Jenkinsfile
pipeline {
    agent any
    
    parameters {
        choice(
            name: 'SCAN_TYPE',
            choices: ['quick', 'full', 'problems-only'],
            description: 'Type of scan to perform'
        )
        string(
            name: 'MEDIA_PATHS', 
            defaultValue: '/mnt/movies,/mnt/tv',
            description: 'Comma-separated media paths'
        )
    }
    
    triggers {
        cron('H 2 * * *')  // Daily at random minute past 2 AM
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install media-audit'
            }
        }
        
        stage('Media Validation') {
            steps {
                script {
                    def scanArgs = ""
                    def paths = params.MEDIA_PATHS.split(',')
                    
                    paths.each { path ->
                        scanArgs += "--roots '${path}' "
                    }
                    
                    if (params.SCAN_TYPE == 'problems-only') {
                        scanArgs += "--problems-only "
                    }
                    
                    sh """
                        media-audit scan ${scanArgs} \
                            --json results.json \
                            --report report.html \
                            --workers 8
                    """
                }
            }
        }
        
        stage('Process Results') {
            steps {
                script {
                    def results = readJSON file: 'results.json'
                    def totalIssues = results.scan_info.total_issues
                    
                    echo "Found ${totalIssues} total issues"
                    
                    if (totalIssues > 0) {
                        currentBuild.result = 'UNSTABLE'
                        
                        // Send notifications
                        emailext (
                            subject: "Media Validation: ${totalIssues} issues found",
                            body: "Media library validation found ${totalIssues} issues. See attached report.",
                            attachmentsPattern: 'report.html',
                            to: "${env.CHANGE_AUTHOR_EMAIL ?: 'admin@example.com'}"
                        )
                    }
                }
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'results.json,report.html', allowEmptyArchive: true
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'report.html',
                reportName: 'Media Audit Report'
            ])
        }
    }
}
```

### Docker Integration

#### Dockerfile
```dockerfile
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install media-audit
RUN pip install media-audit

# Create non-root user
RUN useradd -m -u 1000 mediaaudit
USER mediaaudit

# Set working directory
WORKDIR /app

# Default command
CMD ["media-audit", "--help"]
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  media-audit:
    build: .
    volumes:
      - /path/to/media:/media:ro
      - /path/to/reports:/reports
      - /path/to/cache:/cache
    environment:
      - MEDIA_AUDIT_CACHE_DIR=/cache
    command: >
      media-audit scan 
      --roots /media/Movies /media/TV
      --report /reports/audit.html
      --json /reports/audit.json
      --cache-dir /cache
      --workers 4

  # Scheduled audit
  media-audit-cron:
    build: .
    volumes:
      - /path/to/media:/media:ro
      - /path/to/reports:/reports
      - /path/to/cache:/cache
    environment:
      - CRON_SCHEDULE=0 2 * * *
    command: >
      sh -c "
      echo '$CRON_SCHEDULE media-audit scan --roots /media/Movies /media/TV --report /reports/daily-audit.html --json /reports/daily-audit.json --problems-only' | crontab - &&
      crond -f
      "
```

#### Kubernetes Deployment
```yaml
# kubernetes/media-audit-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: media-audit
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: media-audit
            image: media-audit:latest
            command:
            - media-audit
            - scan
            - --roots
            - /media/movies
            - /media/tv
            - --json
            - /reports/audit.json
            - --report
            - /reports/audit.html
            - --problems-only
            volumeMounts:
            - name: media-storage
              mountPath: /media
              readOnly: true
            - name: reports-storage
              mountPath: /reports
            - name: cache-storage
              mountPath: /cache
            resources:
              requests:
                memory: "1Gi"
                cpu: "500m"
              limits:
                memory: "2Gi"
                cpu: "2000m"
          volumes:
          - name: media-storage
            persistentVolumeClaim:
              claimName: media-pvc
          - name: reports-storage
            persistentVolumeClaim:
              claimName: reports-pvc
          - name: cache-storage
            persistentVolumeClaim:
              claimName: cache-pvc
          restartPolicy: OnFailure
```

## Media Server Integration

### Plex Integration

```python
# plex-integration.py
import json
import requests
from pathlib import Path

class PlexIntegration:
    def __init__(self, plex_url, plex_token):
        self.plex_url = plex_url.rstrip('/')
        self.plex_token = plex_token
        self.headers = {'X-Plex-Token': plex_token}
    
    def get_library_sections(self):
        """Get all library sections from Plex."""
        response = requests.get(
            f"{self.plex_url}/library/sections",
            headers=self.headers
        )
        return response.json()
    
    def refresh_metadata(self, library_key, item_key):
        """Refresh metadata for specific item."""
        requests.put(
            f"{self.plex_url}/library/sections/{library_key}/refresh",
            params={'force': 1, 'X-Plex-Token': self.plex_token}
        )
    
    def sync_audit_results(self, audit_json_path):
        """Process audit results and sync with Plex."""
        with open(audit_json_path) as f:
            audit_data = json.load(f)
        
        # Find items with missing assets
        missing_posters = []
        for movie in audit_data['movies']:
            if not movie['assets']['posters']:
                missing_posters.append({
                    'name': movie['name'],
                    'path': movie['path']
                })
        
        print(f"Found {len(missing_posters)} movies missing posters")
        
        # Trigger metadata refresh for these items
        for movie in missing_posters:
            # Find matching Plex library item
            plex_item = self.find_plex_item(movie['name'])
            if plex_item:
                print(f"Refreshing metadata for: {movie['name']}")
                self.refresh_metadata(plex_item['librarySectionID'], plex_item['key'])

    def find_plex_item(self, title):
        """Find Plex item by title."""
        # Implementation depends on Plex API search
        pass

# Usage
plex = PlexIntegration("http://plex.local:32400", "your-plex-token")
plex.sync_audit_results("audit.json")
```

### Jellyfin Integration

```python
# jellyfin-integration.py
import json
import requests

class JellyfinIntegration:
    def __init__(self, jellyfin_url, api_key):
        self.jellyfin_url = jellyfin_url.rstrip('/')
        self.api_key = api_key
        self.headers = {'X-Emby-Token': api_key}
    
    def get_libraries(self):
        """Get all libraries from Jellyfin."""
        response = requests.get(
            f"{self.jellyfin_url}/Items",
            headers=self.headers,
            params={'ParentId': ''}
        )
        return response.json()
    
    def scan_library(self, library_id):
        """Trigger library scan."""
        requests.post(
            f"{self.jellyfin_url}/Items/{library_id}/Refresh",
            headers=self.headers,
            params={'Recursive': True, 'ImageRefreshMode': 'Default'}
        )
    
    def update_missing_images(self, audit_json_path):
        """Update items with missing images."""
        with open(audit_json_path) as f:
            audit_data = json.load(f)
        
        # Process missing images
        for movie in audit_data['movies']:
            if not movie['assets']['posters'] or not movie['assets']['backgrounds']:
                print(f"Missing images for: {movie['name']}")
                # Trigger image refresh or download
                self.refresh_images_for_item(movie['name'])

    def refresh_images_for_item(self, title):
        """Refresh images for specific item."""
        # Implementation specific to Jellyfin API
        pass
```

## Custom Validation Rules

### Custom Validator Implementation

```python
# custom-validator.py
from media_audit.validator import MediaValidator
from media_audit.models import ValidationIssue, ValidationStatus

class CustomMediaValidator(MediaValidator):
    """Extended validator with custom rules."""
    
    def validate_movie(self, movie):
        """Enhanced movie validation."""
        # Run standard validation
        super().validate_movie(movie)
        
        # Custom validations
        self._validate_movie_quality(movie)
        self._validate_movie_naming(movie) 
        self._validate_movie_size(movie)
        self._validate_movie_bitrate(movie)
    
    def _validate_movie_quality(self, movie):
        """Validate movie quality indicators."""
        quality_indicators = ['4K', 'UHD', '2160p', '1080p', '720p']
        
        # Check if quality is indicated in filename
        video_name = movie.video_info.path.stem if movie.video_info else ""
        has_quality = any(q in video_name.upper() for q in quality_indicators)
        
        if not has_quality:
            movie.issues.append(
                ValidationIssue(
                    category="naming",
                    message="Movie filename should include quality indicator",
                    severity=ValidationStatus.WARNING,
                    details={"expected": quality_indicators}
                )
            )
    
    def _validate_movie_naming(self, movie):
        """Validate movie naming conventions."""
        expected_pattern = r"^.+ \(\d{4}\)$"  # Title (Year)
        
        if not re.match(expected_pattern, movie.name):
            movie.issues.append(
                ValidationIssue(
                    category="naming", 
                    message="Movie folder should follow 'Title (Year)' format",
                    severity=ValidationStatus.ERROR,
                    details={"current": movie.name, "expected": "Title (Year)"}
                )
            )
    
    def _validate_movie_size(self, movie):
        """Validate movie file size."""
        if not movie.video_info or not movie.video_info.size:
            return
            
        size_gb = movie.video_info.size / (1024 ** 3)
        
        # Size recommendations based on resolution
        if movie.video_info.resolution:
            width, height = movie.video_info.resolution
            
            if height >= 2160:  # 4K
                if size_gb < 15:
                    severity = ValidationStatus.WARNING
                    message = "4K movie file seems small (< 15GB), may be low quality"
                elif size_gb > 100:
                    severity = ValidationStatus.WARNING
                    message = "4K movie file is very large (> 100GB), consider compression"
                else:
                    return
            elif height >= 1080:  # 1080p
                if size_gb < 3:
                    severity = ValidationStatus.WARNING
                    message = "1080p movie file seems small (< 3GB), may be low quality"
                elif size_gb > 20:
                    severity = ValidationStatus.WARNING
                    message = "1080p movie file is large (> 20GB), consider HEVC encoding"
                else:
                    return
            else:
                return
                
            movie.issues.append(
                ValidationIssue(
                    category="quality",
                    message=message,
                    severity=severity,
                    details={"size_gb": round(size_gb, 2), "resolution": f"{width}x{height}"}
                )
            )
    
    def _validate_movie_bitrate(self, movie):
        """Validate movie bitrate."""
        if not movie.video_info or not movie.video_info.bitrate:
            return
            
        bitrate_mbps = movie.video_info.bitrate / 1_000_000
        
        if movie.video_info.resolution:
            width, height = movie.video_info.resolution
            
            # Bitrate recommendations
            if height >= 2160:  # 4K
                if bitrate_mbps < 15:
                    message = "4K movie has low bitrate (< 15 Mbps), quality may be poor"
                    severity = ValidationStatus.WARNING
                elif bitrate_mbps > 80:
                    message = "4K movie has very high bitrate (> 80 Mbps), consider re-encoding"
                    severity = ValidationStatus.WARNING
                else:
                    return
            elif height >= 1080:  # 1080p
                if bitrate_mbps < 5:
                    message = "1080p movie has low bitrate (< 5 Mbps), quality may be poor"
                    severity = ValidationStatus.WARNING
                elif bitrate_mbps > 25:
                    message = "1080p movie has high bitrate (> 25 Mbps), consider HEVC"
                    severity = ValidationStatus.WARNING
                else:
                    return
            else:
                return
                
            movie.issues.append(
                ValidationIssue(
                    category="encoding",
                    message=message,
                    severity=severity,
                    details={"bitrate_mbps": round(bitrate_mbps, 2)}
                )
            )

# Usage with custom validator
from media_audit.config import ScanConfig
from media_audit.scanner import MediaScanner

config = ScanConfig(root_paths=[Path("/media")])
scanner = MediaScanner(config)

# Replace default validator
scanner.validator = CustomMediaValidator(config)

result = scanner.scan()
```

### Rule-Based Configuration

```yaml
# custom-rules.yaml
validation_rules:
  movies:
    naming:
      enforce_year: true
      require_quality_tag: true
      allowed_formats: ["Title (Year)", "Title.Year"]
    
    quality:
      min_size_1080p_gb: 3
      max_size_1080p_gb: 20
      min_size_4k_gb: 15
      max_size_4k_gb: 100
      
    encoding:
      min_bitrate_1080p_mbps: 5
      max_bitrate_1080p_mbps: 25
      min_bitrate_4k_mbps: 15
      max_bitrate_4k_mbps: 80
      
  tv_shows:
    episodes:
      require_title_cards: false  # Make optional
      max_episode_size_gb: 5
      
  assets:
    require_multiple_posters: false
    require_trailers: false
    image_min_resolution: [300, 400]  # Width x Height
```

## Performance Optimization

### Large Library Optimization

```python
# large-library-optimizer.py
import asyncio
import aiofiles
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

class OptimizedScanner:
    """High-performance scanner for large libraries."""
    
    def __init__(self, config):
        self.config = config
        self.thread_pool = ThreadPoolExecutor(max_workers=config.concurrent_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=config.concurrent_workers // 2)
    
    async def scan_library_async(self, root_paths):
        """Asynchronous library scanning."""
        tasks = []
        
        for root_path in root_paths:
            # Discover directories asynchronously
            movie_dirs = await self.discover_movies(root_path / "Movies")
            tv_dirs = await self.discover_tv_shows(root_path / "TV Shows")
            
            # Create tasks for parallel processing
            for movie_dir in movie_dirs:
                task = asyncio.create_task(self.process_movie_async(movie_dir))
                tasks.append(task)
                
            for tv_dir in tv_dirs:
                task = asyncio.create_task(self.process_tv_show_async(tv_dir))
                tasks.append(task)
        
        # Process all items concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def discover_movies(self, movies_path):
        """Asynchronously discover movie directories."""
        if not movies_path.exists():
            return []
            
        # Use async file operations
        dirs = []
        for item in movies_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                dirs.append(item)
        return dirs
    
    async def process_movie_async(self, movie_dir):
        """Process single movie asynchronously."""
        loop = asyncio.get_event_loop()
        
        # CPU-intensive tasks in process pool
        movie_data = await loop.run_in_executor(
            self.process_pool, 
            self.parse_movie, 
            movie_dir
        )
        
        # I/O tasks in thread pool  
        video_info = await loop.run_in_executor(
            self.thread_pool,
            self.probe_video,
            movie_data['video_path']
        )
        
        movie_data['video_info'] = video_info
        return movie_data
```

### Memory-Efficient Processing

```python
# memory-efficient.py
import gc
from pathlib import Path
from typing import Iterator

class MemoryEfficientScanner:
    """Memory-efficient scanner using generators."""
    
    def scan_in_batches(self, root_paths, batch_size=100):
        """Process items in batches to manage memory usage."""
        for root_path in root_paths:
            for batch in self.get_movie_batches(root_path / "Movies", batch_size):
                # Process batch
                results = self.process_movie_batch(batch)
                
                # Yield results and clean up
                yield from results
                
                # Force garbage collection
                gc.collect()
    
    def get_movie_batches(self, movies_path, batch_size) -> Iterator[list]:
        """Generate batches of movie directories."""
        if not movies_path.exists():
            return
            
        batch = []
        for movie_dir in movies_path.iterdir():
            if movie_dir.is_dir() and not movie_dir.name.startswith('.'):
                batch.append(movie_dir)
                
                if len(batch) >= batch_size:
                    yield batch
                    batch = []
        
        # Yield remaining items
        if batch:
            yield batch
    
    def process_movie_batch(self, movie_dirs):
        """Process a batch of movies efficiently."""
        results = []
        
        for movie_dir in movie_dirs:
            try:
                movie = self.process_movie_lightweight(movie_dir)
                results.append(movie)
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing {movie_dir}: {e}")
                
        return results
        
    def process_movie_lightweight(self, movie_dir):
        """Lightweight movie processing with minimal memory footprint."""
        # Only load essential data
        movie_data = {
            'name': movie_dir.name,
            'path': str(movie_dir),
            'assets': self.find_assets_minimal(movie_dir),
            'video_info': None  # Load on demand
        }
        
        return movie_data
        
    def find_assets_minimal(self, movie_dir):
        """Minimal asset discovery."""
        assets = {'posters': [], 'backgrounds': [], 'trailers': []}
        
        # Quick check for common files
        for file in movie_dir.iterdir():
            name_lower = file.name.lower()
            if name_lower.startswith('poster') and file.suffix in ['.jpg', '.png']:
                assets['posters'].append(str(file))
            elif name_lower.startswith('fanart') and file.suffix in ['.jpg', '.png']:
                assets['backgrounds'].append(str(file))
                
        return assets
```

### Distributed Processing

```python
# distributed-scanner.py
import ray
from pathlib import Path

@ray.remote
class DistributedMovieProcessor:
    """Ray-based distributed movie processor."""
    
    def __init__(self, config):
        self.config = config
        # Initialize processor state
    
    def process_movies(self, movie_paths):
        """Process list of movie paths."""
        results = []
        for movie_path in movie_paths:
            try:
                result = self.process_single_movie(movie_path)
                results.append(result)
            except Exception as e:
                results.append({'error': str(e), 'path': str(movie_path)})
        return results
    
    def process_single_movie(self, movie_path):
        """Process single movie with full validation."""
        # Implementation details...
        pass

class DistributedScanner:
    """Distributed scanner using Ray."""
    
    def __init__(self, config, num_workers=4):
        self.config = config
        self.num_workers = num_workers
        
        # Initialize Ray
        ray.init()
        
        # Create worker pool
        self.workers = [
            DistributedMovieProcessor.remote(config)
            for _ in range(num_workers)
        ]
    
    def scan_distributed(self, root_paths):
        """Scan libraries using distributed workers."""
        # Collect all movie directories
        all_movies = []
        for root_path in root_paths:
            movies_path = root_path / "Movies"
            if movies_path.exists():
                all_movies.extend(movies_path.iterdir())
        
        # Distribute work among workers
        chunk_size = len(all_movies) // self.num_workers
        chunks = [
            all_movies[i:i + chunk_size]
            for i in range(0, len(all_movies), chunk_size)
        ]
        
        # Process chunks in parallel
        futures = []
        for worker, chunk in zip(self.workers, chunks):
            future = worker.process_movies.remote(chunk)
            futures.append(future)
        
        # Collect results
        results = ray.get(futures)
        
        # Flatten results
        all_results = []
        for result_chunk in results:
            all_results.extend(result_chunk)
            
        return all_results

# Usage
config = ScanConfig(root_paths=[Path("/media")])
scanner = DistributedScanner(config, num_workers=8)
results = scanner.scan_distributed(config.root_paths)
```

## Monitoring and Alerting

### Prometheus Metrics

```python
# prometheus-metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import time

class MetricsCollector:
    """Collect metrics for monitoring."""
    
    def __init__(self):
        # Define metrics
        self.scan_duration = Histogram('media_audit_scan_duration_seconds', 'Scan duration')
        self.total_items = Gauge('media_audit_total_items', 'Total media items')
        self.total_issues = Gauge('media_audit_total_issues', 'Total validation issues')
        self.cache_hits = Counter('media_audit_cache_hits_total', 'Cache hits')
        self.cache_misses = Counter('media_audit_cache_misses_total', 'Cache misses')
        
        # Issue counters by category
        self.issues_by_category = Counter('media_audit_issues_total', 'Issues by category', ['category'])
        self.items_by_status = Gauge('media_audit_items_by_status', 'Items by status', ['status'])
    
    def update_scan_metrics(self, scan_result):
        """Update metrics from scan result."""
        self.total_items.set(scan_result.total_items)
        self.total_issues.set(scan_result.total_issues)
        
        # Count items by status
        status_counts = {'valid': 0, 'warning': 0, 'error': 0}
        
        for movie in scan_result.movies:
            status_counts[movie.status.value] += 1
            
            # Count issues by category
            for issue in movie.issues:
                self.issues_by_category.labels(category=issue.category).inc()
        
        # Update gauges
        for status, count in status_counts.items():
            self.items_by_status.labels(status=status).set(count)
    
    def time_scan(self, scan_func, *args, **kwargs):
        """Time scan execution."""
        with self.scan_duration.time():
            return scan_func(*args, **kwargs)

# Usage
metrics = MetricsCollector()
start_http_server(8000)  # Expose metrics on port 8000

# In scanner
result = metrics.time_scan(scanner.scan)
metrics.update_scan_metrics(result)
```

### Alerting Rules

```yaml
# alertmanager.yml
groups:
- name: media-audit
  rules:
  - alert: HighErrorRate
    expr: media_audit_total_issues > 100
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High number of media validation issues"
      description: "Found {{ $value }} validation issues in media library"
      
  - alert: ScanDurationHigh
    expr: media_audit_scan_duration_seconds > 3600
    for: 0m
    labels:
      severity: warning
    annotations:
      summary: "Media scan taking too long"
      description: "Media scan duration is {{ $value }} seconds"
      
  - alert: CacheHitRateLow
    expr: |
      (
        rate(media_audit_cache_hits_total[5m]) / 
        (rate(media_audit_cache_hits_total[5m]) + rate(media_audit_cache_misses_total[5m]))
      ) < 0.5
    for: 10m
    labels:
      severity: info
    annotations:
      summary: "Low cache hit rate"
      description: "Cache hit rate is below 50%"
```

### Health Checks

```python
# health-check.py
import requests
import json
from datetime import datetime, timedelta

class HealthChecker:
    """Health check system for media audit."""
    
    def __init__(self, config):
        self.config = config
        self.last_scan_file = Path(".last_scan")
    
    def check_health(self):
        """Perform health checks."""
        checks = {
            'last_scan_age': self.check_last_scan_age(),
            'cache_directory': self.check_cache_directory(),
            'ffprobe_available': self.check_ffprobe(),
            'media_paths': self.check_media_paths(),
            'disk_space': self.check_disk_space()
        }
        
        overall_health = all(check['status'] == 'ok' for check in checks.values())
        
        return {
            'overall': 'healthy' if overall_health else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'checks': checks
        }
    
    def check_last_scan_age(self):
        """Check when last scan was performed."""
        if not self.last_scan_file.exists():
            return {'status': 'warning', 'message': 'No previous scan found'}
            
        try:
            last_scan = datetime.fromisoformat(self.last_scan_file.read_text().strip())
            age = datetime.now() - last_scan
            
            if age > timedelta(days=1):
                return {'status': 'warning', 'message': f'Last scan was {age} ago'}
            else:
                return {'status': 'ok', 'message': f'Last scan was {age} ago'}
        except Exception as e:
            return {'status': 'error', 'message': f'Error reading last scan: {e}'}
    
    def check_cache_directory(self):
        """Check cache directory health."""
        cache_dir = self.config.scan.cache_dir
        
        if not cache_dir or not cache_dir.exists():
            return {'status': 'error', 'message': 'Cache directory does not exist'}
            
        try:
            # Check write permissions
            test_file = cache_dir / '.health_check'
            test_file.write_text('test')
            test_file.unlink()
            
            return {'status': 'ok', 'message': 'Cache directory is writable'}
        except Exception as e:
            return {'status': 'error', 'message': f'Cache directory not writable: {e}'}
    
    def check_ffprobe(self):
        """Check if ffprobe is available."""
        import subprocess
        
        try:
            result = subprocess.run(['ffprobe', '-version'], capture_output=True)
            if result.returncode == 0:
                return {'status': 'ok', 'message': 'FFprobe is available'}
            else:
                return {'status': 'error', 'message': 'FFprobe returned non-zero exit code'}
        except FileNotFoundError:
            return {'status': 'error', 'message': 'FFprobe not found in PATH'}
    
    def check_media_paths(self):
        """Check if media paths are accessible."""
        issues = []
        
        for path in self.config.scan.root_paths:
            if not path.exists():
                issues.append(f'{path} does not exist')
            elif not path.is_dir():
                issues.append(f'{path} is not a directory')
            elif not path.stat().st_mode & 0o444:  # Check read permission
                issues.append(f'{path} is not readable')
        
        if issues:
            return {'status': 'error', 'message': '; '.join(issues)}
        else:
            return {'status': 'ok', 'message': 'All media paths accessible'}
    
    def check_disk_space(self):
        """Check available disk space."""
        import shutil
        
        min_free_gb = 10  # Minimum 10GB free space
        
        try:
            free_space = shutil.disk_usage(self.config.scan.cache_dir).free
            free_gb = free_space / (1024 ** 3)
            
            if free_gb < min_free_gb:
                return {'status': 'warning', 'message': f'Low disk space: {free_gb:.1f}GB free'}
            else:
                return {'status': 'ok', 'message': f'Disk space OK: {free_gb:.1f}GB free'}
        except Exception as e:
            return {'status': 'error', 'message': f'Error checking disk space: {e}'}

# Health check endpoint for monitoring
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    checker = HealthChecker(config)
    return jsonify(checker.check_health())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

## Best Practices Summary

### Development
1. **Use Version Control**: Track configuration and custom code
2. **Test Locally**: Validate changes on small test libraries first
3. **Monitor Performance**: Track scan times and cache hit rates
4. **Document Custom Rules**: Maintain clear documentation for custom validation

### Production
1. **Scheduled Scanning**: Regular automated scans to catch issues early
2. **Alerting**: Set up alerts for high error counts or scan failures
3. **Backup Configuration**: Keep configuration files in version control
4. **Resource Monitoring**: Monitor CPU, memory, and disk usage during scans

### Maintenance
1. **Cache Management**: Regular cache cleanup and monitoring
2. **Log Rotation**: Implement log rotation for long-running deployments
3. **Update Strategy**: Plan for Media Audit updates and migrations
4. **Performance Tuning**: Regularly review and optimize scan performance