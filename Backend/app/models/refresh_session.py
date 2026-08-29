import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base


class RefreshSession(Base):
    """Server-side record of one issued refresh token, enabling revocation
    (docs/SECURITY_AND_RBAC.md section 18 - stateless refresh tokens could
    not previously be revoked). Only a SHA-256 hash of the opaque refresh
    token is stored - never the token itself - see
    app/core/security.py:hash_opaque_token. A database read alone cannot be
    used to authenticate as the user.

    Refresh tokens rotate on every use (app/services/auth_service.py): each
    rotation revokes this row (`revoked_reason="rotated"`) and creates a new
    one, linked via `replaced_by_id`. `family_id` stays constant across every
    rotation descending from one login, so the entire lineage can be revoked
    at once - on logout, account deactivation, or when an already-rotated
    token is presented again (reuse detection).
    """

    __tablename__ = "refresh_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    family_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(String(50), nullable=True)
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("refresh_sessions.id", ondelete="SET NULL"), nullable=True
    )

    user: Mapped["User"] = relationship()
