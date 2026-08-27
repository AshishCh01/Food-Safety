import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.core.database import Base


class District(Base):
    __tablename__ = "districts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    division_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("divisions.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Approximate district-headquarters coordinates, not surveyed boundary
    # polygons. Used for nearest-district resolution from a citizen's
    # reported location (see app/services/district_service.py). A future
    # phase can replace this with true point-in-polygon lookup once real
    # district boundary geometry is available.
    centroid_latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    centroid_longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    division: Mapped["Division"] = relationship(back_populates="districts")
    staff_profiles: Mapped[list["StaffProfile"]] = relationship(back_populates="district")
