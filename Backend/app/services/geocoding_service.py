import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def reverse_geocode(latitude: float, longitude: float) -> str | None:
    """Best-effort reverse geocoding via OpenStreetMap's Nominatim service.

    This is advisory only (prefilling an address field for the citizen to
    review/edit) - failures must never block complaint/business creation, so
    any network or parsing error is swallowed and reported as "no address
    found" rather than propagated.
    """
    settings = get_settings()
    if not settings.enable_reverse_geocoding:
        return None

    try:
        response = httpx.get(
            f"{settings.nominatim_base_url}/reverse",
            params={"lat": latitude, "lon": longitude, "format": "jsonv2"},
            headers={"User-Agent": settings.nominatim_user_agent},
            timeout=3.0,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("display_name")
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        logger.warning("Reverse geocoding failed for (%s, %s): %s", latitude, longitude, exc)
        return None
