from app.core.database import SessionLocal
from app.models.complaint_clarification import ComplaintClarification
db = SessionLocal()
c = db.query(ComplaintClarification).filter(ComplaintClarification.complaint_id == '82064ee6-0790-4358-9743-daf5052fb539').first()
if c:
    print(c.response_message)
else:
    print('No clarification found')