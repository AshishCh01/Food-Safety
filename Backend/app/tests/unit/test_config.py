from app.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "Food Safety Platform API"
    assert settings.environment == "development"


def test_cors_origin_list_parses_comma_separated_values() -> None:
    settings = Settings(_env_file=None, cors_origins="http://a.com, http://b.com")

    assert settings.cors_origin_list == ["http://a.com", "http://b.com"]


def test_gemini_and_supabase_settings_have_sane_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.gemini_main_model == "gemini-3.6-flash"
    assert settings.gemini_reasoning_model == "gemini-3.6-flash"
    assert settings.gemini_embedding_model == "gemini-embedding-2-preview"
    assert settings.gemini_api_key.get_secret_value() == ""
    assert settings.supabase_storage_bucket == "complaint-evidence"


def test_secrets_are_not_exposed_in_repr() -> None:
    settings = Settings(_env_file=None, gemini_api_key="super-secret-key")

    assert "super-secret-key" not in repr(settings)
    assert "super-secret-key" not in str(settings)
    assert settings.gemini_api_key.get_secret_value() == "super-secret-key"
