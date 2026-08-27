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
