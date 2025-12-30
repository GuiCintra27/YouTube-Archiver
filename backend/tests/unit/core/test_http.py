"""
Unit tests for HTTP retry helper.
"""
from typing import Any, Dict, Optional, Tuple

import pytest
import requests

from app.core.http import request_with_retry


class _FakeResponse:
    def __init__(self, status_code: int, text: str = "", json_data: Optional[Dict[str, Any]] = None) -> None:
        self.status_code = status_code
        self.text = text
        self._json_data = json_data or {}
        self.closed = False

    def json(self) -> Dict[str, Any]:
        return self._json_data

    def close(self) -> None:
        self.closed = True


def test_retry_get_on_retryable_status(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_get(url: str, headers=None, params=None, stream=False, timeout=None):
        calls["count"] += 1
        if calls["count"] == 1:
            return _FakeResponse(500, text="boom")
        return _FakeResponse(200, json_data={"ok": True})

    monkeypatch.setattr(requests, "get", fake_get)

    response = request_with_retry(
        "GET",
        "http://example.com",
        retries=1,
        backoff=0,
    )
    assert response.status_code == 200
    assert calls["count"] == 2


def test_no_retry_when_streaming(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_get(url: str, headers=None, params=None, stream=False, timeout=None):
        calls["count"] += 1
        return _FakeResponse(500, text="boom")

    monkeypatch.setattr(requests, "get", fake_get)

    response = request_with_retry(
        "GET",
        "http://example.com",
        stream=True,
        retries=2,
        backoff=0,
    )
    assert response.status_code == 500
    assert calls["count"] == 1


def test_retry_on_request_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_get(url: str, headers=None, params=None, stream=False, timeout=None):
        calls["count"] += 1
        if calls["count"] == 1:
            raise requests.RequestException("fail")
        return _FakeResponse(200)

    monkeypatch.setattr(requests, "get", fake_get)

    response = request_with_retry(
        "GET",
        "http://example.com",
        retries=1,
        backoff=0,
    )
    assert response.status_code == 200
    assert calls["count"] == 2


def test_non_get_uses_requests_request(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"method": None, "url": None}

    def fake_request(method: str, url: str, headers=None, params=None, stream=False, timeout=None):
        calls["method"] = method
        calls["url"] = url
        return _FakeResponse(200)

    monkeypatch.setattr(requests, "request", fake_request)

    response = request_with_retry(
        "POST",
        "http://example.com",
        retries=0,
    )
    assert response.status_code == 200
    assert calls["method"] == "POST"
    assert calls["url"] == "http://example.com"
