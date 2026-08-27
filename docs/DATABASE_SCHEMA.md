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
- `ocr_text` nullable
- `ai_analysis` JSONB nullable
- `created_at`

Use Storage for the actual file.

## 14. `assignments`

Purpose: assignment of cases to staff.

Suggested columns:

- `id`
- `complaint_id`
- `assigned_to_staff_id`
- `assigned_by_staff_id`
- `assigned_at`
- `due_at`
- `status`
- `notes`

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

## 20. RAG Tables

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

## 21. Indexing

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
- geographic columns for location queries
- vector index for RAG embeddings after retrieval requirements are validated

## 22. Migrations

All schema changes must be made through Alembic.

Development workflow:

```text
Edit SQLAlchemy models
    -> alembic revision --autogenerate -m "description"
    -> review migration manually
    -> alembic upgrade head
```

Never blindly trust autogenerated migrations; review generated SQL and constraints.
