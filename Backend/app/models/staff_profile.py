import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base
from app.utils.enums import UserRole


class StaffProfile(Base):
    """Staff-specific attributes for inspectors and district officers.

    A partial unique index enforces at most one active district officer per
    district at the database level, backstopping the same rule enforced in
    the service layer.
    """

    __tablename__ = "staff_profiles"
    __table_args__ = (
        Index(
            "uq_one_active_officer_per_district",
            "district_id",
            unique=True,
            postgresql_where=text("role = 'district_officer' AND is_active = true"),
            sqlite_where=text("role = 'district_officer' AND is_active = 1"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    district_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("districts.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role", values_callable=lambda e: [i.value for i in e]),
        nullable=False,
    )
    employee_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="staff_profile")
    district: Mapped["District"] = relationship(back_populates="staff_profiles")
