# Security and RBAC

## 1. Purpose

This document defines access control and security requirements for the Maharashtra Food Safety Complaint and Inspection Platform.

## 2. Roles

```text
Citizen
Inspector
District Officer
Admin
```

## 3. Role Permissions

### Citizen

Can:

- register/login
- create complaints
- upload complaint evidence
- view own complaints
- view own complaint timeline
- receive notifications

Cannot:

- access another user's complaint records
- access staff dashboards
- assign inspectors
- modify official findings
- access private regulatory/admin data unless exposed through an approved public workflow

### Inspector

Can:

- view assigned inspections
- view authorized complaint/evidence data
- create/update inspection records
- upload inspection evidence
- add findings
- use Inspector Assistant
- draft inspection reports

Cannot:

- access unrelated districts
- assign themselves arbitrary cases
- modify another inspector's cases without explicit authorization
- make admin account changes
- finalize regulatory enforcement decisions reserved for officers

### District Officer

Can:

- view complaints within their district
- review/verify/reject complaints
- assign inspectors in their district
- view district analytics
- review inspection reports
- use investigation/inspector assistance tools available to the role

Cannot:

- access another district's operational data
- manage statewide admin settings
- create arbitrary admin accounts

### Admin

Can:

- manage users and staff
- manage districts and business master data
- view statewide analytics
- manage approved RAG documents
- inspect audit logs
- configure system-level settings

Admin access should be tightly controlled and auditable.

## 4. District Isolation

District isolation is a mandatory server-side rule.

Every district-scoped staff identity has a `district_id`.

Example:

```text
Pune Officer
 -> district_id = PUNE
 -> permitted complaint scope = PUNE
```

A request such as:

```text
GET /officer/complaints?district_id=NAGPUR
```

must not allow a Pune officer to switch scope.

The backend must derive scope from the authenticated user.

## 5. Authorization Layers

Use defense in depth:

```text
Authentication
   -> role check
   -> district scope check
   -> object ownership/assignment check
   -> business rule check
   -> database action
```

## 6. Authentication Security

- Use strong password hashing if application passwords are used.
- Never store plaintext passwords.
- Use secure, expiring access tokens.
- Rotate refresh tokens where supported.
- Verify email/phone according to the chosen authentication design.
- Rate-limit login and password reset endpoints.
- Implement account disablement.

## 7. Staff Account Provisioning

Citizens may self-register.

Staff accounts should be provisioned through controlled admin or departmental onboarding workflows.

Never let a public registration parameter such as `role=admin` create an elevated account.

## 8. Evidence Security

Complaint photos and videos may contain sensitive information.

Requirements:

- authorize access before serving evidence
- use private storage buckets where appropriate
- use short-lived signed URLs when needed
- validate file type and size
- scan/validate uploads where operationally feasible
- prevent path traversal
- record uploader and timestamps

## 9. AI Security

AI agents must not bypass RBAC.

Bad design:

```text
Agent -> arbitrary SQL -> database
```

Good design:

```text
Agent
 -> controlled tool
 -> authorization-aware service
 -> repository
 -> database
```

Agents must not independently:

- promote their own permissions
- delete cases
- change staff roles
- issue enforcement actions
- expose data from other districts

## 10. Prompt Injection Defense

Treat user complaint text, uploaded documents, and retrieved text as untrusted content.

Do not let embedded instructions in evidence or retrieved documents override system/tool authorization.

Tools should verify permissions independently of model instructions.

## 11. API Security

- HTTPS in production.
- Strict CORS configuration.
- Request size limits.
- Input validation.
- Rate limiting for abuse-prone endpoints.
- Safe error handling.
- Security headers at the edge.
- Dependency vulnerability monitoring.

## 12. Audit Logging

Record security-sensitive events:

- login success/failure
- account activation/deactivation
- role changes
- district assignments
- case assignment changes
- status changes
- evidence access/deletion where required
- admin actions
- AI tools that perform operational mutations

## 13. Secret Management

Never commit:

- database passwords
- JWT secrets
- Supabase service-role secrets
- AI provider keys
- storage credentials

Use `.env` locally and managed secret storage in production.

## 14. Supabase Key Separation

Keep public client-side keys separate from privileged server credentials.

Privileged service-role credentials must never be shipped to the frontend.

## 15. Data Retention

Define retention rules for:

- complaints
- evidence
- inspection reports
- AI logs
- audit logs
- RAG documents

Retention must follow the actual department/legal requirements once those are provided by the project authority.

## 16. Security Testing

Minimum test categories:

- unauthorized endpoint access
- cross-district access attempts
- cross-user complaint access
- privilege escalation
- token/session misuse
- file upload abuse
- prompt injection attempts
- agent tool authorization
- SQL injection/input validation

## 17. Security Principle

The LLM, frontend, and client are all untrusted from an authorization perspective. The backend is the enforcement boundary.

## 18. Phase 12 Hardening Findings and Fixes

A security/performance audit of Phases 1-11 (auth, RBAC/district isolation,
file uploads, AI agent tools, performance, reliability - see
`docs/DEVELOPMENT_ROADMAP.md` Phase 12) confirmed the core authorization
architecture is sound: district/inspector/citizen scope is always derived
server-side from the authenticated identity (never a client-supplied
parameter), AI agent tools only ever take pre-scoped ORM objects, and no
raw/unparameterized SQL exists anywhere in the repository layer. The
following real, verified issues were found and fixed:

- **No rate limiting on auth/complaint-creation endpoints** (violated
  section 6/11's explicit requirement). Fixed with an in-memory, per-IP
  sliding-window limiter (`app/core/rate_limit.py`) applied to
  `/auth/login`, `/auth/register`, `/auth/refresh`, and `POST /complaints`.
  **Known limitation:** single-process/in-memory - a multi-worker or
  multi-instance production deployment needs a shared store (e.g. Redis)
  instead; not built here since the current deployment target is a single
  backend process (see `docs/DEVELOPMENT_ROADMAP.md` Phase 13).
- **Login timing side-channel**: a nonexistent email short-circuited before
  `verify_password` ran, making "unknown email" measurably faster than
  "known email, wrong password" (account enumeration via timing).
  `app/services/auth_service.py` now always runs a bcrypt comparison
  against a dummy hash when no user is found.
- **File upload validation trusted the client-supplied `Content-Type`
  header alone**, with no filename sanitization before the value was used
  to build a storage key/URL. `app/utils/validators.py` now sniffs file
  content against the declared type's magic bytes, cross-checks the
  filename's extension against the declared type, and sanitizes the
  filename (strips path separators/`..`/unsafe characters) before it is
  used in `evidence_service.py`/`rag_document_service.py`. Uploads are now
  also read in bounded chunks (`app/utils/uploads.py`) so an oversized
  request is rejected without buffering the whole body into memory first.
- **`assignments.complaint_id` had no database-level unique constraint**,
  so two concurrent assign-inspector requests could create two rows for one
  complaint and crash every later read of that assignment. See
  `docs/DATABASE_SCHEMA.md` section 14.
- **Vendor error text from Gemini could reach API clients verbatim**
  (`app/services/ai_service.py`) for non-retryable request failures - now
  logged server-side only, with a fixed generic message returned to the
  client, consistent with the rate-limit/unavailable error paths.
- **Secrets stored as plain `str` on `Settings`** (`gemini_api_key`,
  `supabase_service_role_key`) rather than `SecretStr` - no active leak was
  found, but this is defense-in-depth against a future debug log or
  unhandled-exception traceback accidentally printing one.
- **Refresh tokens were stateless with no server-side revocation** - logout
  and refresh both only validated the JWT signature/expiry; there was no
  token blocklist, so a leaked refresh token remained valid for its full
  lifetime regardless of logout/deactivation. **Fixed** in a follow-up pass
  (see section 19 below): refresh tokens are now opaque, hashed,
  database-backed sessions with rotation and reuse detection.
- **`GET /businesses` and `GET /businesses/{id}` are not district-scoped**
  for any authenticated role. Reviewed and treated as an intentional design
  choice, not a bug: businesses are the subject of complaints (comparable to
  a public business directory), not private citizen/case data, and citizens
  need to search across districts when filing a complaint. Flagged here so
  it's an explicit, documented decision rather than an unreviewed gap.

See `docs/DEVELOPMENT_ROADMAP.md` Phase 12 for the full list of fixes
(including performance/reliability items) and the dependency scan results.

## 19. Server-Side Refresh-Token Sessions

Follow-up to section 18's stateless-refresh-token finding. Uses the existing
Supabase PostgreSQL database via SQLAlchemy/Alembic - no Redis or other
external store.

**Design:**

- Access tokens are unchanged: short-lived (default 30 minutes), stateless
  JWTs, validated on every request without a database round-trip.
- Refresh tokens are opaque, high-entropy random strings (not JWTs). Only a
  SHA-256 hash is ever persisted, in `refresh_sessions.token_hash`
  (docs/DATABASE_SCHEMA.md section 4) - a database read alone cannot be
  used to authenticate as the user, and the plaintext is never logged or
  stored anywhere.
- Every access token carries a `sid` claim identifying the `refresh_sessions`
  row it was issued alongside, so `POST /auth/logout` can revoke exactly
  that session using only the access token already required to call it - no
  request body needed, preserving the existing `/auth/logout` contract.
- **Rotation:** every successful `POST /auth/refresh` revokes the presented
  token's session (`reason=rotated`) and issues a new access/refresh pair
  from a new session in the same `family_id` lineage. The response shape is
  unchanged (`TokenResponse`); the returned `refresh_token` is simply a
  different value that the client must persist and use next time.
- **Reuse detection:** presenting an already-revoked refresh token is always
  rejected. If it was revoked by rotation more than
  `refresh_token_reuse_grace_seconds` (default 5s) ago, the entire session
  family is revoked - the practical signature of a leaked/replayed token,
  as opposed to a benign near-simultaneous concurrent refresh (e.g. two
  browser tabs sharing `localStorage` both refreshing at once), which stays
  within the grace window and only rejects the losing request.
- **Concurrency safety:** rotation claims a session via a single atomic
  conditional `UPDATE ... WHERE id = :id AND revoked_at IS NULL`, so exactly
  one of any number of simultaneous refresh requests presenting the same
  token can ever win; the DB row-level consistency of that one statement is
  the actual guarantee, not application-level locking.
- **Logout** revokes only the current session (`reason=logout`).
- **Account deactivation** (`PATCH /admin/users/{user_id}/status` with
  `is_active=false`) revokes every active session for that user
  immediately, regardless of family - existing refresh tokens stop working
  right away instead of drifting on until they naturally expire.
- All refresh-token failure modes (unknown token, expired, revoked,
  reuse-detected) return the same generic `401 INVALID_TOKEN` response, to
  avoid giving a caller an oracle for which specific condition occurred.

See `app/services/auth_service.py` and `app/repositories/refresh_session_repository.py`
for the implementation, and `app/tests/integration/test_refresh_sessions.py`
/ `app/tests/unit/test_refresh_session_repository.py` for the test coverage
(rotation, reuse across and within the grace window, concurrent refresh,
logout, deactivation, and an authorization/RBAC regression check).

See section 20 below for how `refresh_sessions` rows are retained and
cleaned up over time.

## 20. Refresh-Session Maintenance: Retention and Cleanup

`refresh_sessions` (section 19) accumulates a row for every login and every
rotation. Nothing is ever deleted automatically by the request-handling
code path - deletion is a separate, explicit maintenance concern, kept out
of the request/response cycle so a login or refresh can never be slowed
down (or fail) because of cleanup work. This section defines that
maintenance strategy. It uses only the existing Supabase PostgreSQL
database via SQLAlchemy - no Redis, no Celery, no in-process scheduler.

### 20.1 What accumulates

- **Expired sessions** - a refresh token that was issued but never used
  again before `expires_at` (default 7 days after issuance). These can
  never succeed a refresh again (`refresh_access_token` rejects on
  `expires_at <= now` regardless of `revoked_at`).
- **Revoked sessions** - every rotation, logout, and account deactivation
  leaves behind a revoked row (`revoked_at` set). These can also never
  succeed a refresh again (`refresh_access_token` rejects immediately when
  `revoked_at is not None`). In steady state this is the largest source of
  rows: a token rotates on every single successful refresh, so an
  active user accumulates one revoked row per refresh, indefinitely, unless
  cleaned up.

Both categories are **permanently unusable the moment they enter that
state** - there is no path in `auth_service.py` that ever un-expires or
un-revokes a row. That is what makes deleting them, eventually, safe: a row
eligible for cleanup could not have been presented successfully a moment
before deletion either.

### 20.2 Retention policy

Deletion is not immediate on expiry/revocation - each dead row is kept for
a retention window first, so it remains available for near-term debugging
("why did my session just log out?") and security investigation. Two
tiers, controlled by `Settings` (`app/core/config.py`):

| Revocation reason / state | Setting | Default |
| --- | --- | --- |
| Expired (never revoked) | `refresh_session_retention_days` | 7 days after `expires_at` |
| Revoked: `rotated`, `logout`, `account_deactivated` | `refresh_session_retention_days` | 7 days after `revoked_at` |
| Revoked: `reuse_detected` | `refresh_session_reuse_detected_retention_days` | 90 days after `revoked_at` |

`reuse_detected` gets materially longer retention because it is the
system's strongest signal of a leaked or replayed refresh token - the row
(and its `family_id`, correlatable against other sessions for the same
user) is exactly the evidence an incident investigation would need, and it
is comparatively rare, so the extra retention costs little in row count.
Routine rotation churn is the opposite: high volume, low forensic value
beyond about a week, so it gets the short tier. These two tiers cover it
without over-engineering a per-reason policy the project has no concrete
requirement for; adjust the two settings (not the code) if a specific
compliance/retention requirement is identified later - see section 15's
general data-retention note, which applies here too.

### 20.3 Cleanup mechanism

`scripts/cleanup_refresh_sessions.py` (a standalone script, following this
project's existing `scripts/` convention alongside `create_admin.py`,
`seed_districts.py`, etc. - not a new API endpoint, since a destructive
bulk-delete operation should not be reachable over HTTP) deletes rows past
their retention window:

```bash
# from Backend/
venv/Scripts/python.exe -m scripts.cleanup_refresh_sessions --dry-run   # report only
venv/Scripts/python.exe -m scripts.cleanup_refresh_sessions             # delete
```

It calls `app/services/auth_service.py:cleanup_expired_and_revoked_sessions`,
which in turn uses `app/repositories/refresh_session_repository.py`'s
eligibility query (`count_eligible_for_cleanup` /
`delete_expired_and_revoked_batch`).

**Why it's safe to run on a schedule against a live database:**

- **Never touches a live session.** The eligibility query is a strict
  subset of "already expired or already revoked, and aged past its
  retention window" - by construction (section 20.1) that can never
  include a row that could still succeed a refresh. There is no window
  where a concurrently-running refresh request and the cleanup job could
  race over the same still-usable row, because a row only becomes
  cleanup-eligible once no future refresh could ever legitimately use it
  again - eligibility is monotonic (a row never becomes ineligible once
  eligible, and never becomes eligible before it's genuinely dead).
- **Batched deletes.** Each call deletes at most `--batch-size` rows
  (default 1000) and commits before continuing, rather than one unbounded
  `DELETE`. This bounds how long any single transaction holds locks or
  grows the write-ahead log, which matters most on the first run after a
  gap (a large accumulated backlog) or on a table that's grown large.
- **Self-referential FK handled explicitly.** `replaced_by_id` (the link
  from a rotated-away session to the session that replaced it) is nulled
  out for any row about to be deleted, in the same transaction, rather than
  relying solely on the column's `ON DELETE SET NULL` - see
  `refresh_session_repository.delete_expired_and_revoked_batch`'s
  docstring.
- **Idempotent.** Running it twice in a row (or concurrently with itself)
  deletes nothing extra the second time; there's no state beyond what's
  already in the table.
- **`--dry-run` first.** Reports the eligible count without deleting
  anything, for verifying the policy's effect before scheduling it or
  after changing the retention settings.

### 20.4 Scheduling

There is no in-process scheduler, background worker, Celery, or Redis in
this project, and this maintenance task does not need one - running the
script periodically *is* the mechanism. Wire it up with whatever the
deployment environment already provides:

- **Local/VM deployment:** a daily cron entry, e.g.
  `0 3 * * * cd /path/to/backend && venv/bin/python -m scripts.cleanup_refresh_sessions`.
- **Windows:** a daily Task Scheduler entry running the same command.
- **Render demo deployment (Phase 13):** a scheduled GitHub Actions workflow,
  `.github/workflows/cleanup-refresh-sessions.yml`, running daily against the
  production `DATABASE_URL` (set as a repository secret). Render's own Cron
  Job service type requires a paid plan, incompatible with this project's
  Free Tier target, so GitHub Actions' free scheduled workflows are used
  instead - no new always-on service, no Redis/Celery. See
  `docs/DEPLOYMENT.md` section 7 for the full setup.

Daily is a reasonable default frequency given 7/90-day retention windows -
there is no urgency to clean up more often, since eligible rows are already
long dead by the time they're deleted either way.
