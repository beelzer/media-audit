"""HTML report generator with embedded CSS and JavaScript."""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

from jinja2 import Template

from ..models import ScanResult


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Audit Report - {{ scan_time }}</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header-info {
            display: flex;
            gap: 30px;
            font-size: 0.9em;
            opacity: 0.9;
        }

        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #dee2e6;
        }

        .summary-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .summary-card .number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }

        .summary-card .label {
            color: #6c757d;
            margin-top: 5px;
        }

        .controls {
            padding: 20px 30px;
            background: white;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }

        .search-box {
            flex: 1;
            min-width: 300px;
            position: relative;
        }

        .search-box input {
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #dee2e6;
            border-radius: 25px;
            font-size: 14px;
            transition: border-color 0.3s;
        }

        .search-box input:focus {
            outline: none;
            border-color: #667eea;
        }

        .filter-buttons {
            display: flex;
            gap: 10px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 25px;
            background: #e9ecef;
            color: #495057;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 14px;
            font-weight: 500;
        }

        .btn:hover {
            background: #dee2e6;
        }

        .btn.active {
            background: #667eea;
            color: white;
        }

        .tabs {
            display: flex;
            background: #f8f9fa;
            border-bottom: 2px solid #dee2e6;
        }

        .tab {
            padding: 15px 30px;
            cursor: pointer;
            transition: all 0.3s;
            position: relative;
            font-weight: 500;
        }

        .tab:hover {
            background: #e9ecef;
        }

        .tab.active {
            background: white;
            color: #667eea;
        }

        .tab.active::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            right: 0;
            height: 2px;
            background: #667eea;
        }

        .tab-content {
            display: none;
            padding: 30px;
        }

        .tab-content.active {
            display: block;
        }

        .media-grid {
            display: grid;
            gap: 20px;
        }

        .media-item {
            background: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            transition: all 0.3s;
        }

        .media-item:hover {
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }

        .media-item.error {
            border-left: 4px solid #dc3545;
        }

        .media-item.warning {
            border-left: 4px solid #ffc107;
        }

        .media-item.valid {
            border-left: 4px solid #28a745;
        }

        .media-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 15px;
        }

        .media-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #212529;
        }

        .media-path {
            color: #6c757d;
            font-size: 0.85em;
            margin-top: 5px;
            font-family: monospace;
        }

        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }

        .status-badge.error {
            background: #f8d7da;
            color: #721c24;
        }

        .status-badge.warning {
            background: #fff3cd;
            color: #856404;
        }

        .status-badge.valid {
            background: #d4edda;
            color: #155724;
        }

        .issues-list {
            margin-top: 15px;
        }

        .issue {
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            font-size: 0.9em;
        }

        .issue.error {
            background: #f8d7da;
            color: #721c24;
        }

        .issue.warning {
            background: #fff3cd;
            color: #856404;
        }

        .assets-info {
            display: flex;
            gap: 15px;
            margin-top: 10px;
            flex-wrap: wrap;
        }

        .asset-badge {
            padding: 4px 8px;
            background: #e9ecef;
            border-radius: 4px;
            font-size: 0.85em;
            color: #495057;
        }

        .asset-badge.present {
            background: #d4edda;
            color: #155724;
        }

        .asset-badge.missing {
            background: #f8d7da;
            color: #721c24;
        }

        footer {
            background: #f8f9fa;
            padding: 20px 30px;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }

        .no-items {
            text-align: center;
            padding: 60px;
            color: #6c757d;
        }

        @media (max-width: 768px) {
            .container {
                margin: 0;
                border-radius: 0;
            }

            h1 {
                font-size: 1.8em;
            }

            .tabs {
                overflow-x: auto;
            }

            .controls {
                flex-direction: column;
                align-items: stretch;
            }

            .search-box {
                min-width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📺 Media Audit Report</h1>
            <div class="header-info">
                <span>📅 {{ scan_time }}</span>
                <span>⏱️ {{ "%.2f"|format(duration) }}s</span>
                <span>📁 {{ root_paths|length }} root path(s)</span>
            </div>
        </header>

        <div class="summary">
            <div class="summary-card">
                <div class="number">{{ total_items }}</div>
                <div class="label">Total Items</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ movies|length }}</div>
                <div class="label">Movies</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ series|length }}</div>
                <div class="label">TV Series</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ total_issues }}</div>
                <div class="label">Issues Found</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ error_count }}</div>
                <div class="label">Errors</div>
            </div>
            <div class="summary-card">
                <div class="number">{{ warning_count }}</div>
                <div class="label">Warnings</div>
            </div>
        </div>

        <div class="controls">
            <div class="search-box">
                <input type="text" id="searchInput" placeholder="Search by name or path...">
            </div>
            <div class="filter-buttons">
                <button class="btn active" onclick="filterItems('all')">All Items</button>
                <button class="btn" onclick="filterItems('problems')">Problems Only</button>
                <button class="btn" onclick="filterItems('valid')">Valid Only</button>
            </div>
        </div>

        <div class="tabs">
            <div class="tab active" onclick="showTab('movies')">Movies ({{ movies|length }})</div>
            <div class="tab" onclick="showTab('tv')">TV Shows ({{ series|length }})</div>
        </div>

        <div id="movies" class="tab-content active">
            <div class="media-grid">
                {% if movies %}
                    {% for movie in movies %}
                    <div class="media-item {{ movie.status.value }}" data-name="{{ movie.name|lower }}" data-path="{{ movie.path|lower }}">
                        <div class="media-header">
                            <div>
                                <div class="media-title">{{ movie.name }}{% if movie.year %} ({{ movie.year }}){% endif %}</div>
                                <div class="media-path">{{ movie.path }}</div>
                            </div>
                            <span class="status-badge {{ movie.status.value }}">{{ movie.status.value|upper }}</span>
                        </div>
                        
                        <div class="assets-info">
                            <span class="asset-badge {{ 'present' if movie.assets.posters else 'missing' }}">
                                Poster: {{ 'Yes' if movie.assets.posters else 'No' }}
                            </span>
                            <span class="asset-badge {{ 'present' if movie.assets.backgrounds else 'missing' }}">
                                Background: {{ 'Yes' if movie.assets.backgrounds else 'No' }}
                            </span>
                            <span class="asset-badge {{ 'present' if movie.assets.trailers else 'missing' }}">
                                Trailer: {{ 'Yes' if movie.assets.trailers else 'No' }}
                            </span>
                            {% if movie.video_info and movie.video_info.codec %}
                            <span class="asset-badge">Codec: {{ movie.video_info.codec.value|upper }}</span>
                            {% endif %}
                        </div>

                        {% if movie.issues %}
                        <div class="issues-list">
                            {% for issue in movie.issues %}
                            <div class="issue {{ issue.severity.value }}">
                                <strong>{{ issue.category }}:</strong> {{ issue.message }}
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="no-items">No movies found</div>
                {% endif %}
            </div>
        </div>

        <div id="tv" class="tab-content">
            <div class="media-grid">
                {% if series %}
                    {% for show in series %}
                    <div class="media-item {{ show.status.value }}" data-name="{{ show.name|lower }}" data-path="{{ show.path|lower }}">
                        <div class="media-header">
                            <div>
                                <div class="media-title">{{ show.name }}</div>
                                <div class="media-path">{{ show.path }}</div>
                            </div>
                            <span class="status-badge {{ show.status.value }}">{{ show.status.value|upper }}</span>
                        </div>
                        
                        <div class="assets-info">
                            <span class="asset-badge">{{ show.total_episodes }} episodes</span>
                            <span class="asset-badge">{{ show.seasons|length }} seasons</span>
                            <span class="asset-badge {{ 'present' if show.assets.posters else 'missing' }}">
                                Poster: {{ 'Yes' if show.assets.posters else 'No' }}
                            </span>
                            <span class="asset-badge {{ 'present' if show.assets.backgrounds else 'missing' }}">
                                Background: {{ 'Yes' if show.assets.backgrounds else 'No' }}
                            </span>
                        </div>

                        {% if show.issues %}
                        <div class="issues-list">
                            {% for issue in show.issues %}
                            <div class="issue {{ issue.severity.value }}">
                                <strong>{{ issue.category }}:</strong> {{ issue.message }}
                            </div>
                            {% endfor %}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="no-items">No TV shows found</div>
                {% endif %}
            </div>
        </div>

        <footer>
            <p>Generated on {{ scan_time }} | Duration: {{ "%.2f"|format(duration) }} seconds</p>
            <p>Scanned: {{ root_paths|join(", ") }}</p>
        </footer>
    </div>

    <script>
        let currentFilter = 'all';
        let currentTab = 'movies';

        function showTab(tabName) {
            // Update tabs
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            currentTab = tabName;
            
            // Reapply filters
            applyFilters();
        }

        function filterItems(filterType) {
            currentFilter = filterType;
            
            // Update buttons
            document.querySelectorAll('.filter-buttons .btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            applyFilters();
        }

        function applyFilters() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const items = document.querySelectorAll(`#${currentTab} .media-item`);
            
            items.forEach(item => {
                const name = item.dataset.name;
                const path = item.dataset.path;
                const status = item.classList.contains('error') ? 'error' : 
                              item.classList.contains('warning') ? 'warning' : 'valid';
                
                let show = true;
                
                // Search filter
                if (searchTerm && !name.includes(searchTerm) && !path.includes(searchTerm)) {
                    show = false;
                }
                
                // Status filter
                if (currentFilter === 'problems' && status === 'valid') {
                    show = false;
                } else if (currentFilter === 'valid' && status !== 'valid') {
                    show = false;
                }
                
                item.style.display = show ? 'block' : 'none';
            });
        }

        // Search functionality
        document.getElementById('searchInput').addEventListener('input', applyFilters);

        // Sort functionality
        function sortItems(sortBy) {
            const container = document.querySelector(`#${currentTab} .media-grid`);
            const items = Array.from(container.querySelectorAll('.media-item'));
            
            items.sort((a, b) => {
                if (sortBy === 'name') {
                    return a.dataset.name.localeCompare(b.dataset.name);
                } else if (sortBy === 'status') {
                    const statusOrder = { 'error': 0, 'warning': 1, 'valid': 2 };
                    const aStatus = a.classList.contains('error') ? 'error' : 
                                  a.classList.contains('warning') ? 'warning' : 'valid';
                    const bStatus = b.classList.contains('error') ? 'error' : 
                                  b.classList.contains('warning') ? 'warning' : 'valid';
                    return statusOrder[aStatus] - statusOrder[bStatus];
                }
            });
            
            items.forEach(item => container.appendChild(item));
        }
    </script>
</body>
</html>"""


class HTMLReportGenerator:
    """Generates beautiful HTML reports from scan results."""

    def generate(self, result: ScanResult, output_path: Path, problems_only: bool = False) -> None:
        """Generate HTML report file."""
        template = Template(HTML_TEMPLATE)
        
        # Calculate counts
        error_count = sum(
            1 for issue in self._get_all_issues(result)
            if issue.severity.value == "error"
        )
        warning_count = sum(
            1 for issue in self._get_all_issues(result)
            if issue.severity.value == "warning"
        )

        # Filter items if problems_only
        movies = result.movies
        series = result.series
        if problems_only:
            movies = [m for m in movies if m.has_issues]
            series = [s for s in series if s.has_issues]

        # Render template
        html = template.render(
            scan_time=result.scan_time.strftime("%Y-%m-%d %H:%M:%S"),
            duration=result.duration,
            root_paths=[str(p) for p in result.root_paths],
            total_items=result.total_items,
            total_issues=result.total_issues,
            error_count=error_count,
            warning_count=warning_count,
            movies=movies,
            series=series,
            errors=result.errors,
        )

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write HTML file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    def _get_all_issues(self, result: ScanResult):
        """Get all issues from scan result."""
        issues = []
        for movie in result.movies:
            issues.extend(movie.issues)
        for series in result.series:
            issues.extend(series.issues)
            for season in series.seasons:
                issues.extend(season.issues)
                for episode in season.episodes:
                    issues.extend(episode.issues)
        return issues