"""
Request-scoped context utilities.

Provides a ContextVar-backed request_id so logs and error handlers can
correlate events across the lifetime of a request.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from typing import Optional


_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_request_id() -> Optional[str]:
    """Return the current request id (if any)."""
    return _request_id.get()


def set_request_id(request_id: str) -> Token[Optional[str]]:
    """Set the current request id, returning a token for later reset."""
    return _request_id.set(request_id)


def reset_request_id(token: Token[Optional[str]]) -> None:
    """Reset request id to the previous value."""
    _request_id.reset(token)

