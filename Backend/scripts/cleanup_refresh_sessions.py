"""Deletes refresh_sessions rows that are permanently unusable (expired or
revoked) and old enough to fall outside their retention window - see
docs/SECURITY_AND_RBAC.md section 20 for the full retention policy.

Safe to run repeatedly and safe to run against a live database:
- it only ever deletes rows that could never again be presented
  successfully (a live/current session is never touched - see
  app/repositories/refresh_session_repository.py's eligibility query);
- it deletes in small batches, committing between them, so it never holds
  one long-running transaction/lock even on a large backlog;
- --dry-run reports what would be deleted without deleting anything.

There is no in-process scheduler here and this project does not use
Redis/Celery for background work - running this script on a schedule *is*
the maintenance mechanism. Wire it up with cron, Windows Task Scheduler, or
a scheduled CI/CD job; a suggested frequency is daily.

Usage (from Backend/):
    venv/Scripts/python.exe -m scripts.cleanup_refresh_sessions [--dry-run] [--batch-size N]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.services import auth_service


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report how many rows are eligible for deletion without deleting them.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Rows deleted per transaction (default: %(default)s).",
    )
    args = parser.parse_args()

    if args.batch_size < 1:
        raise SystemExit("--batch-size must be at least 1.")

    db = SessionLocal()
    try:
        if args.dry_run:
            count = auth_service.count_sessions_eligible_for_cleanup(db)
            print(f"[dry run] {count} refresh_sessions row(s) are eligible for deletion; none were deleted.")
            return

        deleted = auth_service.cleanup_expired_and_revoked_sessions(db, batch_size=args.batch_size)
        print(f"deleted {deleted} refresh_sessions row(s).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
