import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.agents.evidence_analysis import agent as evidence_analysis_agent
from app.core.database import get_db
from app.core.dependencies import get_current_staff_profile, require_inspector
from app.models.staff_profile import StaffProfile
from app.schemas.agent import (
    AssistantConversationCreateRequest,
    AssistantConversationRead,
    AssistantMessageCreateRequest,
    AssistantMessageRead,
    EvidenceAnalysisRead,
    PaginatedAssistantConversations,
)
from app.schemas.assignment import AssignmentRead, AssignmentSummary, PaginatedAssignments
from app.schemas.evidence import EvidenceRead
from app.schemas.inspection import (
    InspectionCompleteRequest,
    InspectionCreateRequest,
    InspectionFindingCreateRequest,
    InspectionFindingRead,
    InspectionRead,
    InspectionUpdateRequest,
    PaginatedInspections,
)
from app.services import assignment_service, assistant_service, evidence_service, inspection_service
from app.utils.enums import AssignmentStatus, InspectionStatus
from app.utils.exceptions import EvidenceAnalysisNotFoundError

router = APIRouter(prefix="/inspector", tags=["inspector"], dependencies=[Depends(require_inspector)])


@router.get("/dashboard")
def dashboard(
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> dict:
    _, assigned_total = assignment_service.list_for_inspector(
        db, staff.id, status=AssignmentStatus.ASSIGNED, page=1, page_size=1
    )
    _, in_progress_total = assignment_service.list_for_inspector(
        db, staff.id, status=AssignmentStatus.IN_PROGRESS, page=1, page_size=1
    )
    _, completed_total = inspection_service.list_for_inspector(
        db, staff.id, status=InspectionStatus.COMPLETED, page=1, page_size=1
    )
    return {
        "district_id": staff.district_id,
        "district_name": staff.district.name,
        "district_code": staff.district.code,
        "inspector_name": staff.user.full_name,
        "employee_code": staff.employee_code,
        "assigned_count": assigned_total,
        "in_progress_count": in_progress_total,
        "completed_count": completed_total,
    }


@router.get("/assignments", response_model=PaginatedAssignments)
def list_assignments(
    status_filter: AssignmentStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> PaginatedAssignments:
    # Scope always comes from the authenticated inspector's own staff
    # profile - inspectors never browse a district-wide complaint list.
    items, total = assignment_service.list_for_inspector(
        db, staff.id, status=status_filter, page=page, page_size=page_size
    )
    return PaginatedAssignments(
        items=[assignment_service.to_assignment_summary(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(
    assignment_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> AssignmentRead:
    assignment = assignment_service.get_assignment_for_inspector(db, staff.id, assignment_id)
    inspection = inspection_service.get_inspection_for_complaint_if_owned(db, staff.id, assignment.complaint_id)
    inspection_read = inspection_service.to_inspection_read(inspection) if inspection else None
    return assignment_service.to_assignment_read(assignment, inspection_read=inspection_read)


@router.post("/inspections", response_model=InspectionRead, status_code=status.HTTP_201_CREATED)
def create_inspection(
    payload: InspectionCreateRequest,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> InspectionRead:
    inspection = inspection_service.create_inspection(db, staff, payload)
    return inspection_service.to_inspection_read(inspection)


@router.patch("/inspections/{inspection_id}", response_model=InspectionRead)
def update_inspection(
    inspection_id: uuid.UUID,
    payload: InspectionUpdateRequest,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> InspectionRead:
    inspection = inspection_service.get_inspection_for_inspector(db, staff.id, inspection_id)
    inspection = inspection_service.update_inspection(db, staff, inspection, payload)
    return inspection_service.to_inspection_read(inspection)


@router.post(
    "/inspections/{inspection_id}/findings",
    response_model=InspectionFindingRead,
    status_code=status.HTTP_201_CREATED,
)
def add_finding(
    inspection_id: uuid.UUID,
    payload: InspectionFindingCreateRequest,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> InspectionFindingRead:
    inspection = inspection_service.get_inspection_for_inspector(db, staff.id, inspection_id)
    finding = inspection_service.add_finding(db, staff, inspection, payload)
    return inspection_service.to_finding_read(finding)


@router.post(
    "/inspections/{inspection_id}/evidence", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED
)
async def upload_inspection_evidence(
    inspection_id: uuid.UUID,
    file: UploadFile = File(...),
    captured_at: datetime | None = Form(default=None),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> EvidenceRead:
    inspection = inspection_service.get_inspection_for_inspector(db, staff.id, inspection_id)
    file_bytes = await file.read()
    evidence = evidence_service.upload_evidence(
        db,
        complaint=inspection.complaint,
        uploaded_by_user_id=staff.user_id,
        file_bytes=file_bytes,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        inspection_id=inspection.id,
        captured_at=captured_at,
        latitude=latitude,
        longitude=longitude,
    )
    return evidence_service.to_evidence_read(evidence)


@router.get("/inspections/{inspection_id}/evidence", response_model=list[EvidenceRead])
def list_inspection_evidence(
    inspection_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> list[EvidenceRead]:
    inspection = inspection_service.get_inspection_for_inspector(db, staff.id, inspection_id)
    return evidence_service.list_inspection_evidence_with_urls(db, inspection.id)


@router.post(
    "/inspections/{inspection_id}/evidence/{evidence_id}/analysis", response_model=EvidenceAnalysisRead
)
def run_inspection_evidence_analysis(
    inspection_id: uuid.UUID,
    evidence_id: uuid.UUID,
    force: bool = Query(default=False),
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> EvidenceAnalysisRead:
    """Explicitly triggers the AI Evidence Analysis Agent for an evidence item
    on the inspector's own inspection. Advisory only - see
    docs/AI_AGENTS_ARCHITECTURE.md section 5. Returns a cached result if one
    already exists unless `force=true` is passed."""
    inspection = inspection_service.get_inspection_for_inspector(db, staff.id, inspection_id)
    evidence = evidence_service.get_evidence_for_inspector(db, inspection, evidence_id)
    analysis = evidence_analysis_agent.run_analysis(db, staff, evidence, force=force)
    return evidence_analysis_agent.to_analysis_read(analysis)


@router.get(
    "/inspections/{inspection_id}/evidence/{evidence_id}/analysis", response_model=EvidenceAnalysisRead
)
def get_inspection_evidence_analysis(
    inspection_id: uuid.UUID,
    evidence_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> EvidenceAnalysisRead:
    """Reads the most recent AI evidence analysis result, if any, without
    calling Gemini again."""
    inspection = inspection_service.get_inspection_for_inspector(db, staff.id, inspection_id)
    evidence = evidence_service.get_evidence_for_inspector(db, inspection, evidence_id)
    analysis = evidence_analysis_agent.get_latest_analysis(db, evidence.id)
    if analysis is None:
        raise EvidenceAnalysisNotFoundError()
    return evidence_analysis_agent.to_analysis_read(analysis)


@router.post("/inspections/{inspection_id}/complete", response_model=InspectionRead)
def complete_inspection(
    inspection_id: uuid.UUID,
    payload: InspectionCompleteRequest,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> InspectionRead:
    inspection = inspection_service.get_inspection_for_inspector(db, staff.id, inspection_id)
    inspection = inspection_service.complete_inspection(db, staff, inspection, payload)
    return inspection_service.to_inspection_read(inspection)


@router.get("/history", response_model=PaginatedInspections)
def inspection_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> PaginatedInspections:
    items, total = inspection_service.list_for_inspector(
        db, staff.id, status=InspectionStatus.COMPLETED, page=page, page_size=page_size
    )
    return PaginatedInspections(
        items=[inspection_service.to_inspection_summary(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/assistant/conversations", response_model=AssistantConversationRead, status_code=status.HTTP_201_CREATED
)
def create_assistant_conversation(
    payload: AssistantConversationCreateRequest,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> AssistantConversationRead:
    """Starts an Inspector Assistant conversation (docs/AI_AGENTS_ARCHITECTURE.md
    section 7). When `inspection_id` is given, ownership is verified
    server-side (via inspection_service.get_inspection_for_inspector) before
    the conversation is created - never trusted from the request alone."""
    conversation = assistant_service.create_conversation(db, staff, payload.inspection_id)
    return assistant_service.to_conversation_read(conversation)


@router.get("/assistant/conversations", response_model=PaginatedAssistantConversations)
def list_assistant_conversations(
    inspection_id: uuid.UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> PaginatedAssistantConversations:
    items, total = assistant_service.list_conversations_for_inspector(
        db, staff, inspection_id=inspection_id, page=page, page_size=page_size
    )
    return PaginatedAssistantConversations(
        items=[assistant_service.to_conversation_summary(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/assistant/conversations/{conversation_id}", response_model=AssistantConversationRead)
def get_assistant_conversation(
    conversation_id: uuid.UUID,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> AssistantConversationRead:
    conversation = assistant_service.get_conversation_for_inspector(db, staff, conversation_id)
    return assistant_service.to_conversation_read(conversation)


@router.post("/assistant/conversations/{conversation_id}/messages", response_model=AssistantMessageRead)
def send_assistant_message(
    conversation_id: uuid.UUID,
    payload: AssistantMessageCreateRequest,
    staff: StaffProfile = Depends(get_current_staff_profile),
    db: Session = Depends(get_db),
) -> AssistantMessageRead:
    """Asks the Inspector Assistant a question within `conversation_id`.
    Advisory only - see docs/AI_AGENTS_ARCHITECTURE.md section 7. A Gemini or
    retrieval failure is returned as a normal 200 response containing a
    failed assistant message (error_code/error_message set) rather than a
    fabricated answer; a malformed AI response instead raises (502)."""
    conversation = assistant_service.get_conversation_for_inspector(db, staff, conversation_id)
    message = assistant_service.ask(db, staff, conversation, payload.question)
    return assistant_service.to_message_read(message)
