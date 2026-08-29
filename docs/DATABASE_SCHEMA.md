# Database Schema

## 1. Purpose

This document defines the relational data model for the Maharashtra Food Safety Complaint and Inspection Platform.

Database technology: PostgreSQL on Supabase.

ORM: SQLAlchemy.

Migrations: Alembic.

Optional PostgreSQL extensions: PostGIS and pgvector.

## 2. Design Principles

- Use UUID primary keys unless there is a concrete reason to use another type.
- Keep human-readable complaint numbers separate from database IDs.
- Normalize core operational entities.
- Use foreign keys and database constraints for integrity.
- Add created/updated timestamps to mutable entities.
- Prefer enums or controlled lookup tables for workflow states.
- Store large media in Supabase Storage, not PostgreSQL binary columns.
- Record audit history for important operational changes.
- Never use database structure as a substitute for authorization checks.

## 3. Core Entity Relationship

```text
users
  |
  +----< staff_profiles >---- districts
  |
  +----< complaints >---- businesses
                 |
                 +----< evidence
                 |
                 +----< complaint_status_history
                 |
                 +----< assignments >---- staff_profiles
                 |
                 +----< inspections
                                |
                                +----< inspection_findings
                                |
                                +----< inspection_evidence

districts
   |
   +----< businesses
   |
   +----< staff_profiles

rag_documents
   |
   +----< rag_chunks
```

## 4. `users`

Purpose: authentication identity and basic account state.

Suggested columns:

- `id` UUID PK
- `email` unique, not null
- `password_hash` nullable when external authentication is used
- `full_name`
- `phone`
- `is_active`
- `email_verified_at`
- `created_at`
- `updated_at`
- `last_login_at`

Do not store plaintext passwords.

### `refresh_sessions`

Purpose: server-side, revocable refresh-token sessions
(docs/SECURITY_AND_RBAC.md section 18). Access tokens remain short-lived,
stateless JWTs; refresh tokens are opaque random strings whose hash is
looked up here on every `POST /auth/refresh` call, which is what makes
revocation possible - a stateless JWT refresh token cannot be revoked once
issued.

Columns:

- `id` UUID PK - also embedded as the `sid` claim on the access token
  issued alongside it, so `POST /auth/logout` can revoke the right row
  using only the access token already required to call it
- `user_id` FK `users.id`, `ondelete=CASCADE`
- `family_id` - constant across every rotation descending from one login;
  lets the whole lineage be revoked at once (logout, deactivation, reuse
  detection)
- `token_hash` - SHA-256 hex digest of the refresh token; unique, indexed.
  **The plaintext token is never stored.**
- `created_at`, `expires_at`
- `revoked_at`, `revoked_reason` (`rotated` | `logout` |
  `account_deactivated` | `reuse_detected` - see
  `app/utils/enums.py:RefreshSessionRevokedReason`)
- `replaced_by_id` - self-referential FK, `ondelete=SET NULL`; the session
  that replaced this one via rotation

Refresh tokens rotate on every successful `POST /auth/refresh`: the
presented token's session is revoked (`reason=rotated`) and a new one is
created in the same `family_id`. Presenting an already-rotated token again
is rejected; if that happens more than
`Settings.refresh_token_reuse_grace_seconds` (default 5s) after the
rotation - ruling out a benign near-simultaneous concurrent refresh from,
e.g., multiple browser tabs - the entire `family_id` is revoked
(`reason=reuse_detected`), since that pattern is the practical signature of
a leaked/replayed token. See `app/services/auth_service.py` for the full
rotation/reuse-detection state machine.

Rows are never deleted by the request-handling code - `scripts/cleanup_refresh_sessions.py`
periodically deletes expired/revoked rows once they age past a retention
window (7 days generally, 90 days for `reuse_detected` rows). See
`docs/SECURITY_AND_RBAC.md` section 20 for the full retention/cleanup
policy.

## 5. Roles

A user has one application role in the initial implementation:

- `citizen`
- `inspector`
- `district_officer`
- `admin`

For future expansion, roles may be normalized into `roles` and `user_roles` tables. The initial implementation can use an enum if simplicity is preferred.

## 6. `districts`

Purpose: Maharashtra administrative districts used for data isolation.

Suggested columns:

- `id`
- `name`
- `code` unique
- `division_id`
- `is_active`
- `created_at`
- `updated_at`

The seeded data must contain all 36 Maharashtra districts used by the project.

## 7. `divisions`

Purpose: higher-level grouping of districts.

Suggested columns:

- `id`
- `name`
- `code` unique
- `created_at`
- `updated_at`

Seed the six divisions used by the application.

## 8. `staff_profiles`

Purpose: staff-specific attributes linked to a user.

Suggested columns:

- `id`
- `user_id` unique FK -> users
- `district_id` FK -> districts
- `employee_code` unique
- `designation`
- `is_active`
- `created_at`
- `updated_at`

For district officers, enforce one active officer per district at the application/business-rule level, and preferably with a suitable PostgreSQL partial unique index.

Inspectors may be multiple per district.

## 9. `businesses`

Purpose: food businesses against which complaints and inspections are recorded.

Suggested columns:

- `id`
- `business_name`
- `business_type`
- `license_number`
- `registration_number`
- `address`
- `district_id`
- `latitude`
- `longitude`
- `location` geography(Point, 4326) when PostGIS is enabled
- `contact_phone`
- `is_active`
- `created_at`
- `updated_at`

Index `district_id`, `license_number`, and geographic location where useful.

## 10. `complaints`

Purpose: citizen-reported incidents.

Suggested columns:

- `id` UUID PK
- `complaint_number` unique
- `submitted_by_user_id` FK -> users
- `business_id` nullable FK -> businesses
- `district_id` FK -> districts
- `category_id` FK -> complaint_categories
- `title`
- `description`
- `status`
- `priority`
- `latitude`
- `longitude`
- `location` geography(Point, 4326)
- `reported_at`
- `verified_at`
- `resolved_at`
- `created_at`
- `updated_at`

## 11. `complaint_categories`

Examples:

- expired_food
- spoiled_food
- unhygienic_premises
- improper_storage
- contamination
- foreign_object
- labelling_issue
- suspected_adulteration
- other

Keep category names stable because AI classification may depend on them.

## 12. Complaint Status

Recommended states:

```text
submitted
under_review
verified
rejected
assigned
inspection_scheduled
under_inspection
inspection_completed
action_in_progress
resolved
closed
```

Avoid deleting historical complaints as a way to hide them. Use lifecycle states and audit records.

## 13. `evidence`

Purpose: metadata for uploaded complaint/inspection evidence.

Suggested columns:

- `id`
- `complaint_id` FK
- `uploaded_by_user_id` FK
- `storage_bucket`
- `storage_path`
- `file_type`
- `file_size`
- `checksum`
- `captured_at`
- `latitude`
- `longitude`
- `created_at`

Use Storage for the actual file. AI-generated OCR text and evidence analysis
are **not** stored as columns on this table - see section 20.1
(`evidence_analysis_results`) for why and where they live instead.

## 14. `assignments`

Purpose: assignment of cases to staff.

Suggested columns:

- `id`
- `complaint_id` (unique - a complaint has at most one assignment; see
  Phase 12 note below)
- `assigned_to_staff_id`
- `assigned_by_staff_id`
- `assigned_at`
- `due_at`
- `status`
- `notes`

**Phase 12 hardening note:** `complaint_id` carries a database-level unique
constraint (`uq_assignments_complaint_id`, added in
`alembic/versions/a1b2c3d4e5f6_add_assignment_complaint_unique_constraint.py`),
mirroring the pre-existing unique constraint on `inspections.complaint_id`.
Without it, two concurrent `assign_inspector` requests for the same
complaint could both pass the `complaint.status == VERIFIED` check before
either committed, creating two `assignments` rows for one complaint;
`assignment_repository.get_by_complaint_id`'s `scalar_one_or_none()` would
then raise `MultipleResultsFound` on every later read.
`assignment_service.assign_inspector` catches the resulting `IntegrityError`
and raises the same `InvalidAssignmentError` used for the "not verified"
case, so the loser of the race gets a clean 409 instead of a 500.

## 15. `inspections`

Suggested columns:

- `id`
- `complaint_id`
- `inspector_id`
- `scheduled_at`
- `started_at`
- `completed_at`
- `inspection_status`
- `summary`
- `action_recommended`
- `report_storage_path`
- `created_at`
- `updated_at`

## 16. `inspection_findings`

Suggested columns:

- `id`
- `inspection_id`
- `check_code`
- `finding`
- `severity`
- `compliant`
- `notes`
- `created_at`

This allows structured checklists while retaining free-text inspector notes.

## 17. `complaint_status_history`

Purpose: immutable timeline of case status transitions.

Suggested columns:

- `id`
- `complaint_id`
- `old_status`
- `new_status`
- `changed_by_user_id`
- `reason`
- `created_at`

## 18. `audit_logs`

Track sensitive or important actions:

- user/role changes
- complaint reassignment
- complaint status changes
- inspection updates
- evidence deletion/access where appropriate
- admin actions
- AI tool executions when operationally significant

Suggested columns:

- `id`
- `actor_user_id`
- `action`
- `entity_type`
- `entity_id`
- `details` JSONB
- `created_at`

## 19. Notifications

Suggested `notifications` table:

- `id`
- `user_id`
- `type`
- `title`
- `message`
- `entity_type`
- `entity_id`
- `is_read`
- `created_at`

## 20. AI Advisory Result Tables

Advisory AI output (Phase 6 Complaint Triage, Phase 7 Evidence Analysis) is
never written into the source-of-truth tables (`complaints`, `evidence`).
Each agent instead appends rows to its own results table, so that:

- the original citizen/inspector-submitted record is never overwritten,
- re-running an agent accumulates history instead of destroying the prior
  result, and
- callers can distinguish "no analysis has been run yet" from "analysis ran
  and failed" from "analysis completed".

Both tables share the same shape: a foreign key to the source record, who
requested the run, a `model_used` string, a `completed`/`failed` status, the
structured fields specific to that agent, `confidence`/uncertainty
indicators, `error_code`/`error_message` (populated only when `status =
failed`), and `created_at`. Callers read the latest row by `created_at`
rather than assuming one row per source record.

### `complaint_triage_results`

- `id`
- `complaint_id` FK -> complaints (CASCADE)
- `requested_by_user_id` FK -> users (RESTRICT)
- `status` (`completed` / `failed`)
- `model_used`
- `suggested_category_id` FK -> complaint_categories (SET NULL, only ever a
  real active category)
- `suggested_category_raw` - the raw label the model produced, kept even when
  it didn't map onto a known category
- `category_match_uncertain`
- `suggested_priority` (reuses the `complaint_priority` enum)
- `summary`
- `entities` JSON (e.g. business name/product extracted from the complaint
  text)
- `missing_information` JSON (list of strings)
- `confidence`, `is_uncertain`
- `error_code`, `error_message`
- `created_at`

### `evidence_analysis_results`

- `id`
- `evidence_id` FK -> evidence (CASCADE)
- `requested_by_user_id` FK -> users (RESTRICT)
- `status` (`completed` / `failed`)
- `model_used`
- `extracted_text` (OCR)
- `product_name`, `manufacturer`, `batch_lot_number`
- `manufacturing_date_text`, `expiry_date_text` - raw as extracted from the
  label, never parsed into a `Date` column since packaging dates are
  frequently partial/ambiguous
- `possible_expired` - a deterministic, code-side interpretation of
  `expiry_date_text` against the current date, kept separate from the raw
  extracted value; `NULL` when the date couldn't be parsed. This is an
  advisory flag for officer/inspector review only, never a legal conclusion
  that a product is expired or non-compliant.
- `packaging_observations`, `hygiene_observations`,
  `foreign_object_observations`
- `uncertainty_notes` JSON (list of strings)
- `confidence`, `is_uncertain`
- `error_code`, `error_message`
- `created_at`

### `investigation_briefs`

AI-generated Investigation Agent output for a District Officer (Phase 9, see
`docs/AI_AGENTS_ARCHITECTURE.md` section 6), stored separately from
`complaints`/`inspections` for the same reasons as the two tables above.
`relevant_evidence` and `business_history` are populated directly from
controlled tool results (never model-generated prose), so those facts can
never be fabricated - only the analytical fields are model-generated, and
every `regulatory_guidance` entry carries a citation resolved against an
actually-retrieved RAG chunk (an entry whose citation can't be resolved is
dropped rather than persisted uncited).

- `id`
- `complaint_id` FK -> complaints (CASCADE)
- `requested_by_user_id` FK -> users (RESTRICT) - the requesting district
  officer
- `status` (`completed` / `failed`)
- `model_used`
- `case_summary` - model-generated, grounded only in the data fetched below
- `relevant_evidence` JSON - list of completed evidence-analysis summaries,
  copied verbatim from `evidence_analysis_results` via the agent's
  `get_evidence_analysis` tool
- `business_history` JSON - business info, previous-complaint count/list, and
  previous-inspection count/list, all from controlled tools scoped to the
  officer's own district
- `complaint_patterns` JSON (list of strings) - model-identified patterns
  across the complaint/inspection history above
- `regulatory_guidance` JSON (list of `{guidance, citation}`) - model-drafted
  guidance, each entry cited against a retrieved `rag_document_chunks` row
- `risk_indicators` JSON (list of strings)
- `missing_information` JSON (list of strings) - merges deterministic,
  code-detected gaps (no triage run, no evidence analysis, no inspection
  yet, ...) with model-identified ones
- `suggested_actions` JSON (list of strings) - investigation/review actions
  only, never a penalty, enforcement action, or case resolution
- `confidence`, `is_uncertain`, `uncertainty_reasons` JSON (list of strings)
- `error_code`, `error_message`
- `created_at`

## 21. RAG Tables

### `rag_documents`

- `id`
- `title`
- `source_organization`
- `document_type`
- `version`
- `effective_date`
- `source_url`
- `storage_path`
- `checksum`
- `created_at`
- `updated_at`

### `rag_chunks`

- `id`
- `document_id`
- `chunk_index`
- `content`
- `page_number`
- `section_title`
- `metadata` JSONB
- `embedding` vector(...) when pgvector is enabled
- `created_at`

## 22. Indexing

Recommended indexes include:

- users.email
- users role where useful
- staff_profiles.district_id
- businesses.district_id
- businesses.license_number
- complaints.district_id + status
- complaints.district_id + priority
- complaints.business_id
- complaints.created_at
- assignments.assigned_to_staff_id + status
- inspections.inspector_id + inspection_status
- complaint_status_history.complaint_id + created_at
- complaint_triage_results.complaint_id + created_at
- evidence_analysis_results.evidence_id + created_at
- investigation_briefs.complaint_id + created_at
- geographic columns for location queries
- vector index for RAG embeddings after retrieval requirements are validated

## 23. Migrations

All schema changes must be made through Alembic.

Development workflow:

```text
Edit SQLAlchemy models
    -> alembic revision --autogenerate -m "description"
    -> review migration manually
    -> alembic upgrade head
```

Never blindly trust autogenerated migrations; review generated SQL and constraints.
