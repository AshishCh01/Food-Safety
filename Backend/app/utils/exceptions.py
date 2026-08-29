class AppError(Exception):
    """Base application error mapped to a consistent API error envelope."""

    code = "APP_ERROR"
    status_code = 400

    def __init__(self, message: str, details: dict | list | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class AuthenticationRequiredError(AppError):
    code = "AUTHENTICATION_REQUIRED"
    status_code = 401

    def __init__(self, message: str = "Authentication is required.") -> None:
        super().__init__(message)


class InvalidCredentialsError(AppError):
    code = "INVALID_CREDENTIALS"
    status_code = 401

    def __init__(self, message: str = "Invalid email or password.") -> None:
        super().__init__(message)


class InvalidTokenError(AppError):
    code = "INVALID_TOKEN"
    status_code = 401

    def __init__(self, message: str = "Invalid or expired token.") -> None:
        super().__init__(message)


class InactiveAccountError(AppError):
    code = "ACCOUNT_INACTIVE"
    status_code = 403

    def __init__(self, message: str = "This account has been deactivated.") -> None:
        super().__init__(message)


class PermissionDeniedError(AppError):
    code = "PERMISSION_DENIED"
    status_code = 403

    def __init__(self, message: str = "You do not have permission to perform this action.") -> None:
        super().__init__(message)


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404

    def __init__(self, message: str = "Resource not found.") -> None:
        super().__init__(message)


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409

    def __init__(self, message: str = "The request conflicts with the current state of the resource.") -> None:
        super().__init__(message)


class UserAlreadyExistsError(ConflictError):
    code = "USER_ALREADY_EXISTS"

    def __init__(self, message: str = "A user with this email already exists.") -> None:
        super().__init__(message)


class ComplaintNotFoundError(NotFoundError):
    code = "COMPLAINT_NOT_FOUND"

    def __init__(self, message: str = "Complaint was not found.") -> None:
        super().__init__(message)


class CategoryNotFoundError(NotFoundError):
    code = "CATEGORY_NOT_FOUND"

    def __init__(self, message: str = "Complaint category was not found.") -> None:
        super().__init__(message)


class BusinessNotFoundError(NotFoundError):
    code = "BUSINESS_NOT_FOUND"

    def __init__(self, message: str = "Business was not found.") -> None:
        super().__init__(message)


class InvalidComplaintStatusTransitionError(ConflictError):
    code = "INVALID_STATUS_TRANSITION"

    def __init__(self, message: str = "This status transition is not allowed.") -> None:
        super().__init__(message)


class EvidenceUploadError(AppError):
    code = "EVIDENCE_UPLOAD_FAILED"
    status_code = 400

    def __init__(self, message: str = "Evidence upload failed.") -> None:
        super().__init__(message)


class UnsupportedFileTypeError(AppError):
    code = "UNSUPPORTED_FILE_TYPE"
    status_code = 415

    def __init__(self, message: str = "This file type is not supported.") -> None:
        super().__init__(message)


class FileTooLargeError(AppError):
    code = "FILE_TOO_LARGE"
    status_code = 413

    def __init__(self, message: str = "This file exceeds the maximum allowed size.") -> None:
        super().__init__(message)


class EvidenceDownloadError(AppError):
    code = "EVIDENCE_DOWNLOAD_FAILED"
    status_code = 502

    def __init__(self, message: str = "Could not retrieve the evidence file from storage.") -> None:
        super().__init__(message)


class EvidenceNotFoundError(NotFoundError):
    code = "EVIDENCE_NOT_FOUND"

    def __init__(self, message: str = "Evidence was not found.") -> None:
        super().__init__(message)


class AssignmentNotFoundError(NotFoundError):
    code = "ASSIGNMENT_NOT_FOUND"

    def __init__(self, message: str = "Assignment was not found.") -> None:
        super().__init__(message)


class InspectionNotFoundError(NotFoundError):
    code = "INSPECTION_NOT_FOUND"

    def __init__(self, message: str = "Inspection was not found.") -> None:
        super().__init__(message)


class InvalidAssignmentError(ConflictError):
    code = "INVALID_ASSIGNMENT"

    def __init__(self, message: str = "This complaint cannot be assigned right now.") -> None:
        super().__init__(message)


class InvalidCoordinatesError(AppError):
    code = "INVALID_COORDINATES"
    status_code = 422

    def __init__(self, message: str = "The supplied coordinates are invalid.") -> None:
        super().__init__(message)


class DistrictNotResolvableError(AppError):
    code = "DISTRICT_NOT_RESOLVABLE"
    status_code = 422

    def __init__(self, message: str = "Could not determine a district for the supplied location.") -> None:
        super().__init__(message)


class GeminiRateLimitedError(AppError):
    """Raised when the Gemini API rejects a request for exceeding its rate
    limit. Retryable - see app.agents.complaint_triage.agent for the
    retry policy."""

    code = "GEMINI_RATE_LIMITED"
    status_code = 429

    def __init__(self, message: str = "The AI service is receiving too many requests. Please try again shortly.") -> None:
        super().__init__(message)


class GeminiUnavailableError(AppError):
    """Raised for Gemini server errors, timeouts, or other transport-level
    failures. Retryable."""

    code = "GEMINI_UNAVAILABLE"
    status_code = 503

    def __init__(self, message: str = "The AI service is temporarily unavailable. Please try again shortly.") -> None:
        super().__init__(message)


class GeminiRequestError(AppError):
    """Raised for non-retryable Gemini request failures (e.g. an invalid
    request rejected by the API for reasons other than rate limiting)."""

    code = "GEMINI_REQUEST_FAILED"
    status_code = 502

    def __init__(self, message: str = "The AI service could not process this request.") -> None:
        super().__init__(message)


class InvalidAiResponseError(AppError):
    code = "INVALID_AI_RESPONSE"
    status_code = 502

    def __init__(self, message: str = "The AI service returned a response that could not be validated.") -> None:
        super().__init__(message)


class TriageNotFoundError(NotFoundError):
    code = "TRIAGE_NOT_FOUND"

    def __init__(self, message: str = "No AI triage analysis exists for this complaint yet.") -> None:
        super().__init__(message)


class EvidenceAnalysisNotFoundError(NotFoundError):
    code = "EVIDENCE_ANALYSIS_NOT_FOUND"

    def __init__(self, message: str = "No AI evidence analysis exists for this evidence item yet.") -> None:
        super().__init__(message)


class RagDocumentNotFoundError(NotFoundError):
    code = "RAG_DOCUMENT_NOT_FOUND"

    def __init__(self, message: str = "Knowledge base document was not found.") -> None:
        super().__init__(message)


class RagDocumentDuplicateError(ConflictError):
    code = "RAG_DOCUMENT_DUPLICATE"

    def __init__(self, message: str = "A document with identical content has already been uploaded.") -> None:
        super().__init__(message)


class RagIngestionError(AppError):
    code = "RAG_INGESTION_FAILED"
    status_code = 422

    def __init__(self, message: str = "The document could not be parsed or ingested.") -> None:
        super().__init__(message)


class AssistantConversationNotFoundError(NotFoundError):
    code = "ASSISTANT_CONVERSATION_NOT_FOUND"

    def __init__(self, message: str = "Assistant conversation was not found.") -> None:
        super().__init__(message)


class InvestigationNotFoundError(NotFoundError):
    code = "INVESTIGATION_NOT_FOUND"

    def __init__(self, message: str = "No AI investigation brief exists for this complaint yet.") -> None:
        super().__init__(message)


class NotificationNotFoundError(NotFoundError):
    code = "NOTIFICATION_NOT_FOUND"

    def __init__(self, message: str = "Notification was not found.") -> None:
        super().__init__(message)


class RateLimitExceededError(AppError):
    code = "RATE_LIMIT_EXCEEDED"
    status_code = 429

    def __init__(self, message: str = "Too many requests. Please try again later.") -> None:
        super().__init__(message)
