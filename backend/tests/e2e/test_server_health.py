"""
E2E tests that exercise the running API server.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
import requests


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_ready(url: str, timeout: float = 10.0) -> None:
    start = time.time()
    while time.time() - start < timeout:
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                return
        except requests.RequestException:
            pass
        time.sleep(0.2)
    raise AssertionError(f"Server did not become ready within {timeout}s")


@pytest.mark.e2e
def test_server_health_endpoints() -> None:
    port = _find_free_port()
    backend_dir = Path(__file__).resolve().parents[2]

    env = os.environ.copy()
    env["CATALOG_DB_PATH"] = ":memory:"
    env["DRIVE_CACHE_ENABLED"] = "false"
    env["DRIVE_CACHE_FALLBACK_TO_API"] = "false"
    env["WORKER_ROLE"] = "api"

    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=backend_dir,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        base_url = f"http://127.0.0.1:{port}"
        _wait_until_ready(f"{base_url}/api/health")

        health = requests.get(f"{base_url}/api/health", timeout=2)
        assert health.status_code == 200
        payload = health.json()
        assert payload["status"] == "ok"
        assert payload["worker_role"] == "api"

        root = requests.get(f"{base_url}/", timeout=2)
        assert root.status_code == 200
        assert "version" in root.json()

        catalog = requests.get(f"{base_url}/api/catalog/status", timeout=2)
        assert catalog.status_code == 200
        assert "counts" in catalog.json()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
