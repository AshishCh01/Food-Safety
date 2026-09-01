"""Verifies that the Supabase Storage buckets holding complaint/inspection
evidence and RAG knowledge-base documents are actually configured private.

Why this exists: every evidence/RAG-document access path in this codebase
(evidence_service.py, rag_document_service.py) enforces ownership/district/
role checks in the backend API before ever generating a signed URL - but
that authorization only matters if the underlying Supabase Storage bucket
itself is private. If a bucket is ever toggled public (a single checkbox in
the Supabase dashboard, easy to fumble on initial setup or a later config
change), every uploaded file becomes fetchable directly at
`{supabase_url}/storage/v1/object/public/{bucket}/{path}` with no
authorization involved at all (docs/SECURITY_AND_RBAC.md section 8,
docs/PROJECT_AUDIT_REPORT.md finding 1.5). Nothing in the request-handling
code path can detect that on its own, since it never has a reason to call
the bucket-config endpoint during normal operation.

This is a standalone script (not an API endpoint or startup check) so it
can run on a schedule independently of the app's own uptime, following this
project's existing scripts/ convention (cleanup_refresh_sessions.py,
create_admin.py, seed_districts.py) rather than adding request-path latency
or a hard app-boot dependency on an external network call succeeding.

Usage (from Backend/):
    venv/Scripts/python.exe -m scripts.check_storage_bucket_privacy

Exit codes:
    0 - every configured bucket was confirmed private.
    1 - at least one bucket was confirmed PUBLIC, or a check could not be
        completed (network error, unexpected response) - both are treated
        as failures so a scheduled job's non-zero exit reliably signals
        "this needs a human," rather than a broken check silently passing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import get_settings
from app.services import storage_service


def main() -> None:
    settings = get_settings()
    buckets = {settings.supabase_storage_bucket, settings.rag_storage_bucket}

    if not settings.supabase_url:
        print("SUPABASE_URL is not configured - nothing to check.")
        raise SystemExit(0)

    failures: list[str] = []
    for bucket in sorted(buckets):
        is_public = storage_service.get_bucket_public(bucket)
        if is_public is None:
            print(f"[UNKNOWN] '{bucket}': could not verify (Supabase Storage unreachable or an unexpected "
                  f"response) - manually confirm this bucket is private.")
            failures.append(bucket)
        elif is_public:
            print(f"[PUBLIC!] '{bucket}': this bucket is configured PUBLIC. Every uploaded file is fetchable "
                  f"with no authorization. Fix this in the Supabase dashboard (Storage -> bucket -> make "
                  f"private) immediately.")
            failures.append(bucket)
        else:
            print(f"[private] '{bucket}': confirmed private.")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
