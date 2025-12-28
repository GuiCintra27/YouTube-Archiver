"""
Request ID middleware.

- Accepts inbound `X-Request-Id` (if provided by the client).
- Otherwise generates a UUID4.
- Stores it in `request.state.request_id` and in a ContextVar.
- Always returns `X-Request-Id` in the response.
"""

from __future__ import annotations

import uuid
from typing import Callable, Optional

from app.core.request_context import reset_request_id, set_request_id


class RequestIdMiddleware:
    def __init__(
        self,
        app,
        header_name: str = "X-Request-Id",
        generator: Optional[Callable[[], str]] = None,
    ) -> None:
        self.app = app
        self.header_name = header_name
        self._header_name_bytes = header_name.lower().encode("latin-1")
        self.generator = generator or (lambda: str(uuid.uuid4()))

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = None
        for key, value in scope.get("headers", []):
            if key == self._header_name_bytes:
                try:
                    request_id = value.decode("utf-8", errors="replace").strip() or None
                except Exception:
                    request_id = None
                break

        if not request_id:
            request_id = self.generator()

        token = set_request_id(request_id)

        scope.setdefault("state", {})
        scope["state"]["request_id"] = request_id

        async def send_wrapper(message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                if not any(key == self._header_name_bytes for key, _ in headers):
                    headers.append((self._header_name_bytes, request_id.encode("utf-8")))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            reset_request_id(token)
