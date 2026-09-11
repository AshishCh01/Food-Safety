from app.core.database import SessionLocal
from app.models.complaint_clarification import ComplaintClarification
from app.models.complaint_status_history import ComplaintStatusHistory
from sqlalchemy import select

db = SessionLocal()
clarifications = db.execute(select(ComplaintClarification).where(ComplaintClarification.response_message.is_not(None))).scalars().all()
for c in clarifications:
    print(f"Complaint: {c.complaint_id}, response: {c.response_message}")
    history = db.execute(
        select(ComplaintStatusHistory)
        .where(
            ComplaintStatusHistory.complaint_id == c.complaint_id,
            ComplaintStatusHistory.new_status == 'under_review'
        )
        .order_by(ComplaintStatusHistory.created_at.desc())
    ).scalars().first()
    
    if history:
        print(f"Found history: {history.reason}")
        if history.reason == "Citizen provided requested information.":
            history.reason = f"Citizen provided requested information: {c.response_message}"
            print("Updated!")

db.commit()
db.close()