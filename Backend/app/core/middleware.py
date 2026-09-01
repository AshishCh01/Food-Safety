"""Raw ASGI (not `BaseHTTPMiddleware`) request-size limiting.

`BaseHTTPMiddleware` would defeat the purpose here - it fully buffers the
request body itself before handing control to the next layer, which is
exactly the "receive the whole oversized body before anything checks its
size" problem this exists to avoid (see app/utils/uploads.py's own docstring
for the same concern one layer down, which only sees the body *after*
Starlette/python-multipart has already received all of it). A plain ASGI
middleware instead inspects `Content-Length` up front (rejecting before a
single body byte is read, the common case) and also counts bytes as they
stream in via a wrapped `receive`, so a request that omits or understates
its true size (e.g. chunked transfer encoding) is still bounded.
"""

import json

from app.core.config import get_settings


class _RequestTooLarge(Exception):
    pass


def _too_large_response_body(max_bytes: int) -> bytes:
    return json.dumps(
        {
            "error": {
                "code": "REQUEST_TOO_LARGE",
                "message": f"Request body exceeds the maximum allowed size of {max_bytes // (1024 * 1024)}MB.",
                "details": None,
                "request_id": None,
            }
        }
    ).encode("utf-8")


class MaxBodySizeMiddleware:
    """Rejects a request whose body exceeds `max_bytes` with `413`, before
    Starlette's request/multipart parsing ever buffers it. Must be
    registered (via `app.add_middleware`) so it ends up *inside*
    `CORSMiddleware` - i.e. added to the app after the error-handling
    middleware but before `CORSMiddleware` - so a 413 response generated
    here still passes back out through `CORSMiddleware` and carries proper
    CORS headers, matching the ordering rule documented on
    `error_handling_middleware` in app/main.py.
    """

    def __init__(self, app, max_bytes: int | None = None) -> None:
        self.app = app
        self._max_bytes = max_bytes

    @property
    def max_bytes(self) -> int:
        if self._max_bytes is not None:
            return self._max_bytes
        return get_settings().max_request_body_size_mb * 1024 * 1024

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        max_bytes = self.max_bytes

        content_length = _content_length_from_headers(scope.get("headers", []))
        if content_length is not None and content_length > max_bytes:
            await _send_too_large(send, max_bytes)
            return

        total = 0

        async def limited_receive():
            nonlocal total
            message = await receive()
            if message["type"] == "http.request":
                total += len(message.get("body") or b"")
                if total > max_bytes:
                    raise _RequestTooLarge()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _RequestTooLarge:
            await _send_too_large(send, max_bytes)


def _content_length_from_headers(raw_headers: list[tuple[bytes, bytes]]) -> int | None:
    for name, value in raw_headers:
        if name.lower() == b"content-length":
            try:
                return int(value)
            except ValueError:
                return None
    return None


async def _send_too_large(send, max_bytes: int) -> None:
    body = _too_large_response_body(max_bytes)
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
        }
    )
    await send({"type": "http.response.body", "body": body})
