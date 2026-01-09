"""
HTTP helpers with retry/backoff for idempotent requests.
"""
from __future__ import annotations

import time
from typing import Iterable, Optional

import requests
from fastapi.responses import Response

from app.core.logging import get_module_logger

logger = get_module_logger("core.http")


DEFAULT_RETRY_STATUSES = {429, 500, 502, 503, 504}


def request_with_retry(
    method: str,
    url: str,
    *,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    stream: bool = False,
    timeout: Optional[tuple[float, float]] = None,
    retries: int = 0,
    backoff: float = 0.2,
    retry_statuses: Optional[Iterable[int]] = None,
) -> requests.Response:
    method_upper = method.upper()
    retryable = method_upper == "GET" and not stream
    retry_statuses_set = set(retry_statuses or DEFAULT_RETRY_STATUSES)

    attempt = 0
    while True:
        try:
            if method_upper == "GET":
                response = requests.get(
                    url,
                    headers=headers,
                    params=params,
                    stream=stream,
                    timeout=timeout,
                )
            else:
                response = requests.request(
                    method_upper,
                    url,
                    headers=headers,
                    params=params,
                    stream=stream,
                    timeout=timeout,
                )
            if (
                retryable
                and response.status_code in retry_statuses_set
                and attempt < retries
            ):
                response.close()
                sleep_for = backoff * (2**attempt)
                logger.warning(
                    "HTTP %s retry %s/%s for %s (status %s)",
                    method_upper,
                    attempt + 1,
                    retries,
                    url,
                    response.status_code,
                )
                time.sleep(sleep_for)
                attempt += 1
                continue
            return response
        except requests.RequestException as exc:
            if attempt >= retries:
                raise
            sleep_for = backoff * (2**attempt)
            logger.warning(
                "HTTP %s retry %s/%s for %s (error: %s)",
                method_upper,
                attempt + 1,
                retries,
                url,
                exc,
            )
            time.sleep(sleep_for)
            attempt += 1


def build_cache_response(
    content: bytes,
    media_type: str,
    *,
    max_age: int = 86400,
) -> Response:
    return Response(
        content=content,
        media_type=media_type,
        headers={"Cache-Control": f"public, max-age={max_age}"},
    )
