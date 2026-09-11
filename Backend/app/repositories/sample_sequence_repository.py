from datetime import timezone
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sample_sequence import SampleSequence


def next_sequence_number(db: Session, year: int) -> int:
    """Atomically increment and return the next sample sequence number for year.

    Uses SELECT FOR UPDATE to prevent concurrent duplicates (same pattern as
    complaint_sequence_repository).
    """
    row = db.execute(
        select(SampleSequence).where(SampleSequence.year == year).with_for_update()
    ).scalar_one_or_none()
    if row is None:
        row = SampleSequence(year=year, last_value=1)
        db.add(row)
        db.flush()
        return 1
    row.last_value += 1
    db.flush()
    return row.last_value