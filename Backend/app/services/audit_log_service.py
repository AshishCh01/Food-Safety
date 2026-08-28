import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.repositories import audit_log_repository
from app.schemas.audit_log import AuditLogRead


def list_logs(
    db: Session,
    *,
    actor_user_id: uuid.UUID | None = None,
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[AuditLog], int]:
    return audit_log_repository.list_logs(
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


def to_audit_log_read(entry: AuditLog) -> AuditLogRead:
    return AuditLogRead(
        id=entry.id,
        actor_user_id=entry.actor_user_id,
        actor_name=entry.actor.full_name,
        action=entry.action,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        details=entry.details,
        created_at=entry.created_at,
    )
