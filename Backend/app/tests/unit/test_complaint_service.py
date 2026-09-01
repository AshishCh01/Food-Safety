import pytest
from sqlalchemy.orm import Session

from app.repositories import complaint_sequence_repository
from app.schemas.business import BusinessInput
from app.services import business_service, complaint_service
from app.tests.factories import (
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_staff,
    create_user,
)
from app.utils.enums import ComplaintStatus, UserRole
from app.utils.exceptions import InvalidComplaintStatusTransitionError


def test_sequence_numbers_increment_per_district_per_year(db_session: Session) -> None:
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")

    first = complaint_sequence_repository.next_sequence_number(db_session, district.id, 2026)
    second = complaint_sequence_repository.next_sequence_number(db_session, district.id, 2026)
    db_session.commit()

    assert first == 1
    assert second == 2


def test_sequence_numbers_reset_per_year(db_session: Session) -> None:
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")

    this_year = complaint_sequence_repository.next_sequence_number(db_session, district.id, 2026)
    next_year = complaint_sequence_repository.next_sequence_number(db_session, district.id, 2027)
    db_session.commit()

    assert this_year == 1
    assert next_year == 1


def test_sequence_numbers_are_independent_per_district(db_session: Session) -> None:
    division = create_division(db_session, name="Pune Division", code="PUN")
    pune = create_district(db_session, division, name="Pune", code="PUN")
    nagpur = create_district(db_session, division, name="Nagpur", code="NGP")

    pune_seq = complaint_sequence_repository.next_sequence_number(db_session, pune.id, 2026)
    nagpur_seq = complaint_sequence_repository.next_sequence_number(db_session, nagpur.id, 2026)
    db_session.commit()

    assert pune_seq == 1
    assert nagpur_seq == 1


def test_allowed_transitions_exclude_future_phase_states() -> None:
    # Assignment/inspection/resolution states belong to Phase 4+ and must not
    # be reachable through this phase's status-update endpoint.
    reachable = set(complaint_service.ALLOWED_TRANSITIONS[ComplaintStatus.UNDER_REVIEW])
    assert ComplaintStatus.ASSIGNED not in reachable
    assert ComplaintStatus.RESOLVED not in reachable
    assert ComplaintStatus.VERIFIED in reachable


def test_terminal_status_has_no_allowed_transitions() -> None:
    assert complaint_service.ALLOWED_TRANSITIONS.get(ComplaintStatus.REJECTED, set()) == set()


def test_update_status_rejects_disallowed_transition(db_session: Session) -> None:
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")
    category = create_complaint_category(db_session)
    citizen = create_user(db_session, email="citizen@example.com")
    _, officer_profile = create_staff(
        db_session, district, role=UserRole.DISTRICT_OFFICER, email="officer@example.com", employee_code="DO-1"
    )
    complaint = create_complaint(db_session, citizen, district, category)

    with pytest.raises(InvalidComplaintStatusTransitionError):
        complaint_service.update_status(db_session, officer_profile, complaint, ComplaintStatus.RESOLVED, None)


def test_business_get_or_create_reuses_matching_business(db_session: Session) -> None:
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")
    citizen = create_user(db_session, email="citizen@example.com")
    payload = BusinessInput(business_name="Green Grocers", address="Shop 4, FC Road, Pune")

    first = business_service.get_or_create_business(
        db_session, district_id=district.id, created_by_user_id=citizen.id, payload=payload
    )
    second = business_service.get_or_create_business(
        db_session, district_id=district.id, created_by_user_id=citizen.id, payload=payload
    )

    assert first.id == second.id


def test_business_get_or_create_treats_different_address_as_new(db_session: Session) -> None:
    division = create_division(db_session, name="Pune Division", code="PUN")
    district = create_district(db_session, division, name="Pune", code="PUN")
    citizen = create_user(db_session, email="citizen@example.com")

    first = business_service.get_or_create_business(
        db_session,
        district_id=district.id,
        created_by_user_id=citizen.id,
        payload=BusinessInput(business_name="Green Grocers", address="Shop 4, FC Road, Pune"),
    )
    second = business_service.get_or_create_business(
        db_session,
        district_id=district.id,
        created_by_user_id=citizen.id,
        payload=BusinessInput(business_name="Green Grocers", address="Shop 9, MG Road, Pune"),
    )

    assert first.id != second.id
