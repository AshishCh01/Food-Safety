import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services import geocoding_service
from app.tests.factories import auth_headers, create_complaint_category, create_district, create_division, create_user


def _setup(db_session: Session):
    division = create_division(db_session, name="Test Division", code="TST")
    pune = create_district(
        db_session, division, name="Pune", code="PUN", centroid_latitude=18.5204, centroid_longitude=73.8567
    )
    nagpur = create_district(
        db_session, division, name="Nagpur", code="NGP", centroid_latitude=21.1458, centroid_longitude=79.0882
    )
    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")
    return pune, nagpur, category, citizen


def _payload(district_id, category_id, **overrides) -> dict:
    payload = {
        "category_id": str(category_id),
        "district_id": str(district_id),
        "title": "Expired dairy products on sale",
        "description": "Found expired milk packets still being sold at the counter this morning.",
        "priority": "high",
        "business": {
            "business_name": "Green Grocers",
            "address": "Shop 4, FC Road, Pune",
        },
    }
    payload.update(overrides)
    return payload


def test_complaint_creation_rejects_out_of_range_coordinates(client: TestClient, db_session: Session) -> None:
    pune, _nagpur, category, citizen = _setup(db_session)
    payload = _payload(pune.id, category.id, latitude=999.0, longitude=73.86)

    response = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


def test_complaint_creation_rejects_lone_coordinate(client: TestClient, db_session: Session) -> None:
    pune, _nagpur, category, citizen = _setup(db_session)
    payload = _payload(pune.id, category.id, latitude=18.52, longitude=None)

    response = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


def test_complaint_district_is_derived_from_coordinates_not_client_field(
    client: TestClient, db_session: Session
) -> None:
    """Per docs/PROJECT_SPEC.md section 11, a citizen-supplied district_id
    must not be the sole source of routing truth: when coordinates are
    given, the backend derives (and here overrides) the district from them.
    """
    pune, nagpur, category, citizen = _setup(db_session)
    # Client claims Pune, but the coordinates are right next to Nagpur's
    # centroid - the backend must route this to Nagpur regardless.
    payload = _payload(pune.id, category.id, latitude=21.15, longitude=79.09)

    response = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen))

    assert response.status_code == 201
    body = response.json()
    assert body["district_id"] == str(nagpur.id)
    assert body["district_name"] == "Nagpur"


def test_complaint_without_coordinates_trusts_client_supplied_district(
    client: TestClient, db_session: Session
) -> None:
    pune, _nagpur, category, citizen = _setup(db_session)
    payload = _payload(pune.id, category.id)

    response = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen))

    assert response.status_code == 201
    assert response.json()["district_id"] == str(pune.id)


def test_business_creation_rejects_invalid_coordinates(client: TestClient, db_session: Session) -> None:
    pune, _nagpur, category, citizen = _setup(db_session)
    payload = _payload(pune.id, category.id)
    payload["business"]["latitude"] = 18.52
    payload["business"]["longitude"] = 200.0

    response = client.post("/api/v1/complaints", json=payload, headers=auth_headers(citizen))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


def test_reverse_geocode_returns_address_on_success(client: TestClient, db_session: Session, monkeypatch) -> None:
    _pune, _nagpur, _category, citizen = _setup(db_session)

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"display_name": "FC Road, Pune, Maharashtra, India"}

    monkeypatch.setattr(httpx, "get", lambda *args, **kwargs: FakeResponse())

    response = client.get(
        "/api/v1/reverse-geocode", params={"lat": 18.52, "lon": 73.86}, headers=auth_headers(citizen)
    )

    assert response.status_code == 200
    assert response.json()["address"] == "FC Road, Pune, Maharashtra, India"


def test_reverse_geocode_degrades_gracefully_on_failure(client: TestClient, db_session: Session, monkeypatch) -> None:
    _pune, _nagpur, _category, citizen = _setup(db_session)

    def _raise(*args, **kwargs):
        raise httpx.ConnectError("network unavailable")

    monkeypatch.setattr(httpx, "get", _raise)

    response = client.get(
        "/api/v1/reverse-geocode", params={"lat": 18.52, "lon": 73.86}, headers=auth_headers(citizen)
    )

    assert response.status_code == 200
    assert response.json()["address"] is None


def test_reverse_geocode_rejects_invalid_coordinates(client: TestClient, db_session: Session) -> None:
    _pune, _nagpur, _category, citizen = _setup(db_session)

    response = client.get(
        "/api/v1/reverse-geocode", params={"lat": 999.0, "lon": 73.86}, headers=auth_headers(citizen)
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_COORDINATES"


def test_reverse_geocode_service_returns_none_when_disabled(monkeypatch) -> None:
    from app.core.config import Settings

    disabled_settings = Settings(enable_reverse_geocoding=False)
    monkeypatch.setattr(geocoding_service, "get_settings", lambda: disabled_settings)

    assert geocoding_service.reverse_geocode(18.52, 73.86) is None
