from app.core.config import Settings


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app_name == "Food Safety Platform API"
    assert settings.environment == "development"


def test_cors_origin_list_parses_comma_separated_values() -> None:
    settings = Settings(_env_file=None, cors_origins="http://a.com, http://b.com")

    assert settings.cors_origin_list == ["http://a.com", "http://b.com"]
