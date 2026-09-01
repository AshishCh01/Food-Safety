import asyncio

from app.core import middleware as middleware_module
from app.core.middleware import MaxBodySizeMiddleware


class _FakeSettings:
    def __init__(self, max_mb: int) -> None:
        self.max_request_body_size_mb = max_mb


async def _echo_app(scope, receive, send):
    """A minimal downstream app that reads the full body (looping until
    `more_body` is false) then sends a normal 200 - used to prove
    MaxBodySizeMiddleware intercepts before this app ever gets to respond,
    once the streamed body exceeds the configured limit."""
    body = b""
    while True:
        message = await receive()
        if message["type"] == "http.disconnect":
            return
        body += message.get("body", b"")
        if not message.get("more_body", False):
            break
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": body})


def _scope(headers: list[tuple[bytes, bytes]] | None = None) -> dict:
    return {"type": "http", "method": "POST", "path": "/test", "headers": headers or []}


def _chunk_messages(chunks: list[bytes]) -> list[dict]:
    return [
        {"type": "http.request", "body": chunk, "more_body": i < len(chunks) - 1}
        for i, chunk in enumerate(chunks)
    ]


class _ReceiveQueue:
    def __init__(self, messages: list[dict]) -> None:
        self._messages = list(messages)

    async def __call__(self) -> dict:
        if not self._messages:
            return {"type": "http.disconnect"}
        return self._messages.pop(0)


class _SendRecorder:
    def __init__(self) -> None:
        self.messages: list[dict] = []

    async def __call__(self, message: dict) -> None:
        self.messages.append(message)

    @property
    def status(self) -> int | None:
        for message in self.messages:
            if message["type"] == "http.response.start":
                return message["status"]
        return None

    @property
    def response_starts(self) -> int:
        return sum(1 for message in self.messages if message["type"] == "http.response.start")


def test_content_length_over_limit_is_rejected_without_touching_downstream_app() -> None:
    calls = {"count": 0}

    async def _never_called(scope, receive, send):
        calls["count"] += 1

    middleware = MaxBodySizeMiddleware(_never_called, max_bytes=10)
    send = _SendRecorder()
    scope = _scope(headers=[(b"content-length", b"11")])

    asyncio.run(middleware(scope, _ReceiveQueue([]), send))

    assert calls["count"] == 0
    assert send.status == 413


def test_content_length_at_or_under_limit_reaches_downstream_app() -> None:
    middleware = MaxBodySizeMiddleware(_echo_app, max_bytes=10)
    send = _SendRecorder()
    scope = _scope(headers=[(b"content-length", b"10")])
    receive = _ReceiveQueue(_chunk_messages([b"0123456789"]))

    asyncio.run(middleware(scope, receive, send))

    assert send.status == 200


def test_streamed_body_without_content_length_is_rejected_once_it_exceeds_the_limit() -> None:
    """Simulates chunked transfer encoding (no Content-Length header) - the
    only way to bound this is counting bytes as they stream in, since the
    pre-check above has nothing to check up front."""
    middleware = MaxBodySizeMiddleware(_echo_app, max_bytes=10)
    send = _SendRecorder()
    scope = _scope(headers=[])  # no content-length
    receive = _ReceiveQueue(_chunk_messages([b"01234", b"56789", b"extra-bytes-over-limit"]))

    asyncio.run(middleware(scope, receive, send))

    assert send.status == 413
    # Exactly one response was sent - the downstream _echo_app's own 200
    # never went out once the middleware intercepted mid-stream.
    assert send.response_starts == 1


def test_max_bytes_is_read_fresh_from_settings_each_request() -> None:
    """max_bytes is a property, not resolved once in __init__ - a
    request-size-limit change (env var) must take effect without a restart
    being the only thing that would otherwise let it apply."""
    middleware_module_settings = {"mb": 5}
    original_get_settings = middleware_module.get_settings
    try:
        middleware_module.get_settings = lambda: _FakeSettings(middleware_module_settings["mb"])
        middleware = MaxBodySizeMiddleware(_echo_app)

        assert middleware.max_bytes == 5 * 1024 * 1024

        middleware_module_settings["mb"] = 1
        assert middleware.max_bytes == 1 * 1024 * 1024
    finally:
        middleware_module.get_settings = original_get_settings
