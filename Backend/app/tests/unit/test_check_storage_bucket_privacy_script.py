import pytest

from app.core.config import Settings
from scripts import check_storage_bucket_privacy


def _settings(**overrides) -> Settings:
    fields = {
        "supabase_url": "https://example.supabase.co",
        "supabase_storage_bucket": "evidence-bucket",
        "rag_storage_bucket": "docs-bucket",
    }
    fields.update(overrides)
    return Settings(_env_file=None, **fields)


def test_main_exits_zero_when_supabase_not_configured(monkeypatch) -> None:
    monkeypatch.setattr(check_storage_bucket_privacy, "get_settings", lambda: _settings(supabase_url=""))

    with pytest.raises(SystemExit) as exc_info:
        check_storage_bucket_privacy.main()

    assert exc_info.value.code == 0


def test_main_succeeds_when_every_bucket_is_confirmed_private(monkeypatch) -> None:
    monkeypatch.setattr(check_storage_bucket_privacy, "get_settings", lambda: _settings())
    monkeypatch.setattr(check_storage_bucket_privacy.storage_service, "get_bucket_public", lambda bucket: False)

    check_storage_bucket_privacy.main()  # returns normally - no SystemExit


def test_main_exits_nonzero_when_a_bucket_is_confirmed_public(monkeypatch) -> None:
    monkeypatch.setattr(check_storage_bucket_privacy, "get_settings", lambda: _settings())
    monkeypatch.setattr(
        check_storage_bucket_privacy.storage_service,
        "get_bucket_public",
        lambda bucket: bucket == "evidence-bucket",
    )

    with pytest.raises(SystemExit) as exc_info:
        check_storage_bucket_privacy.main()

    assert exc_info.value.code == 1


def test_main_exits_nonzero_when_a_check_is_inconclusive(monkeypatch) -> None:
    # A check that could not be completed (network error, unexpected
    # response) must not be silently treated as "fine" - the whole point of
    # a scheduled check is to alert a human, and a broken check that always
    # exits 0 would defeat that.
    monkeypatch.setattr(check_storage_bucket_privacy, "get_settings", lambda: _settings())
    monkeypatch.setattr(check_storage_bucket_privacy.storage_service, "get_bucket_public", lambda bucket: None)

    with pytest.raises(SystemExit) as exc_info:
        check_storage_bucket_privacy.main()

    assert exc_info.value.code == 1
