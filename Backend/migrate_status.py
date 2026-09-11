from app.core.database import SessionLocal
from app.models.complaint import Complaint
from app.models.complaint_status_history import ComplaintStatusHistory
from sqlalchemy import update

db = SessionLocal()
db.execute(update(Complaint).where(Complaint.status == 'needs_information').values(status='insufficient_evidence'))
db.execute(update(ComplaintStatusHistory).where(ComplaintStatusHistory.new_status == 'needs_information').values(new_status='insufficient_evidence'))
db.execute(update(ComplaintStatusHistory).where(ComplaintStatusHistory.old_status == 'needs_information').values(old_status='insufficient_evidence'))
db.commit()
db.close()
print('Migration complete')