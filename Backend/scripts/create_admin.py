"""Create (or reuse) an admin account from environment variables.

Public self-registration must never be able to create an admin account, so
admin provisioning is a deliberate, out-of-band script instead of an API
endpoint.

Usage (from Backend/):
    ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=... ADMIN_FULL_NAME="..." \
        venv/Scripts/python.exe -m scripts.create_admin
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.repositories import user_repository
from app.utils.enums import UserRole


def main() -> None:
    email = os.environ.get("ADMIN_EMAIL")
    password = os.environ.get("ADMIN_PASSWORD")
    full_name = os.environ.get("ADMIN_FULL_NAME", "Platform Administrator")

    if not email or not password:
        raise SystemExit(
            "Set ADMIN_EMAIL and ADMIN_PASSWORD environment variables before running this script."
        )
    if len(password) < 8:
        raise SystemExit("ADMIN_PASSWORD must be at least 8 characters long.")

    db = SessionLocal()
    try:
        existing = user_repository.get_by_email(db, email)
        if existing is not None:
            print(f"user {email} already exists (role={existing.role.value}); no changes made.")
            return

        user_repository.create(
            db,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            phone=None,
            role=UserRole.ADMIN,
        )
        print(f"created admin account: {email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
