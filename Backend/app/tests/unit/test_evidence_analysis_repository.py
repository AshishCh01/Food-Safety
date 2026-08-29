from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.evidence_analysis import EvidenceAnalysis
from app.repositories import evidence_analysis_repository
from app.tests.factories import (
    create_complaint,
    create_complaint_category,
    create_district,
    create_division,
    create_evidence,
    create_user,
)
from app.utils.enums import EvidenceAnalysisStatus


def _setup(db: Session):
    division = create_division(db, name="Pune Division", code="PUN")
    district = create_district(db, division, name="Pune", code="PUN")
    category = create_complaint_category(db)
    citizen = create_user(db, email="citizen@example.com")
    complaint = create_complaint(db, citizen, district, category)
    return complaint, citizen


def _add_analysis(
    db: Session,
    evidence_id,
    requested_by_id,
    *,
    product_name: str,
    status=EvidenceAnalysisStatus.COMPLETED,
    created_at: datetime | None = None,
) -> EvidenceAnalysis:
    # created_at is set explicitly (rather than relying on the server
    # default) so two analyses for the same evidence item have a
    # deterministic ordering - SQLite's CURRENT_TIMESTAMP only has
    # second-level resolution, so two rows inserted in the same test could
    # otherwise tie.
    analysis = EvidenceAnalysis(
        evidence_id=evidence_id,
        requested_by_user_id=requested_by_id,
        status=status,
        model_used="gemini-3.7-flash",
        product_name=product_name,
        created_at=created_at or datetime.now(timezone.utc),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return analysis


def test_get_latest_by_evidence_ids_returns_one_result_per_evidence_item(db_session: Session) -> None:
    complaint, citizen = _setup(db_session)
    evidence_one = create_evidence(db_session, complaint, citizen, file_name="one.jpg")
    evidence_two = create_evidence(db_session, complaint, citizen, file_name="two.jpg")
    evidence_three = create_evidence(db_session, complaint, citizen, file_name="three.jpg")  # no analysis at all

    # Two analyses for evidence_one - the batch lookup must return only the
    # latest one, matching get_latest_by_evidence's single-item behavior.
    now = datetime.now(timezone.utc)
    _add_analysis(db_session, evidence_one.id, citizen.id, product_name="Old Milk Brand", created_at=now)
    newest_for_one = _add_analysis(
        db_session, evidence_one.id, citizen.id, product_name="New Milk Brand", created_at=now + timedelta(seconds=5)
    )
    newest_for_two = _add_analysis(db_session, evidence_two.id, citizen.id, product_name="Bread Brand", created_at=now)

    latest = evidence_analysis_repository.get_latest_by_evidence_ids(
        db_session, [evidence_one.id, evidence_two.id, evidence_three.id]
    )

    assert set(latest.keys()) == {evidence_one.id, evidence_two.id}
    assert latest[evidence_one.id].id == newest_for_one.id
    assert latest[evidence_one.id].product_name == "New Milk Brand"
    assert latest[evidence_two.id].id == newest_for_two.id
    assert evidence_three.id not in latest

    # Must agree with the single-item lookup for every evidence item.
    for evidence_id in (evidence_one.id, evidence_two.id):
        single = evidence_analysis_repository.get_latest_by_evidence(db_session, evidence_id)
        assert single is not None
        assert latest[evidence_id].id == single.id


def test_get_latest_by_evidence_ids_returns_empty_dict_for_no_ids(db_session: Session) -> None:
    assert evidence_analysis_repository.get_latest_by_evidence_ids(db_session, []) == {}
