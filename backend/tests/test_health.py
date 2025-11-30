"""
Tests for health check endpoint.
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root health check endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "YT-Archiver" in data["message"]


def test_root_returns_version(client: TestClient):
    """Test that root endpoint returns version info."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["version"] == "2.0.0"
