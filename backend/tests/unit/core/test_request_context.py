"""
Unit tests for request context utilities.
"""
from app.core.request_context import get_request_id, set_request_id, reset_request_id


def test_set_get_reset_request_id() -> None:
    assert get_request_id() is None
    token = set_request_id("req-123")
    assert get_request_id() == "req-123"
    reset_request_id(token)
    assert get_request_id() is None
