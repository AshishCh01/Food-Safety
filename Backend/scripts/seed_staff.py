"""Seed one district officer and one inspector per Maharashtra district.

Intended for development/testing only. Every seeded account shares the
same default password (override with SEED_STAFF_PASSWORD) - rotate or
disable these accounts before any shared/production deployment.

Usage (from Backend/):
    venv/Scripts/python.exe -m scripts.seed_staff
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.repositories import district_repository
from app.schemas.staff import StaffCreateRequest
from app.services import staff_service
from app.utils.enums import UserRole
from app.utils.exceptions import AppError

DEFAULT_PASSWORD = os.environ.get("SEED_STAFF_PASSWORD", "DevPass123!")
EMAIL_DOMAIN = "mhfoodsafety.dev"


def seed_for_district(db, district) -> None:
    code = district.code.lower()

    officer_request = StaffCreateRequest(
        email=f"officer.{code}@{EMAIL_DOMAIN}",
        password=DEFAULT_PASSWORD,
        full_name=f"{district.name} District Officer",
        role=UserRole.DISTRICT_OFFICER,
        district_id=district.id,
        employee_code=f"DO-{district.code}",
        designation="District Officer",
    )
    try:
        staff_service.create_staff(db, officer_request)
        print(f"created district officer for {district.code}")
    except AppError as exc:
        print(f"district officer for {district.code} skipped ({exc.message})")

    inspector_request = StaffCreateRequest(
        email=f"inspector1.{code}@{EMAIL_DOMAIN}",
        password=DEFAULT_PASSWORD,
        full_name=f"{district.name} Inspector 1",
        role=UserRole.INSPECTOR,
        district_id=district.id,
        employee_code=f"INS-{district.code}-01",
        designation="Food Safety Inspector",
    )
    try:
        staff_service.create_staff(db, inspector_request)
        print(f"created inspector for {district.code}")
    except AppError as exc:
        print(f"inspector for {district.code} skipped ({exc.message})")


def main() -> None:
    db = SessionLocal()
    try:
        districts = district_repository.list_all(db)
        if not districts:
            print("No districts found. Run scripts/seed_districts.py first.")
            return

        for district in districts:
            seed_for_district(db, district)

        print(f"\nSeed complete. Default password for seeded staff accounts: {DEFAULT_PASSWORD}")
        print("This is a development/testing default only - do not use in production.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
