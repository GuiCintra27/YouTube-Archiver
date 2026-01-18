"""
Prometheus metrics helpers.
"""
from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

REQUEST_COUNT = Counter(
    "yt_archiver_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
    "yt_archiver_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

DOWNLOAD_REQUESTS = Counter(
    "yt_archiver_download_requests_total",
    "Download requests accepted via API",
)

VIDEO_INFO_REQUESTS = Counter(
    "yt_archiver_video_info_total",
    "Video info requests served via API",
)

VIDEO_INFO_LATENCY = Histogram(
    "yt_archiver_video_info_duration_seconds",
    "Video info request duration in seconds",
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)

DOWNLOAD_JOBS_STARTED = Counter(
    "yt_archiver_download_jobs_started_total",
    "Download jobs started",
)

DOWNLOAD_JOBS_COMPLETED = Counter(
    "yt_archiver_download_jobs_completed_total",
    "Download jobs completed successfully",
)

DOWNLOAD_JOBS_FAILED = Counter(
    "yt_archiver_download_jobs_failed_total",
    "Download jobs failed",
)

DOWNLOAD_JOBS_ACTIVE = Gauge(
    "yt_archiver_download_jobs_active",
    "Active download jobs",
)

DOWNLOAD_JOB_DURATION = Histogram(
    "yt_archiver_download_job_duration_seconds",
    "Download job duration in seconds",
    buckets=(1, 2.5, 5, 10, 30, 60, 120, 300, 600, 1200, 1800, 3600),
)
