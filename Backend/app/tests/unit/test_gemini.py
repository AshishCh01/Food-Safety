from app.core.gemini import get_gemini_client


def test_get_gemini_client_is_cached_and_lazy() -> None:
    """Client construction must not require network access or a real API
    key - it should succeed even with an empty GEMINI_API_KEY, and the
    same instance should be reused across calls."""
    client_one = get_gemini_client()
    client_two = get_gemini_client()

    assert client_one is client_two
