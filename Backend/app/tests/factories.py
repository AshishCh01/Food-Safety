import uuid

from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password
from app.models.assignment import Assignment
from app.models.assistant_conversation import AssistantConversation
from app.models.business import Business
from app.models.complaint import Complaint
from app.models.complaint_category import ComplaintCategory
from app.models.district import District
from app.models.division import Division
from app.models.evidence import Evidence
from app.models.inspection import Inspection
from app.models.inspection_finding import InspectionFinding
from app.models.rag_document import RagDocument
from app.models.rag_document_chunk import RagDocumentChunk
from app.models.staff_profile import StaffProfile
from app.models.user import User
from app.utils.enums import (
    AssignmentStatus,
    ComplaintPriority,
    ComplaintStatus,
    FindingSeverity,
    InspectionStatus,
    RagDocumentStatus,
    RagDocumentType,
    UserRole,
)

DEFAULT_PASSWORD = "Password123!"


def create_division(db: Session, *, name: str = "Pune", code: str = "PUN") -> Division:
    division = Division(name=name, code=code)
    db.add(division)
    db.commit()
    db.refresh(division)
    return division


def create_district(
    db: Session,
    division: Division,
    *,
    name: str = "Pune",
    code: str = "PUN",
    centroid_latitude: float | None = 18.5204,
    centroid_longitude: float | None = 73.8567,
) -> District:
    district = District(
        name=name,
        code=code,
        division_id=division.id,
        centroid_latitude=centroid_latitude,
        centroid_longitude=centroid_longitude,
    )
    db.add(district)
    db.commit()
    db.refresh(district)
    return district


def create_user(
    db: Session,
    *,
    email: str,
    password: str = DEFAULT_PASSWORD,
    full_name: str = "Test User",
    role: UserRole = UserRole.CITIZEN,
    is_active: bool = True,
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_staff(
    db: Session,
    district: District,
    *,
    role: UserRole,
    email: str,
    employee_code: str,
    password: str = DEFAULT_PASSWORD,
    is_active: bool = True,
) -> tuple[User, StaffProfile]:
    user = create_user(db, email=email, password=password, full_name=f"{role.value} {employee_code}", role=role, is_active=is_active)
    profile = StaffProfile(
        user_id=user.id,
        district_id=district.id,
        role=role,
        employee_code=employee_code,
        designation=role.value,
        is_active=is_active,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return user, profile


def auth_headers(user: User, district_id=None) -> dict:
    token = create_access_token(user.id, user.role.value, district_id, user.is_active)
    return {"Authorization": f"Bearer {token}"}


def create_complaint_category(
    db: Session, *, key: str = "expired_food", name: str = "Expired Food"
) -> ComplaintCategory:
    category = ComplaintCategory(key=key, name=name, description=f"{name} issues")
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def create_business(
    db: Session,
    district: District,
    *,
    business_name: str = "Test Restaurant",
    address: str = "123 Main Street",
    latitude: float | None = None,
    longitude: float | None = None,
) -> Business:
    business = Business(
        business_name=business_name,
        address=address,
        district_id=district.id,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    return business


def create_complaint(
    db: Session,
    citizen: User,
    district: District,
    category: ComplaintCategory,
    *,
    business: Business | None = None,
    title: str = "Expired dairy products on sale",
    description: str = "Found expired milk packets still being sold at the counter.",
    status: ComplaintStatus = ComplaintStatus.SUBMITTED,
    priority: ComplaintPriority = ComplaintPriority.MEDIUM,
    complaint_number: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> Complaint:
    complaint = Complaint(
        complaint_number=complaint_number or f"MH-{district.code}-2026-{uuid.uuid4().int % 1_000_000:06d}",
        submitted_by_user_id=citizen.id,
        business_id=business.id if business else None,
        district_id=district.id,
        category_id=category.id,
        title=title,
        description=description,
        status=status,
        priority=priority,
        latitude=latitude,
        longitude=longitude,
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


def create_assignment(
    db: Session,
    complaint: Complaint,
    inspector_staff: StaffProfile,
    officer_staff: StaffProfile,
    *,
    status: AssignmentStatus = AssignmentStatus.ASSIGNED,
) -> Assignment:
    assignment = Assignment(
        complaint_id=complaint.id,
        assigned_to_staff_id=inspector_staff.id,
        assigned_by_staff_id=officer_staff.id,
        status=status,
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def create_evidence(
    db: Session,
    complaint: Complaint,
    uploaded_by: User,
    *,
    inspection_id=None,
    file_name: str = "photo.jpg",
    file_type: str = "image/jpeg",
    file_size: int = 1024,
    storage_bucket: str = "complaint-evidence",
    storage_path: str | None = None,
    checksum: str = "a" * 64,
) -> Evidence:
    evidence = Evidence(
        complaint_id=complaint.id,
        inspection_id=inspection_id,
        uploaded_by_user_id=uploaded_by.id,
        storage_bucket=storage_bucket,
        storage_path=storage_path or f"evidence/{complaint.id}/{uuid.uuid4()}_{file_name}",
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
        checksum=checksum,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def create_rag_document(
    db: Session,
    uploaded_by: User,
    *,
    title: str = "FSSAI Food Safety Regulations 2011",
    source_organization: str = "FSSAI",
    document_type: RagDocumentType = RagDocumentType.REGULATION,
    file_type: str = "application/pdf",
    business_type: str | None = None,
    status: RagDocumentStatus = RagDocumentStatus.PENDING,
    is_active: bool = True,
    checksum: str | None = None,
) -> RagDocument:
    document = RagDocument(
        title=title,
        source_organization=source_organization,
        document_type=document_type,
        storage_path=f"rag/{uuid.uuid4()}",
        original_filename="document.pdf",
        file_type=file_type,
        checksum=checksum or uuid.uuid4().hex,
        business_type=business_type,
        jurisdiction="India",
        status=status,
        is_active=is_active,
        uploaded_by_user_id=uploaded_by.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def create_rag_chunk(
    db: Session,
    document: RagDocument,
    *,
    chunk_index: int = 0,
    content: str = "Sample regulation text.",
    page_number: int | None = None,
    section_title: str | None = None,
    embedding: list[float] | None = None,
    embedding_model: str = "gemini-embedding-2-preview",
) -> RagDocumentChunk:
    chunk = RagDocumentChunk(
        document_id=document.id,
        chunk_index=chunk_index,
        content=content,
        page_number=page_number,
        section_title=section_title,
        chunk_metadata={
            "document_type": document.document_type.value,
            "business_type": document.business_type,
            "jurisdiction": document.jurisdiction,
            "version": document.version,
        },
        embedding=embedding if embedding is not None else [0.1, 0.2, 0.3],
        embedding_model=embedding_model,
    )
    db.add(chunk)
    db.commit()
    db.refresh(chunk)
    return chunk


def create_assistant_conversation(
    db: Session,
    inspector_staff: StaffProfile,
    *,
    inspection: Inspection | None = None,
    complaint: Complaint | None = None,
) -> AssistantConversation:
    conversation = AssistantConversation(
        inspector_staff_id=inspector_staff.id,
        inspection_id=inspection.id if inspection else None,
        complaint_id=complaint.id if complaint else (inspection.complaint_id if inspection else None),
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def create_inspection(
    db: Session,
    complaint: Complaint,
    inspector_staff: StaffProfile,
    *,
    status: InspectionStatus = InspectionStatus.SCHEDULED,
) -> Inspection:
    inspection = Inspection(
        complaint_id=complaint.id,
        inspector_id=inspector_staff.id,
        inspection_status=status,
    )
    db.add(inspection)
    db.commit()
    db.refresh(inspection)
    return inspection


def create_inspection_finding(
    db: Session,
    inspection: Inspection,
    *,
    check_code: str = "HYG-01",
    finding: str = "Storage area inspected.",
    severity: FindingSeverity = FindingSeverity.LOW,
    compliant: bool = True,
) -> InspectionFinding:
    record = InspectionFinding(
        inspection_id=inspection.id,
        check_code=check_code,
        finding=finding,
        severity=severity,
        compliant=compliant,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
