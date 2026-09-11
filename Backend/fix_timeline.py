from app.core.database import SessionLocal
from app.models.complaint_clarification import ComplaintClarification
from app.models.complaint_status_history import ComplaintStatusHistory
from sqlalchemy import select

db = SessionLocal()
clarifications = db.execute(select(ComplaintClarification).where(ComplaintClarification.response_message.is_not(None))).scalars().all()
for c in clarifications:
    # Find the most recent UNDER_REVIEW transition by this citizen for this complaint
    history = db.execute(
        select(ComplaintStatusHistory)
        .where(
            ComplaintStatusHistory.complaint_id == c.complaint_id,
            ComplaintStatusHistory.new_status == 'under_review',
            ComplaintStatusHistory.changed_by_user_id == c.responded_by_user_id
        )
        .order_by(ComplaintStatusHistory.created_at.desc())
    ).scalar_one_or_none()
    
    if history and history.reason == "Citizen provided requested information.":
        history.reason = f"Citizen provided requested information: {c.response_message}"
        print(f"Updated history for complaint {c.complaint_id}")

db.commit()
db.close()