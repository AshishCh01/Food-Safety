from app.core.database import SessionLocal
from app.models.complaint import Complaint
db = SessionLocal()
c = db.query(Complaint).filter(Complaint.id == '82064ee6-0790-4358-9743-daf5052fb539').first()
print(c.status)