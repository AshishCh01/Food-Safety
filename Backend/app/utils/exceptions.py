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
