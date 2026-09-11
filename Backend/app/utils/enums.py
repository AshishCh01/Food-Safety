import enum


class UserRole(str, enum.Enum):
    CITIZEN = "citizen"
    INSPECTOR = "inspector"
    DISTRICT_OFFICER = "district_officer"
    FOOD_ANALYST = "food_analyst"
    ADMIN = "admin"


STAFF_ROLES = (UserRole.INSPECTOR, UserRole.DISTRICT_OFFICER, UserRole.FOOD_ANALYST)


class ComplaintStatus(str, enum.Enum):
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    ASSIGNED = "assigned"
    INSPECTION_SCHEDULED = "inspection_scheduled"
    UNDER_INSPECTION = "under_inspection"
    INSPECTION_COMPLETED = "inspection_completed"
    SAMPLE_PENDING_LAB_RESULT = "sample_pending_lab_result"
    ACTION_IN_PROGRESS = "action_in_progress"
    LEGAL_ACTION_IN_PROGRESS = "legal_action_in_progress"
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
    CLARIFICATION_REQUESTED = "clarification_requested"
    CITIZEN_RESPONDED = "citizen_responded"
    SAMPLE_RESULT_RECEIVED = "sample_result_received"
    LEGAL_ACTION_INITIATED = "legal_action_initiated"


class RefreshSessionRevokedReason(str, enum.Enum):
    """Why a refresh_sessions row was revoked - see
    app/services/auth_service.py for where each is set. Stored as a plain
    string column (not a DB enum type) since this is an internal diagnostic
    tag, not a workflow state with validated transitions."""

    ROTATED = "rotated"
    LOGOUT = "logout"
    ACCOUNT_DEACTIVATED = "account_deactivated"
    REUSE_DETECTED = "reuse_detected"


class SampleStatus(str, enum.Enum):
    COLLECTED = "collected"
    DISPATCHED = "dispatched"
    RECEIVED_AT_LAB = "received_at_lab"
    TESTING_IN_PROGRESS = "testing_in_progress"
    RESULT_RECEIVED = "result_received"


class LabVerdict(str, enum.Enum):
    SAFE = "safe"
    ADULTERATED = "adulterated"
    UNSAFE = "unsafe"
    MISBRANDED = "misbranded"
    MISLEADINGLY_ADVERTISED = "misleadingly_advertised"


# Verdicts that trigger LEGAL_ACTION_IN_PROGRESS on the complaint.
LAB_UNSAFE_VERDICTS = (
    LabVerdict.ADULTERATED,
    LabVerdict.UNSAFE,
    LabVerdict.MISBRANDED,
    LabVerdict.MISLEADINGLY_ADVERTISED,
)


class LegalActionType(str, enum.Enum):
    FINE = "fine"
    LICENCE_SUSPENSION = "licence_suspension"
    LICENCE_CANCELLATION = "licence_cancellation"
    PROSECUTION_REFERRAL = "prosecution_referral"


class LegalActionStatus(str, enum.Enum):
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    CONCLUDED = "concluded"
