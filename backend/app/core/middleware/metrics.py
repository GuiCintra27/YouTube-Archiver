"""
Metrics middleware for Prometheus.
"""
from __future__ import annotations

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.metrics import REQUEST_COUNT, REQUEST_LATENCY


class MetricsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, exclude_paths: set[str] | None = None) -> None:
        super().__init__(app)
        self._exclude_paths = exclude_paths or set()

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        if path in self._exclude_paths:
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start

        REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
        REQUEST_LATENCY.labels(request.method, path).observe(duration)
        return response
