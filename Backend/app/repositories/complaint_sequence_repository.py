import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.complaint_sequence import ComplaintSequence


def next_sequence_number(db: Session, district_id: uuid.UUID, year: int) -> int:
    """Returns the next per-district, per-year sequence number.

    Runs within the caller's transaction (no commit here) so complaint
    creation stays atomic. Adequate for this project's expected write
    volume; not safe under heavy concurrent writes to the same district+year.
    """
    stmt = select(ComplaintSequence).where(
        ComplaintSequence.district_id == district_id,
        ComplaintSequence.year == year,
    )
    sequence = db.execute(stmt).scalar_one_or_none()
    if sequence is None:
        sequence = ComplaintSequence(district_id=district_id, year=year, last_seq=0)
        db.add(sequence)
        db.flush()

    sequence.last_seq += 1
    db.flush()
    return sequence.last_seq
