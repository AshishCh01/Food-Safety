from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.tests.factories import auth_headers, create_district, create_division, create_staff
from app.utils.enums import UserRole


def _setup_two_districts(db_session: Session):
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    nagpur = create_district(db_session, division, name="Nagpur", code="NGP")

    pune_officer, _ = create_staff(
        db_session, pune, role=UserRole.DISTRICT_OFFICER, email="pune.officer@example.com", employee_code="DO-PUN"
    )
    pune_inspector, _ = create_staff(
        db_session, pune, role=UserRole.INSPECTOR, email="pune.inspector@example.com", employee_code="INS-PUN"
    )
    nagpur_officer, _ = create_staff(
        db_session, nagpur, role=UserRole.DISTRICT_OFFICER, email="nagpur.officer@example.com", employee_code="DO-NGP"
    )
    nagpur_inspector, _ = create_staff(
        db_session, nagpur, role=UserRole.INSPECTOR, email="nagpur.inspector@example.com", employee_code="INS-NGP"
    )

    return pune, nagpur, pune_officer, pune_inspector, nagpur_officer, nagpur_inspector


def test_officer_only_sees_inspectors_in_own_district(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, pune_inspector, nagpur_officer, nagpur_inspector = _setup_two_districts(db_session)

    response = client.get("/api/v1/officer/inspectors", headers=auth_headers(pune_officer))

    assert response.status_code == 200
    inspectors = response.json()
    emails = {item["email"] for item in inspectors}
    assert emails == {"pune.inspector@example.com"}
    assert "nagpur.inspector@example.com" not in emails


def test_officer_scope_cannot_be_overridden_by_query_params(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, pune_inspector, nagpur_officer, nagpur_inspector = _setup_two_districts(db_session)

    # The officer endpoint takes no district_id parameter at all - scope is
    # derived solely from the authenticated officer's own staff profile, so
    # there is nothing a client could tamper with to reach another district.
    response = client.get(
        "/api/v1/officer/inspectors",
        params={"district_id": str(nagpur.id)},
        headers=auth_headers(pune_officer),
    )

    assert response.status_code == 200
    emails = {item["email"] for item in response.json()}
    assert emails == {"pune.inspector@example.com"}


def test_officer_dashboard_reports_own_district_only(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, pune_inspector, nagpur_officer, nagpur_inspector = _setup_two_districts(db_session)

    response = client.get("/api/v1/officer/dashboard", headers=auth_headers(pune_officer))

    assert response.status_code == 200
    body = response.json()
    assert body["district_code"] == "PUN"
    assert body["inspector_count"] == 1


def test_inspector_dashboard_reports_own_district(client: TestClient, db_session: Session) -> None:
    pune, nagpur, pune_officer, pune_inspector, nagpur_officer, nagpur_inspector = _setup_two_districts(db_session)

    response = client.get("/api/v1/inspector/dashboard", headers=auth_headers(nagpur_inspector))

    assert response.status_code == 200
    assert response.json()["district_code"] == "NGP"


def test_forged_token_district_claim_does_not_grant_access(client: TestClient, db_session: Session) -> None:
    """The access token carries a district_id claim for convenience, but
    server-side authorization must derive scope from the staff_profiles
    table, not from the token claim, so a stale/forged claim cannot grant
    cross-district access."""
    pune, nagpur, pune_officer, pune_inspector, nagpur_officer, nagpur_inspector = _setup_two_districts(db_session)

    # Build a token for the Pune officer but stamp Nagpur's district_id into
    # the (unused-for-authz) claim to simulate a forged/stale claim.
    headers = auth_headers(pune_officer, district_id=nagpur.id)

    response = client.get("/api/v1/officer/inspectors", headers=headers)

    assert response.status_code == 200
    emails = {item["email"] for item in response.json()}
    assert emails == {"pune.inspector@example.com"}
