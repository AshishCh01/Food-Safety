import enum


class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    INSPECTOR = "inspector"
    DISTRICT_OFFICER = "district_officer"
    ADMIN = "admin"


STAFF_ROLES = (UserRole.INSPECTOR, UserRole.DISTRICT_OFFICER)


class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    NEEDS_INFORMATION = "needs_information"
    VERIFIED = "verified"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    ASSIGNED = "assigned"
    INSPECTION_SCHEDULED = "inspection_scheduled"
    UNDER_INSPECTION = "under_inspection"
    INSPECTION_COMPLETED = "inspection_completed"
    ACTION_IN_PROGRESS = "action_in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class ComplaintPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AssignmentStatus(str, enum.Enum):
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class InspectionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class FindingSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TriageStatus(str, enum.Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class EvidenceAnalysisStatus(str, enum.Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class InvestigationStatus(str, enum.Enum):
    COMPLETED = "completed"
    FAILED = "failed"


class RagDocumentType(str, enum.Enum):
    LAW = "law"
    REGULATION = "regulation"
    INSPECTION_GUIDELINE = "inspection_guideline"
    HYGIENE_GUIDELINE = "hygiene_guideline"
    SAMPLING_PROCEDURE = "sampling_procedure"
    RECALL_PROCEDURE = "recall_procedure"
    LICENSING = "licensing"
    DEPARTMENT_SOP = "department_sop"
    OTHER = "other"


# Document types considered when an inspector's question is regulatory/legal in
# nature (search_regulations).
REGULATION_DOCUMENT_TYPES = (
    RagDocumentType.LAW,
    RagDocumentType.REGULATION,
    RagDocumentType.LICENSING,
    RagDocumentType.RECALL_PROCEDURE,
    RagDocumentType.OTHER,
)

# Document types considered when an inspector's question is about how to conduct
# an inspection (search_inspection_guidelines).
INSPECTION_GUIDELINE_DOCUMENT_TYPES = (
    RagDocumentType.INSPECTION_GUIDELINE,
    RagDocumentType.HYGIENE_GUIDELINE,
    RagDocumentType.SAMPLING_PROCEDURE,
    RagDocumentType.DEPARTMENT_SOP,
)


class RagDocumentStatus(str, enum.Enum):
    PENDING = "pending"
    INGESTED = "ingested"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    DEACTIVATED = "deactivated"


class AssistantMessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"


class NotificationType(str, enum.Enum):
    COMPLAINT_SUBMITTED = "complaint_submitted"
    COMPLAINT_VERIFIED = "complaint_verified"
    COMPLAINT_REJECTED = "complaint_rejected"
    INSPECTOR_ASSIGNED = "inspector_assigned"
    INSPECTION_SCHEDULED = "inspection_scheduled"
    INSPECTION_COMPLETED = "inspection_completed"
    COMPLAINT_RESOLVED = "complaint_resolved"
