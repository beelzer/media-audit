"""Modern HTML report generator with interactive UI."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Template

from media_audit.logging import get_logger
from media_audit.models import ScanResult, ValidationStatus

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Media Audit Report</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --surface: #ffffff;
            --surface-hover: #f8fafc;

            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-tertiary: #94a3b8;

            --border: #e2e8f0;
            --border-hover: #cbd5e1;

            --accent: #6366f1;
            --accent-hover: #4f46e5;
            --accent-light: #eef2ff;

            --success: #10b981;
            --success-light: #d1fae5;
            --warning: #f59e0b;
            --warning-light: #fed7aa;
            --error: #ef4444;
            --error-light: #fee2e2;

            --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
            --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
            --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
            --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #0a0b0d;
                --bg-secondary: #13151a;
                --bg-tertiary: #1a1d23;
                --surface: #1f2329;
                --surface-hover: #262b33;

                --text-primary: #f7f8f9;
                --text-secondary: #b8bfc7;
                --text-tertiary: #6b7280;

                --border: #2d3139;
                --border-hover: #3d414b;

                --accent: #6366f1;
                --accent-hover: #7c7ff3;
                --accent-light: rgba(99, 102, 241, 0.1);

                --success-light: rgba(16, 185, 129, 0.1);
                --warning-light: rgba(245, 158, 11, 0.1);
                --error-light: rgba(239, 68, 68, 0.1);
            }
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.5;
            font-size: 14px;
        }

        /* Layout */
        .layout {
            display: flex;
            height: 100vh;
            overflow: hidden;
        }

        /* Sidebar */
        .sidebar {
            width: 260px;
            background: var(--bg-secondary);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .brand {
            padding: 24px;
            border-bottom: 1px solid var(--border);
        }

        .brand h1 {
            font-size: 20px;
            font-weight: 700;
            background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Stats Cards */
        .stats-container {
            padding: 20px;
            display: grid;
            gap: 12px;
        }

        .stat-card {
            background: var(--surface);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid var(--border);
            transition: all 0.2s;
        }

        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-md);
            border-color: var(--accent);
        }

        .stat-value {
            font-size: 28px;
            font-weight: 700;
            margin-bottom: 4px;
        }

        .stat-label {
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-tertiary);
            font-weight: 500;
        }

        .stat-change {
            font-size: 11px;
            margin-top: 8px;
            padding: 4px 8px;
            border-radius: 20px;
            display: inline-block;
            font-weight: 500;
        }

        .stat-card.error .stat-value { color: var(--error); }
        .stat-card.warning .stat-value { color: var(--warning); }
        .stat-card.success .stat-value { color: var(--success); }

        /* Navigation */
        .nav-section {
            padding: 12px;
            flex: 1;
            overflow-y: auto;
        }

        .nav-title {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-tertiary);
            margin: 16px 8px 8px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 12px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            margin-bottom: 2px;
        }

        .nav-item:hover {
            background: var(--surface-hover);
        }

        .nav-item.active {
            background: var(--accent-light);
            color: var(--accent);
            font-weight: 500;
        }

        .nav-item input[type="checkbox"] {
            width: 16px;
            height: 16px;
            accent-color: var(--accent);
            cursor: pointer;
        }

        .nav-item label {
            flex: 1;
            cursor: pointer;
            margin-left: 8px;
        }

        .badge {
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 10px;
            background: var(--bg-tertiary);
            color: var(--text-tertiary);
            font-weight: 600;
        }

        /* Main Content */
        .main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-secondary);
        }

        /* Header */
        .header {
            background: var(--surface);
            border-bottom: 1px solid var(--border);
            padding: 16px 24px;
            display: flex;
            align-items: center;
            gap: 16px;
            flex-wrap: wrap;
        }

        .search-wrapper {
            flex: 1;
            min-width: 300px;
            max-width: 500px;
            position: relative;
        }

        .search-input {
            width: 100%;
            padding: 10px 16px 10px 40px;
            background: var(--bg-secondary);
            border: 2px solid var(--border);
            border-radius: 12px;
            font-size: 14px;
            color: var(--text-primary);
            transition: all 0.2s;
        }

        .search-input:focus {
            outline: none;
            border-color: var(--accent);
            background: var(--bg-primary);
        }

        .search-icon {
            position: absolute;
            left: 14px;
            top: 50%;
            transform: translateY(-50%);
            color: var(--text-tertiary);
            pointer-events: none;
        }

        .controls {
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .btn-group {
            display: flex;
            background: var(--bg-secondary);
            border-radius: 10px;
            padding: 2px;
            border: 1px solid var(--border);
        }

        .btn {
            padding: 8px 14px;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            border-radius: 8px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }

        .btn.active {
            background: var(--surface);
            color: var(--text-primary);
            box-shadow: var(--shadow-sm);
        }

        .dropdown {
            padding: 10px 14px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }

        .dropdown:hover {
            border-color: var(--border-hover);
        }

        .dropdown:focus {
            outline: none;
            border-color: var(--accent);
        }

        /* Content Area */
        .content {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            background: var(--bg-secondary);
        }

        /* Summary Section */
        .summary-section {
            margin-bottom: 24px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 16px;
        }

        .summary-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }

        .summary-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--accent), var(--warning));
        }

        .summary-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-tertiary);
            margin-bottom: 12px;
        }

        .summary-content {
            display: flex;
            align-items: baseline;
            gap: 8px;
        }

        .summary-value {
            font-size: 32px;
            font-weight: 700;
            color: var(--text-primary);
        }

        .summary-unit {
            font-size: 14px;
            color: var(--text-secondary);
        }

        /* Media Grid */
        .media-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 16px;
        }

        .media-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        /* Media Card */
        .media-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
            overflow: hidden;
        }

        .media-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 3px;
            height: 100%;
            background: var(--accent);
            transform: scaleY(0);
            transition: transform 0.2s;
        }

        .media-card:hover {
            border-color: var(--border-hover);
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }

        .media-card:hover::before {
            transform: scaleY(1);
        }

        .media-card.list-view {
            display: flex;
            align-items: center;
            gap: 16px;
            padding: 12px 16px;
        }

        .media-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }

        .media-title {
            font-size: 15px;
            font-weight: 600;
            color: var(--text-primary);
            line-height: 1.3;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }

        .media-type {
            font-size: 10px;
            font-weight: 600;
            text-transform: uppercase;
            padding: 4px 8px;
            border-radius: 6px;
            background: var(--accent-light);
            color: var(--accent);
            letter-spacing: 0.5px;
            flex-shrink: 0;
        }

        .media-meta {
            font-size: 12px;
            color: var(--text-tertiary);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .media-meta span {
            display: flex;
            align-items: center;
            gap: 4px;
        }

        .media-meta span:not(:last-child)::after {
            content: '•';
            margin-left: 8px;
            color: var(--text-tertiary);
        }

        .media-stats {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }

        .stat-badge {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            transition: all 0.2s;
        }

        .stat-badge.error {
            background: linear-gradient(135deg, #ef4444, #dc2626);
            color: white;
            box-shadow: 0 2px 4px rgba(239, 68, 68, 0.2);
        }

        .stat-badge.warning {
            background: linear-gradient(135deg, #f59e0b, #d97706);
            color: white;
            box-shadow: 0 2px 4px rgba(245, 158, 11, 0.2);
        }

        .stat-badge.success {
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            box-shadow: 0 2px 4px rgba(16, 185, 129, 0.2);
        }

        .stat-badge .count {
            background: rgba(255, 255, 255, 0.3);
            color: white;
            padding: 1px 5px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            min-width: 18px;
            text-align: center;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
            z-index: 1000;
            padding: 40px 20px;
            overflow-y: auto;
        }

        .modal.active {
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.2s;
        }

        .modal-dialog {
            background: var(--surface);
            border-radius: 16px;
            width: 100%;
            max-width: 700px;
            box-shadow: var(--shadow-xl);
            animation: slideUp 0.3s;
        }

        .modal-header {
            padding: 24px;
            border-bottom: 1px solid var(--border);
        }

        .modal-title {
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .modal-close {
            background: none;
            border: none;
            font-size: 24px;
            color: var(--text-tertiary);
            cursor: pointer;
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
        }

        .modal-close:hover {
            background: var(--bg-secondary);
            color: var(--text-primary);
        }

        .modal-body {
            padding: 24px;
        }

        .detail-section {
            margin-bottom: 24px;
        }

        .detail-title {
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: var(--text-tertiary);
            margin-bottom: 12px;
        }

        .detail-grid {
            display: grid;
            grid-template-columns: 120px 1fr;
            gap: 12px;
            font-size: 14px;
        }

        .detail-label {
            color: var(--text-tertiary);
            font-weight: 500;
        }

        .detail-value {
            color: var(--text-primary);
        }

        .detail-value a {
            color: var(--accent);
            text-decoration: none;
            transition: color 0.2s;
        }

        .detail-value a:hover {
            color: var(--accent-hover);
            text-decoration: underline;
        }

        .issues-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }

        .issue-item {
            padding: 12px;
            background: var(--bg-secondary);
            border-radius: 8px;
            border-left: 3px solid;
            font-size: 13px;
        }

        .issue-item.error {
            border-color: var(--error);
            background: var(--error-light);
        }

        .issue-item.warning {
            border-color: var(--warning);
            background: var(--warning-light);
        }

        .issue-category {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.8;
            margin-bottom: 4px;
        }

        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
        }

        .empty-icon {
            font-size: 48px;
            color: var(--text-tertiary);
            margin-bottom: 16px;
        }

        .empty-title {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 8px;
        }

        .empty-text {
            color: var(--text-secondary);
        }

        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        @keyframes slideUp {
            from {
                transform: translateY(20px);
                opacity: 0;
            }
            to {
                transform: translateY(0);
                opacity: 1;
            }
        }

        /* Loading */
        .loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 60px;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        /* Responsive */
        @media (max-width: 768px) {
            .sidebar {
                display: none;
            }

            .media-grid {
                grid-template-columns: 1fr;
            }

            .header {
                flex-direction: column;
                align-items: stretch;
            }

            .search-wrapper {
                max-width: none;
            }
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-secondary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--text-tertiary);
        }
    </style>
</head>
<body>
    <div class="layout">
        <!-- Sidebar -->
        <aside class="sidebar">
            <div class="brand">
                <h1>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="2" y="3" width="20" height="14" rx="2"/>
                        <path d="M8 21h8M12 17v4"/>
                    </svg>
                    Media Audit
                </h1>
            </div>

            <div class="stats-container">
                <div class="stat-card">
                    <div class="stat-value">{{ total_items }}</div>
                    <div class="stat-label">Total Media</div>
                </div>
                <div class="stat-card error">
                    <div class="stat-value">{{ error_count }}</div>
                    <div class="stat-label">Errors Found</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-value">{{ warning_count }}</div>
                    <div class="stat-label">Warnings</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-value">{{ clean_count }}</div>
                    <div class="stat-label">Clean Items</div>
                </div>
            </div>

            <nav class="nav-section">
                <div class="nav-title">Media Type</div>
                <div class="nav-item">
                    <input type="checkbox" id="filter-movies" checked>
                    <label for="filter-movies">Movies</label>
                    <span class="badge">{{ movie_count }}</span>
                </div>
                <div class="nav-item">
                    <input type="checkbox" id="filter-series" checked>
                    <label for="filter-series">TV Series</label>
                    <span class="badge">{{ series_count }}</span>
                </div>

                <div class="nav-title">Status Filter</div>
                <div class="nav-item">
                    <input type="checkbox" id="filter-errors" checked>
                    <label for="filter-errors">Has Errors</label>
                </div>
                <div class="nav-item">
                    <input type="checkbox" id="filter-warnings" checked>
                    <label for="filter-warnings">Has Warnings</label>
                </div>
                <div class="nav-item">
                    <input type="checkbox" id="filter-clean" checked>
                    <label for="filter-clean">No Issues</label>
                </div>

                <div class="nav-title">Issue Types</div>
                <div class="nav-item">
                    <input type="checkbox" id="filter-metadata" checked>
                    <label for="filter-metadata">Metadata</label>
                </div>
                <div class="nav-item">
                    <input type="checkbox" id="filter-codec" checked>
                    <label for="filter-codec">Codec</label>
                </div>
                <div class="nav-item">
                    <input type="checkbox" id="filter-naming" checked>
                    <label for="filter-naming">Naming</label>
                </div>
            </nav>
        </aside>

        <!-- Main Content -->
        <main class="main">
            <header class="header">
                <div class="search-wrapper">
                    <svg class="search-icon" width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="7" cy="7" r="5"/>
                        <path d="M10 10l3 3"/>
                    </svg>
                    <input type="text" class="search-input" placeholder="Search media files...">
                </div>

                <div class="controls">
                    <div class="btn-group">
                        <button class="btn active" data-view="grid">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                                <rect x="1" y="1" width="6" height="6" rx="1"/>
                                <rect x="9" y="1" width="6" height="6" rx="1"/>
                                <rect x="1" y="9" width="6" height="6" rx="1"/>
                                <rect x="9" y="9" width="6" height="6" rx="1"/>
                            </svg>
                        </button>
                        <button class="btn" data-view="list">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
                                <rect x="1" y="2" width="14" height="2" rx="1"/>
                                <rect x="1" y="7" width="14" height="2" rx="1"/>
                                <rect x="1" y="12" width="14" height="2" rx="1"/>
                            </svg>
                        </button>
                    </div>

                    <select class="dropdown">
                        <option value="name">Name</option>
                        <option value="issues">Issues</option>
                        <option value="type">Type</option>
                        <option value="year">Year</option>
                    </select>
                </div>
            </header>

            <div class="content">
                <div id="items-container" class="media-grid"></div>
            </div>
        </main>
    </div>

    <!-- Modal -->
    <div class="modal" id="detailModal">
        <div class="modal-dialog">
            <div class="modal-header">
                <h2 class="modal-title">
                    <span id="modalTitle"></span>
                    <button class="modal-close" onclick="closeModal()">×</button>
                </h2>
            </div>
            <div class="modal-body" id="modalBody"></div>
        </div>
    </div>

    <script>
        // Data
        const scanData = {{ scan_data|safe }};
        let filteredItems = [];
        let currentView = 'grid';
        let currentSort = 'name';
        let loadedCount = 0;
        const ITEMS_PER_PAGE = 50;

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            processData();
            setupEventListeners();
            applyFilters();
        });

        function processData() {
            filteredItems = [
                ...scanData.movies.map(m => ({...m, type: 'movie'})),
                ...scanData.series.map(s => ({...s, type: 'series'}))
            ];
        }

        function setupEventListeners() {
            // Search
            let searchTimeout;
            document.querySelector('.search-input').addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => applyFilters(), 300);
            });

            // View toggle
            document.querySelectorAll('.btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const view = btn.dataset.view;
                    if (view) {
                        document.querySelectorAll('.btn').forEach(b => b.classList.remove('active'));
                        btn.classList.add('active');
                        currentView = view;
                        renderItems();
                    }
                });
            });

            // Sort
            document.querySelector('.dropdown').addEventListener('change', (e) => {
                currentSort = e.target.value;
                sortItems();
                renderItems();
            });

            // Filters
            document.querySelectorAll('.nav-item input').forEach(checkbox => {
                checkbox.addEventListener('change', applyFilters);
            });

            // Infinite scroll
            document.querySelector('.content').addEventListener('scroll', (e) => {
                const el = e.target;
                if (el.scrollTop + el.clientHeight >= el.scrollHeight - 100) {
                    loadMore();
                }
            });
        }

        function applyFilters() {
            const searchTerm = document.querySelector('.search-input').value.toLowerCase();
            const showMovies = document.getElementById('filter-movies').checked;
            const showSeries = document.getElementById('filter-series').checked;
            const showErrors = document.getElementById('filter-errors').checked;
            const showWarnings = document.getElementById('filter-warnings').checked;
            const showClean = document.getElementById('filter-clean').checked;

            let items = [];
            if (showMovies) items.push(...scanData.movies.map(m => ({...m, type: 'movie'})));
            if (showSeries) items.push(...scanData.series.map(s => ({...s, type: 'series'})));

            filteredItems = items.filter(item => {
                const hasErrors = item.issues.some(i => i.severity === 'error');
                const hasWarnings = item.issues.some(i => i.severity === 'warning');
                const isClean = item.issues.length === 0;

                const statusMatch = (hasErrors && showErrors) ||
                                  (hasWarnings && !hasErrors && showWarnings) ||
                                  (isClean && showClean);

                if (!statusMatch) return false;

                if (searchTerm) {
                    return item.name.toLowerCase().includes(searchTerm) ||
                           item.path.toLowerCase().includes(searchTerm);
                }

                return true;
            });

            sortItems();
            renderItems();
        }

        function sortItems() {
            filteredItems.sort((a, b) => {
                switch(currentSort) {
                    case 'name':
                        return a.name.localeCompare(b.name);
                    case 'issues':
                        return b.issues.length - a.issues.length;
                    case 'type':
                        return a.type.localeCompare(b.type);
                    case 'year':
                        return (b.year || 0) - (a.year || 0);
                    default:
                        return 0;
                }
            });
        }

        function renderItems() {
            const container = document.getElementById('items-container');
            container.className = currentView === 'grid' ? 'media-grid' : 'media-list';

            loadedCount = 0;
            container.innerHTML = '';
            loadMore();
        }

        function loadMore() {
            const container = document.getElementById('items-container');
            const items = filteredItems.slice(loadedCount, loadedCount + ITEMS_PER_PAGE);

            if (items.length === 0 && loadedCount === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📂</div>
                        <div class="empty-title">No items found</div>
                        <div class="empty-text">Try adjusting your filters or search terms</div>
                    </div>
                `;
                return;
            }

            items.forEach(item => {
                container.insertAdjacentHTML('beforeend', createItemCard(item));
            });

            loadedCount += items.length;
        }

        function createItemCard(item) {
            const errorCount = item.issues.filter(i => i.severity === 'error').length;
            const warningCount = item.issues.filter(i => i.severity === 'warning').length;
            const listClass = currentView === 'list' ? 'list-view' : '';

            return `
                <div class="media-card ${listClass}" onclick="showDetails('${item.type}', '${escapeHtml(item.name)}')">
                    <div class="media-header">
                        <div class="media-title">${escapeHtml(item.name)}</div>
                        ${currentView === 'grid' ? `<span class="media-type">${item.type}</span>` : ''}
                    </div>
                    <div class="media-meta">
                        <span>${item.year || 'Unknown Year'}</span>
                        <span>${item.type === 'series' ? item.total_episodes + ' episodes' : 'Movie'}</span>
                    </div>
                    <div class="media-stats">
                        ${errorCount > 0 ? `<div class="stat-badge error">Errors <span class="count">${errorCount}</span></div>` : ''}
                        ${warningCount > 0 ? `<div class="stat-badge warning">Warnings <span class="count">${warningCount}</span></div>` : ''}
                        ${item.issues.length === 0 ? '<div class="stat-badge success">✓ Clean</div>' : ''}
                    </div>
                </div>
            `;
        }

        function showDetails(type, name) {
            const items = type === 'movie' ? scanData.movies : scanData.series;
            const item = items.find(i => i.name === name);
            if (!item) return;

            document.getElementById('modalTitle').textContent = item.name;

            let detailsHTML = `
                <div class="detail-section">
                    <div class="detail-title">Information</div>
                    <div class="detail-grid">
                        <div class="detail-label">Path</div>
                        <div class="detail-value">${escapeHtml(item.path)}</div>

                        ${item.year ? `
                            <div class="detail-label">Year</div>
                            <div class="detail-value">${item.year}</div>
                        ` : ''}

                        ${item.imdb_id ? `
                            <div class="detail-label">IMDb</div>
                            <div class="detail-value">
                                <a href="https://www.imdb.com/title/${item.imdb_id}" target="_blank">${item.imdb_id} ↗</a>
                            </div>
                        ` : ''}

                        ${item.tmdb_id ? `
                            <div class="detail-label">TMDB</div>
                            <div class="detail-value">
                                <a href="https://www.themoviedb.org/${item.type === 'movie' ? 'movie' : 'tv'}/${item.tmdb_id}" target="_blank">${item.tmdb_id} ↗</a>
                            </div>
                        ` : ''}

                        ${item.tvdb_id ? `
                            <div class="detail-label">TVDB</div>
                            <div class="detail-value">${item.tvdb_id}</div>
                        ` : ''}

                        ${item.release_group ? `
                            <div class="detail-label">Release Group</div>
                            <div class="detail-value">${item.release_group}</div>
                        ` : ''}

                        ${item.quality ? `
                            <div class="detail-label">Quality</div>
                            <div class="detail-value">${item.quality}</div>
                        ` : ''}

                        ${item.source ? `
                            <div class="detail-label">Source</div>
                            <div class="detail-value">${item.source}</div>
                        ` : ''}
                    </div>
                </div>
            `;

            if (item.issues.length > 0) {
                const errors = item.issues.filter(i => i.severity === 'error');
                const warnings = item.issues.filter(i => i.severity === 'warning');

                detailsHTML += `
                    <div class="detail-section">
                        <div class="detail-title">Issues (${item.issues.length})</div>
                        <div class="issues-list">
                `;

                if (errors.length > 0) {
                    errors.forEach(issue => {
                        detailsHTML += `
                            <div class="issue-item error">
                                <div class="issue-category">${issue.category}</div>
                                <div>${escapeHtml(issue.message)}</div>
                            </div>
                        `;
                    });
                }

                if (warnings.length > 0) {
                    warnings.forEach(issue => {
                        detailsHTML += `
                            <div class="issue-item warning">
                                <div class="issue-category">${issue.category}</div>
                                <div>${escapeHtml(issue.message)}</div>
                            </div>
                        `;
                    });
                }

                detailsHTML += '</div></div>';
            } else {
                detailsHTML += `
                    <div class="detail-section">
                        <div class="detail-title">Status</div>
                        <div class="stat-badge success">✓ No issues found</div>
                    </div>
                `;
            }

            document.getElementById('modalBody').innerHTML = detailsHTML;
            document.getElementById('detailModal').classList.add('active');
        }

        function closeModal() {
            document.getElementById('detailModal').classList.remove('active');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text || '';
            return div.innerHTML;
        }

        // Close modal on outside click
        document.getElementById('detailModal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) {
                closeModal();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                closeModal();
            }
            if (e.key === '/' && e.target.tagName !== 'INPUT') {
                e.preventDefault();
                document.querySelector('.search-input').focus();
            }
        });
    </script>
</body>
</html>"""


class HTMLReportGenerator:
    """Generates modern interactive HTML reports."""

    def __init__(self) -> None:
        """Initialize HTML report generator."""
        self.logger = get_logger("report.html")

    def generate(
        self,
        result: ScanResult,
        output_path: Path,
        problems_only: bool = False,
    ) -> None:
        """Generate HTML report file."""
        # Ensure directory exists
        self.logger.info(f"Generating HTML report: {output_path}")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare data
        movies_data = []
        series_data = []

        for movie in result.movies:
            if problems_only and len(movie.issues) == 0:
                continue
            movies_data.append(self._serialize_movie(movie))

        for series in result.series:
            if problems_only and len(series.issues) == 0:
                continue
            series_data.append(self._serialize_series(series))

        # Count statistics
        error_count = sum(
            1 for m in result.movies for i in m.issues if i.severity == ValidationStatus.ERROR
        )
        error_count += sum(
            1 for s in result.series for i in s.issues if i.severity == ValidationStatus.ERROR
        )

        warning_count = sum(
            1 for m in result.movies for i in m.issues if i.severity == ValidationStatus.WARNING
        )
        warning_count += sum(
            1 for s in result.series for i in s.issues if i.severity == ValidationStatus.WARNING
        )

        clean_count = sum(1 for m in result.movies if len(m.issues) == 0)
        clean_count += sum(1 for s in result.series if len(s.issues) == 0)

        # Prepare scan data as JSON
        scan_data = {
            "movies": movies_data,
            "series": series_data,
        }

        # Render template
        template = Template(HTML_TEMPLATE)
        html_content = template.render(
            scan_data=json.dumps(scan_data),
            total_items=len(movies_data) + len(series_data),
            movie_count=len(movies_data),
            series_count=len(series_data),
            error_count=error_count,
            warning_count=warning_count,
            clean_count=clean_count,
        )

        # Write report
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    def _serialize_movie(self, movie: Any) -> dict[str, Any]:
        """Serialize movie for JSON embedding."""
        return {
            "name": movie.name,
            "path": str(movie.path),
            "year": movie.year,
            "imdb_id": movie.imdb_id,
            "tmdb_id": movie.tmdb_id,
            "release_group": movie.release_group,
            "quality": movie.quality,
            "source": movie.source,
            "issues": [
                {
                    "category": issue.category,
                    "message": issue.message,
                    "severity": issue.severity.value,
                }
                for issue in movie.issues
            ],
        }

    def _serialize_series(self, series: Any) -> dict[str, Any]:
        """Serialize series for JSON embedding."""
        # Aggregate all issues from series and its seasons/episodes
        all_issues = list(series.issues)
        for season in series.seasons:
            all_issues.extend(season.issues)
            for episode in season.episodes:
                all_issues.extend(episode.issues)

        return {
            "name": series.name,
            "path": str(series.path),
            "total_episodes": series.total_episodes,
            "imdb_id": series.imdb_id,
            "tvdb_id": series.tvdb_id,
            "tmdb_id": series.tmdb_id,
            "issues": [
                {
                    "category": issue.category,
                    "message": issue.message,
                    "severity": issue.severity.value,
                }
                for issue in all_issues
            ],
        }
