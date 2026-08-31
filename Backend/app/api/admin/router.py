import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.repositories import (
    audit_log_repository,
    district_repository,
    division_repository,
    rag_document_repository,
    user_repository,
)
from app.schemas.analytics import StatewideAnalytics
from app.schemas.audit_log import PaginatedAuditLogs
from app.schemas.district import DistrictRead
from app.schemas.rag import PaginatedRagDocuments, RagDocumentCreate, RagDocumentRead
from app.schemas.staff import StaffCreateRequest, StaffRead
from app.schemas.user import PaginatedUsers, UserStatusUpdate, UserSummary
from app.services import (
    analytics_service,
    audit_log_service,
    auth_service,
    district_service,
    rag_document_service,
    staff_service,
)
from app.utils.enums import RagDocumentStatus, RagDocumentType, UserRole
from app.utils.exceptions import NotFoundError
from app.utils.uploads import read_upload_bounded

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)) -> dict:
    _, citizen_total = user_repository.list_users(db, role=UserRole.CITIZEN, page=1, page_size=1)
    _, officer_total = user_repository.list_users(db, role=UserRole.DISTRICT_OFFICER, page=1, page_size=1)
    _, inspector_total = user_repository.list_users(db, role=UserRole.INSPECTOR, page=1, page_size=1)
    _, admin_total = user_repository.list_users(db, role=UserRole.ADMIN, page=1, page_size=1)

    return {
        "division_count": len(division_repository.list_all(db)),
        "district_count": len(district_repository.list_all(db)),
        "citizen_count": citizen_total,
        "district_officer_count": officer_total,
        "inspector_count": inspector_total,
        "admin_count": admin_total,
    }


@router.get("/districts", response_model=list[DistrictRead])
def list_districts(
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[DistrictRead]:
    districts = district_service.list_districts(db, is_active=is_active)
    return [district_service.to_district_read(district) for district in districts]


@router.post("/staff", response_model=StaffRead, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreateRequest,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> StaffRead:
    profile = staff_service.create_staff(db, payload, actor_user_id=admin_user.id)
    return staff_service.to_staff_read(profile)


@router.get("/users", response_model=PaginatedUsers)
def list_users(
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedUsers:
    items, total = user_repository.list_users(db, role=role, is_active=is_active, page=page, page_size=page_size)
    return PaginatedUsers(
        items=[UserSummary.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{user_id}/status", response_model=UserSummary)
def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserSummary:
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("User was not found.")
    user = user_repository.set_active_status(db, user, payload.is_active)

    revoked_sessions = 0
    if not payload.is_active:
        # Deactivation must not leave existing refresh tokens usable until
        # they naturally expire (docs/SECURITY_AND_RBAC.md section 18).
        revoked_sessions = auth_service.revoke_all_sessions_for_user(db, user.id)

    audit_log_repository.record(
        db,
        actor_user_id=admin_user.id,
        action="user_status_updated",
        entity_type="user",
        entity_id=user.id,
        details={"is_active": payload.is_active, "revoked_sessions": revoked_sessions},
    )
    db.commit()
    return UserSummary.model_validate(user)


@router.get("/analytics", response_model=StatewideAnalytics)
def get_admin_analytics(
    trend_days: int = Query(default=30, ge=1, le=180),
    db: Session = Depends(get_db),
) -> StatewideAnalytics:
    """Statewide operational KPIs with a per-district breakdown
    (docs/PROJECT_SPEC.md section 21)."""
    return analytics_service.get_statewide_analytics(db, trend_days=trend_days)


@router.get("/audit-logs", response_model=PaginatedAuditLogs)
def list_audit_logs(
    actor_user_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: uuid.UUID | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedAuditLogs:
    """Read-only, filterable view over the append-only audit trail
    (docs/SECURITY_AND_RBAC.md section 12). There is no corresponding write
    endpoint - audit records are only ever created as a side effect of the
    action they describe."""
    items, total = audit_log_service.list_logs(
        db,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )
    return PaginatedAuditLogs(
        items=[audit_log_service.to_audit_log_read(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/rag/documents", response_model=RagDocumentRead, status_code=status.HTTP_201_CREATED)
async def upload_rag_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: RagDocumentType = Form(...),
    source_organization: str | None = Form(default=None),
    version: str | None = Form(default=None),
    effective_date: str | None = Form(default=None),
    source_url: str | None = Form(default=None),
    business_type: str | None = Form(default=None),
    jurisdiction: str = Form(default="India"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RagDocumentRead:
    """Uploads an official knowledge-base source document (see
    docs/RAG_ARCHITECTURE.md). Only stores and records the file - a separate
    POST to /rag/documents/{id}/ingest triggers parsing/chunking/embedding."""
    payload = RagDocumentCreate(
        title=title,
        source_organization=source_organization,
        document_type=document_type,
        version=version,
        effective_date=effective_date or None,
        source_url=source_url,
        business_type=business_type,
        jurisdiction=jurisdiction,
    )
    max_bytes = get_settings().rag_max_upload_size_mb * 1024 * 1024
    file_bytes = await read_upload_bounded(file, max_bytes)
    document = rag_document_service.upload_document(
        db,
        current_user,
        payload,
        file_bytes=file_bytes,
        filename=file.filename or "document",
        content_type=file.content_type or "application/octet-stream",
    )
    return rag_document_service.to_document_read(document)


@router.get("/rag/documents", response_model=PaginatedRagDocuments)
def list_rag_documents(
    status_filter: RagDocumentStatus | None = Query(default=None, alias="status"),
    document_type: RagDocumentType | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedRagDocuments:
    items, total = rag_document_repository.list_documents(
        db, status=status_filter, document_type=document_type, is_active=is_active, page=page, page_size=page_size
    )
    return PaginatedRagDocuments(
        items=[rag_document_service.to_document_read(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/rag/documents/{document_id}", response_model=RagDocumentRead)
def get_rag_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> RagDocumentRead:
    document = rag_document_service.get_document(db, document_id)
    return rag_document_service.to_document_read(document)


@router.post("/rag/documents/{document_id}/ingest", response_model=RagDocumentRead)
def ingest_rag_document(
    document_id: uuid.UUID,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RagDocumentRead:
    """Explicitly triggers document parsing/chunking/embedding (synchronous -
    matches the existing pattern of Complaint Triage / Evidence Analysis
    running on an explicit POST). Safe to re-run; replaces any existing
    chunks for this document."""
    document = rag_document_service.get_document(db, document_id)
    document = rag_document_service.run_ingestion(db, document, actor_user_id=admin_user.id)
    return rag_document_service.to_document_read(document)


@router.post("/rag/documents/{document_id}/deactivate", response_model=RagDocumentRead)
def deactivate_rag_document(
    document_id: uuid.UUID,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RagDocumentRead:
    """Deactivates a knowledge-base source (docs/RAG_ARCHITECTURE.md section
    12) without deleting it - retrieval only ever considers active documents."""
    document = rag_document_service.get_document(db, document_id)
    document = rag_document_service.deactivate_document(db, document, actor_user_id=admin_user.id)
    return rag_document_service.to_document_read(document)


@router.delete("/rag/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rag_document(
    document_id: uuid.UUID,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    """Permanently removes a document that never successfully entered the
    knowledge base (`pending` or `failed`), so a bad upload/ingest attempt can
    be cleared and retried from scratch. An `ingested` document must be
    deactivated instead - see `deactivate_rag_document`."""
    document = rag_document_service.get_document(db, document_id)
    rag_document_service.delete_document(db, document, actor_user_id=admin_user.id)
