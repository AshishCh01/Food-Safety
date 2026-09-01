import httpx
import pytest

from app.core.config import Settings
from app.services import storage_service


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, response: _FakeResponse | Exception) -> None:
        self._response = response

    def get(self, url, headers=None, timeout=None):
        if isinstance(self._response, Exception):
            raise self._response
        return self._response


@pytest.fixture(autouse=True)
def _configured_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        storage_service,
        "get_settings",
        lambda: Settings(_env_file=None, supabase_url="https://example.supabase.co"),
    )


def test_get_bucket_public_returns_none_when_supabase_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(storage_service, "get_settings", lambda: Settings(_env_file=None, supabase_url=""))

    assert storage_service.get_bucket_public("complaint-evidence") is None


def test_get_bucket_public_returns_true_for_a_public_bucket(monkeypatch) -> None:
    monkeypatch.setattr(
        storage_service, "_client", lambda: _FakeClient(_FakeResponse(200, {"public": True}))
    )

    assert storage_service.get_bucket_public("complaint-evidence") is True


def test_get_bucket_public_returns_false_for_a_private_bucket(monkeypatch) -> None:
    monkeypatch.setattr(
        storage_service, "_client", lambda: _FakeClient(_FakeResponse(200, {"public": False}))
    )

    assert storage_service.get_bucket_public("complaint-evidence") is False


def test_get_bucket_public_returns_none_on_non_200_response(monkeypatch) -> None:
    monkeypatch.setattr(storage_service, "_client", lambda: _FakeClient(_FakeResponse(404)))

    assert storage_service.get_bucket_public("missing-bucket") is None


def test_get_bucket_public_returns_none_on_network_error(monkeypatch) -> None:
    monkeypatch.setattr(
        storage_service, "_client", lambda: _FakeClient(httpx.ConnectError("no route to host"))
    )

    assert storage_service.get_bucket_public("complaint-evidence") is None
