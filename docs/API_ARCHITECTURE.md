# API Architecture

## 1. API Style

Use REST APIs over HTTPS with JSON request/response bodies unless a binary upload flow requires multipart form data.

Base path:

```text
/api/v1
```

All production endpoints require authentication unless explicitly marked public.

## 2. Authentication

The backend should use token-based authentication. The exact provider may be implemented with application-managed JWTs or Supabase Auth, but there must be one consistent identity model.

Every protected request resolves:

- `user_id`
- `role`
- `district_id` for district-scoped staff
- active/inactive status

## 3. API Layering

```text
Router
  -> dependency/authentication
  -> RBAC / scope check
  -> Pydantic validation
  -> service
  -> repository
  -> SQLAlchemy
```

Routes should stay thin. Business logic belongs in services.

## 4. Error Format

Use a consistent error response:

```json
{
  "error": {
    "code": "COMPLAINT_NOT_FOUND",
    "message": "Complaint was not found.",
    "details": null,
    "request_id": "..."
  }
}
```

Do not leak database stack traces or sensitive implementation details.

## 5. Authentication Endpoints

```text
POST /auth/register
POST /auth/login
POST /auth/refresh
POST /auth/logout
POST /auth/forgot-password
POST /auth/reset-password
GET  /auth/me
```

Staff creation should not use public self-registration.

## 6. Citizen Complaint Endpoints

```text
POST /complaints
GET  /complaints/my
GET  /complaints/{complaint_id}
PATCH /complaints/{complaint_id}
POST /complaints/{complaint_id}/evidence
GET  /complaints/{complaint_id}/timeline
```

Citizens may read and modify only fields/cases they are authorized to access.

## 7. Business Endpoints

```text
GET  /businesses
GET  /businesses/{business_id}
POST /businesses
PATCH /businesses/{business_id}
```

Search and filtering should support district scope, name, business type, license number, and geography where relevant.

## 8. District Officer Endpoints

```text
GET  /officer/dashboard
GET  /officer/complaints
GET  /officer/complaints/{complaint_id}
POST /officer/complaints/{complaint_id}/verify
POST /officer/complaints/{complaint_id}/reject
POST /officer/complaints/{complaint_id}/assign
GET  /officer/inspectors
GET  /officer/analytics
GET  /officer/businesses/{business_id}/complaints
POST /officer/complaints/{complaint_id}/triage
GET  /officer/complaints/{complaint_id}/triage
POST /officer/complaints/{complaint_id}/evidence/{evidence_id}/analysis
GET  /officer/complaints/{complaint_id}/evidence/{evidence_id}/analysis
POST /officer/complaints/{complaint_id}/investigation
GET  /officer/complaints/{complaint_id}/investigation
```

See section 11 for the agent endpoints. All officer endpoints automatically
scope operational data to the officer's district.

## 9. Inspector Endpoints

```text
GET  /inspector/dashboard
GET  /inspector/assignments
GET  /inspector/assignments/{assignment_id}
POST /inspector/inspections
PATCH /inspector/inspections/{inspection_id}
POST /inspector/inspections/{inspection_id}/findings
POST /inspector/inspections/{inspection_id}/evidence
POST /inspector/inspections/{inspection_id}/evidence/{evidence_id}/analysis
GET  /inspector/inspections/{inspection_id}/evidence/{evidence_id}/analysis
POST /inspector/inspections/{inspection_id}/complete
GET  /inspector/history
```

Inspectors can only access cases assigned to them or otherwise explicitly authorized within their district.

## 10. Admin Endpoints

```text
GET  /admin/dashboard
POST /admin/staff
PATCH /admin/staff/{staff_id}
GET  /admin/users
PATCH /admin/users/{user_id}/status
GET  /admin/districts
GET  /admin/businesses
GET  /admin/audit-logs
GET  /admin/analytics
```

Admin actions require elevated permissions and should create audit records.

As implemented (Phase 10), `/admin/audit-logs` is a read-only, filterable
listing (`actor_user_id`, `action`, `entity_type`, `entity_id`, `date_from`,
`date_to`, pagination) over `app.repositories.audit_log_repository.list_logs`
- there is intentionally no corresponding write/update/delete endpoint,
since audit records are only ever created as a side effect of the action
they describe (see section 19 below). `/admin/analytics` and
`/officer/analytics` return the statewide/district-scoped KPI payloads from
`app.services.analytics_service`.

## 8.1 Notifications

Notifications are not role-specific - every authenticated identity manages
its own inbox through one shared, top-level resource rather than being
duplicated under `/citizen`, `/officer`, `/inspector`, and `/admin`:

```text
GET   /notifications
GET   /notifications/unread-count
PATCH /notifications/{notification_id}/read
POST  /notifications/read-all
```

Scope is always the authenticated user's own `user_id` - there is no
parameter to request another user's notifications. See
docs/PROJECT_SPEC.md section 27 for the workflow events that create them
(complaint submitted/verified/rejected/resolved, inspector assigned,
inspection scheduled/completed) - each is written by the same service call
that performs the triggering action
(`app.services.complaint_service`/`app.services.assignment_service`), never
by a separate notification job.

## 11. Agent Endpoints

Do not expose internal agent tools directly as public APIs.

As implemented (Phase 6 Complaint Triage, Phase 7 Evidence Analysis), agent
endpoints are nested under the owning resource rather than under a flat
top-level `/agent/*` namespace, so the same authorization/scope dependency
that resolves the resource (`get_complaint_for_officer`,
`get_inspection_for_inspector`, ...) always runs before the agent is ever
called:

```text
POST /officer/complaints/{complaint_id}/triage
GET  /officer/complaints/{complaint_id}/triage

POST /officer/complaints/{complaint_id}/evidence/{evidence_id}/analysis
GET  /officer/complaints/{complaint_id}/evidence/{evidence_id}/analysis

POST /inspector/inspections/{inspection_id}/evidence/{evidence_id}/analysis
GET  /inspector/inspections/{inspection_id}/evidence/{evidence_id}/analysis

POST /officer/complaints/{complaint_id}/investigation
GET  /officer/complaints/{complaint_id}/investigation
```

`POST` explicitly triggers a new agent run (never automatic on view); `GET`
reads the latest persisted result without calling the AI provider again. For
evidence analysis and the Investigation Agent, `POST` also accepts
`?force=true` to explicitly re-run the agent even when a completed result
already exists - without it, an existing completed result is returned as-is
rather than calling the AI provider again.

The Investigation Agent (Phase 9) follows the same
`complaint_service.get_complaint_for_officer`-scoped pattern as triage/
evidence analysis - district isolation and role checks run before the agent
is ever invoked, never inside it.

The Inspector Assistant (Phase 8) instead exposes a small conversation
resource nested under `/inspector/assistant/conversations` (see section 9)
since it is multi-turn, but still resolves its scope
(`inspection_service.get_inspection_for_inspector`) the same way before the
agent runs. Future agents (e.g. Report Generation) should follow whichever
of these two shapes fits - single-shot cacheable result vs. conversation -
rather than a flat `/agent/*` path.

These endpoints must validate role and scope before the agent is invoked.

## 12. RAG Endpoints

RAG administration should be restricted to authorized staff/admin workflows.

```text
POST /admin/rag/documents
GET  /admin/rag/documents
POST /admin/rag/documents/{document_id}/ingest
GET  /admin/rag/documents/{document_id}
```

The inspector-facing application should generally use the Inspector Assistant endpoint instead of exposing raw vector-search endpoints.

## 13. Pagination

List endpoints should use pagination.

Recommended query parameters:

```text
?page=1&page_size=20
```

Where datasets are large, cursor pagination can be introduced.

## 14. Filtering and Sorting

Use explicit allowlists for filterable/sortable fields.

Example:

```text
GET /officer/complaints?status=verified&priority=high&category=expired_food
```

Do not concatenate arbitrary query strings into SQL.

## 15. File Uploads

Recommended flow:

```text
Client
  -> backend validates user + complaint
  -> upload authorization
  -> Supabase Storage
  -> evidence metadata saved in DB
```

Validate file type, size, ownership, and allowed storage path.

## 16. Idempotency

For operations that may be retried, such as report generation or notification triggers, use idempotency keys or database uniqueness rules where needed.

## 17. Versioning

Do not break existing contracts casually. Add new fields as optional where possible and introduce a new API version for incompatible changes.

## 18. Security Rules

- Never trust role/district values supplied by clients.
- Enforce object-level authorization on every resource endpoint.
- Protect admin routes separately.
- Validate IDs and request bodies.
- Rate-limit public complaint creation and authentication endpoints.
- Restrict CORS in production.
- Keep secrets in environment/secret management.
- Return safe error messages.
