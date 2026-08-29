# Project Architecture Tree

## Purpose

This document is the canonical reference for the repository's folder and module structure use it as reference not the same exact architecture.

Claude Code should consult this file together with:

- `docs/PROJECT_SPEC.md`
- `docs/SYSTEM_ARCHITECTURE.md`
- `docs/DATABASE_SCHEMA.md`
- `docs/API_ARCHITECTURE.md`
- `docs/AI_AGENTS_ARCHITECTURE.md`
- `docs/RAG_ARCHITECTURE.md`
- `docs/SECURITY_AND_RBAC.md`
- `docs/DEVELOPMENT_ROADMAP.md`

Do not introduce a new top-level architecture without updating this document and the relevant architecture document.

---

## Repository Tree

```text
Food Safety/
│
├── README.md
├── .gitignore
├── .env.example
├── CLAUDE.md
├── render.yaml
├── docker-compose.yml
├── docker-compose.prod.yml
├── Makefile
│
├── docs/
│   ├── PROJECT_SPEC.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── API_ARCHITECTURE.md
│   ├── AI_AGENTS_ARCHITECTURE.md
│   ├── RAG_ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── SECURITY_AND_RBAC.md
│   ├── DEVELOPMENT_ROADMAP.md
│   └── ARCHITECTURE_TREE.md
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tsconfig.json
│   ├── .env.example
│   ├── public/
│   │   ├── favicon.ico
│   │   └── images/
│   │
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       │
│       ├── assets/
│       │   ├── images/
│       │   └── icons/
│       │
│       ├── components/
│       │   ├── common/
│       │   │   ├── Button.jsx
│       │   │   ├── Modal.jsx
│       │   │   ├── Loader.jsx
│       │   │   ├── ErrorMessage.jsx
│       │   │   └── Pagination.jsx
│       │   │
│       │   ├── layout/
│       │   │   ├── Navbar.jsx
│       │   │   ├── Sidebar.jsx
│       │   │   ├── Footer.jsx
│       │   │   └── DashboardLayout.jsx
│       │   │
│       │   ├── complaint/
│       │   │   ├── ComplaintForm.jsx
│       │   │   ├── ComplaintCard.jsx
│       │   │   ├── ComplaintStatus.jsx
│       │   │   ├── EvidenceUploader.jsx
│       │   │   └── ComplaintTimeline.jsx
│       │   │
│       │   ├── map/
│       │   │   ├── ComplaintMap.jsx
│       │   │   ├── ComplaintMarker.jsx
│       │   │   └── LocationPicker.jsx
│       │   │
│       │   ├── dashboard/
│       │   │   ├── StatsCard.jsx
│       │   │   ├── ComplaintChart.jsx
│       │   │   ├── PriorityChart.jsx
│       │   │   └── TrendChart.jsx
│       │   │
│       │   └── agent/
│       │       ├── AgentChat.jsx
│       │       ├── AgentResponse.jsx
│       │       └── SourceCitation.jsx
│       │
│       ├── pages/
│       │   ├── public/
│       │   │   ├── Home.jsx
│       │   │   ├── About.jsx
│       │   │   └── Contact.jsx
│       │   │
│       │   ├── auth/
│       │   │   ├── Login.jsx
│       │   │   ├── Register.jsx
│       │   │   ├── ForgotPassword.jsx
│       │   │   └── ResetPassword.jsx
│       │   │
│       │   ├── citizen/
│       │   │   ├── CitizenDashboard.jsx
│       │   │   ├── CreateComplaint.jsx
│       │   │   ├── MyComplaints.jsx
│       │   │   ├── ComplaintDetails.jsx
│       │   │   └── Profile.jsx
│       │   │
│       │   ├── inspector/
│       │   │   ├── InspectorDashboard.jsx
│       │   │   ├── AssignedComplaints.jsx
│       │   │   ├── InspectionDetails.jsx
│       │   │   ├── InspectionForm.jsx
│       │   │   ├── InspectionHistory.jsx
│       │   │   └── InspectorAssistant.jsx
│       │   │
│       │   ├── officer/
│       │   │   ├── OfficerDashboard.jsx
│       │   │   ├── ComplaintQueue.jsx
│       │   │   ├── ComplaintReview.jsx
│       │   │   ├── AssignInspector.jsx
│       │   │   └── Investigation.jsx
│       │   │
│       │   └── admin/
│       │       ├── AdminDashboard.jsx
│       │       ├── ManageUsers.jsx
│       │       ├── ManageStaff.jsx
│       │       ├── ManageBusinesses.jsx
│       │       ├── ManageCategories.jsx
│       │       ├── SystemAnalytics.jsx
│       │       └── AuditLogs.jsx
│       │
│       ├── services/
│       │   ├── api.js
│       │   ├── authService.js
│       │   ├── complaintService.js
│       │   ├── inspectionService.js
│       │   ├── businessService.js
│       │   ├── agentService.js
│       │   └── uploadService.js
│       │
│       ├── store/
│       │   ├── authStore.js
│       │   ├── complaintStore.js
│       │   └── uiStore.js
│       │
│       ├── hooks/
│       │   ├── useAuth.js
│       │   ├── useComplaints.js
│       │   ├── useLocation.js
│       │   └── useDebounce.js
│       │
│       ├── utils/
│       │   ├── constants.js
│       │   ├── validators.js
│       │   ├── formatters.js
│       │   └── permissions.js
│       │
│       └── routes/
│           ├── AppRoutes.jsx
│           ├── ProtectedRoute.jsx
│           └── RoleRoute.jsx
│
├── backend/
│   ├── requirements.txt
│   ├── pyproject.toml
│   ├── Dockerfile
│   ├── .env.example
│   ├── alembic.ini
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       ├── 0536e568a656_add_users_divisions_districts_staff_.py
│   │       ├── 5867bff9f79e_add_complaint_management_tables.py
│   │       ├── 014114ea0cea_add_postgis_and_location_columns.py
│   │       ├── 30824dc06f71_add_inspection_assignment_workflow.py
│   │       ├── 18b2ad6af96d_add_complaint_triage_results.py
│   │       ├── 09b78bb3d711_add_evidence_analysis_results.py
│   │       ├── 7c3f1a9d2e4b_add_rag_and_assistant_tables.py
│   │       ├── 4d8e6a1c9b2f_add_investigation_briefs.py
│   │       ├── 8f1a2c6d4b3e_add_notifications_and_audit_log_indexes.py
│   │       └── ...
│   │
│   └── app/
│       ├── main.py
│       │
│       ├── core/
│       │   ├── config.py
│       │   ├── security.py
│       │   ├── database.py
│       │   ├── dependencies.py
│       │   ├── logging.py
│       │   ├── gemini.py          # centralized Gemini client (see app.services.ai_service)
│       │   └── geo_types.py
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── division.py
│       │   ├── district.py
│       │   ├── staff_profile.py
│       │   ├── business.py
│       │   ├── complaint.py
│       │   ├── complaint_category.py
│       │   ├── complaint_sequence.py
│       │   ├── complaint_status_history.py
│       │   ├── complaint_triage.py    # Phase 6 advisory result, see DATABASE_SCHEMA.md sec 20
│       │   ├── evidence.py
│       │   ├── evidence_analysis.py   # Phase 7 advisory result, see DATABASE_SCHEMA.md sec 20
│       │   ├── assignment.py
│       │   ├── inspection.py
│       │   ├── inspection_finding.py
│       │   ├── investigation_brief.py # Phase 9 advisory result, see DATABASE_SCHEMA.md sec 20
│       │   ├── notification.py        # Phase 10, see DATABASE_SCHEMA.md sec 19
│       │   ├── rag_document.py
│       │   ├── rag_document_chunk.py
│       │   ├── assistant_conversation.py
│       │   ├── assistant_message.py
│       │   └── audit_log.py
│       │
│       ├── schemas/
│       │   ├── auth.py
│       │   ├── user.py
│       │   ├── staff.py
│       │   ├── district.py
│       │   ├── business.py
│       │   ├── complaint.py
│       │   ├── complaint_category.py
│       │   ├── complaint_status_history.py
│       │   ├── evidence.py
│       │   ├── inspection.py
│       │   ├── assignment.py
│       │   ├── agent.py           # ComplaintTriageRead, EvidenceAnalysisRead, InvestigationBriefRead, Assistant*
│       │   ├── rag.py
│       │   ├── notification.py    # Phase 10
│       │   ├── analytics.py       # Phase 10
│       │   ├── audit_log.py       # Phase 10
│       │   └── common.py
│       │
│       ├── api/
│       │   ├── router.py
│       │   ├── health.py
│       │   ├── businesses.py
│       │   ├── reference.py
│       │   ├── auth/
│       │   ├── citizen/
│       │   ├── officer/           # includes /triage, /evidence/{id}/analysis, /investigation, /analytics endpoints
│       │   ├── inspector/         # includes /evidence/{id}/analysis and /assistant endpoints
│       │   ├── admin/             # includes /rag/documents, /analytics, /audit-logs endpoints
│       │   └── notifications.py   # Phase 10 - shared across all roles, scoped to current_user.id
│       │
│       ├── services/
│       │   ├── auth_service.py
│       │   ├── staff_service.py
│       │   ├── complaint_service.py
│       │   ├── complaint_category_service.py
│       │   ├── business_service.py
│       │   ├── district_service.py
│       │   ├── geocoding_service.py
│       │   ├── inspection_service.py
│       │   ├── assignment_service.py
│       │   ├── evidence_service.py
│       │   ├── storage_service.py     # Supabase Storage: upload/download/signed URLs
│       │   ├── ai_service.py          # centralized Gemini text/structured/multimodal wrapper
│       │   ├── rag_document_service.py
│       │   ├── assistant_service.py
│       │   ├── notification_service.py  # Phase 10 - read/mark-read for a user's own inbox
│       │   ├── analytics_service.py     # Phase 10 - district/statewide KPI aggregation
│       │   └── audit_log_service.py     # Phase 10 - read-only admin audit-log listing
│       │
│       ├── repositories/
│       │   ├── user_repository.py
│       │   ├── staff_repository.py
│       │   ├── division_repository.py
│       │   ├── district_repository.py
│       │   ├── business_repository.py
│       │   ├── complaint_repository.py
│       │   ├── complaint_category_repository.py
│       │   ├── complaint_sequence_repository.py
│       │   ├── complaint_status_history_repository.py
│       │   ├── complaint_triage_repository.py
│       │   ├── evidence_repository.py
│       │   ├── evidence_analysis_repository.py
│       │   ├── assignment_repository.py
│       │   ├── inspection_repository.py
│       │   ├── inspection_finding_repository.py
│       │   ├── investigation_repository.py
│       │   ├── rag_document_repository.py
│       │   ├── rag_chunk_repository.py
│       │   ├── assistant_repository.py
│       │   ├── audit_log_repository.py    # Phase 10 adds list_logs(); record() is still the only writer
│       │   ├── notification_repository.py # Phase 10 - flush-only create(), mirrors audit_log_repository.record
│       │   └── analytics_repository.py    # Phase 10 - aggregation queries, no ORM model of its own
│       │
│       ├── agents/
│       │   ├── complaint_triage/
│       │   │   └── agent.py       # Phase 6 - module functions, not a class
│       │   ├── evidence_analysis/
│       │   │   └── agent.py       # Phase 7 - module functions, not a class
│       │   ├── inspector_assistant/
│       │   │   ├── agent.py       # Phase 8 - module functions, not a class
│       │   │   └── tools.py
│       │   └── investigation/
│       │       ├── agent.py       # Phase 9 - module functions, not a class
│       │       └── tools.py
│       │
│       ├── rag/
│       │   ├── parsing.py
│       │   ├── chunking.py
│       │   ├── ingestion.py
│       │   └── retrieval.py
│       │
│       ├── utils/
│       │   ├── enums.py
│       │   ├── validators.py
│       │   ├── geo.py
│       │   └── exceptions.py
│       │
│       └── tests/
│           ├── conftest.py
│           ├── factories.py
│           ├── unit/
│           └── integration/
│
├── data/
│   ├── raw/
│   │   └── food_safety_documents/
│   ├── processed/
│   │   ├── chunks/
│   │   └── metadata/
│   └── sample/
│       ├── complaints.json
│       ├── businesses.json
│       └── districts.json
│
├── scripts/
│   ├── seed_database.py
│   ├── seed_districts.py
│   ├── seed_staff.py
│   ├── ingest_documents.py
│   ├── create_admin.py
│   └── create_staff.py
│
├── nginx/
│   ├── nginx.conf
│   └── Dockerfile
│
└── .github/
    └── workflows/
        ├── frontend-ci.yml
        ├── backend-ci.yml
        └── deploy.yml
```

---

## Build Status Note

The tree above is updated through Phase 9 (Investigation Agent) for the
`backend/app/` subtree specifically, since that is what recent phases
actually touch. A few items shown are still aspirational rather than built
yet:

- `data/`, `scripts/`, `nginx/`, and `.github/` do not exist in the
  repository yet.
- `backend/app/agents/` now contains `complaint_triage/` (Phase 6),
  `evidence_analysis/` (Phase 7), `inspector_assistant/` (Phase 8), and
  `investigation/` (Phase 9) - all plain module functions (`tools.py` +
  `agent.py`) rather than classes, matching the existing agents' style.
  There is still no `orchestrator.py`, `state.py`, or `report_generation/`
  yet (see `docs/DEVELOPMENT_ROADMAP.md` for when those are planned).
- `backend/app/rag/` now exists (`parsing.py`, `chunking.py`, `ingestion.py`,
  `retrieval.py`). `backend/app/tools/` still does not exist - each
  tool-using agent keeps its own `tools.py` (`app/agents/inspector_assistant/
  tools.py`, `app/agents/investigation/tools.py`) rather than sharing one
  top-level tools module, since the tool sets barely overlap and each is
  already scoped by the agent that owns it.
- RAG tables now exist as `rag_documents`/`rag_document_chunks`
  (`app/models/rag_document.py`, `app/models/rag_document_chunk.py`), plus
  `assistant_conversations`/`assistant_messages`
  (`app/models/assistant_conversation.py`, `app/models/assistant_message.py`)
  for Inspector Assistant conversation state, and `investigation_briefs`
  (`app/models/investigation_brief.py`) for the Investigation Agent's
  advisory result (Phase 9, single-shot and cacheable like
  `evidence_analysis_results`, not a conversation). Phase 10 adds
  `notifications` (`app/models/notification.py`) - unlike the AI advisory
  result tables above, this is written directly by the domain services
  (`complaint_service`, `assignment_service`) that trigger each workflow
  event, not by an agent. Phase 10 does not add any new persistent table for
  analytics or the audit trail - `analytics_repository` aggregates the
  existing operational tables on read, and `audit_logs` (already created in
  Phase 4) only gained two extra indexes and a `list_logs()` reader.
- On the frontend, the actual AI-facing components are
  `frontend/src/components/agent/ComplaintTriagePanel.jsx`,
  `EvidenceAnalysisPanel.jsx`, `AssistantChat.jsx`, and
  `InvestigationBriefPanel.jsx` (Phase 9) - not the generic
  `AgentChat.jsx`/`AgentResponse.jsx`/`SourceCitation.jsx` names shown in the
  aspirational frontend tree above. The Investigation Agent has no dedicated
  page; it renders inline on `pages/officer/ComplaintReview.jsx` alongside
  the triage/evidence panels, since it is scoped to one complaint being
  reviewed rather than a standalone workflow.
- Phase 10 adds `frontend/src/pages/shared/Notifications.jsx` - a role-
  agnostic inbox page (not under `pages/citizen|officer|inspector|admin/`,
  since every role has one) - and `frontend/src/pages/admin/AuditLogs.jsx`,
  plus `services/notificationService.js`, `services/analyticsService.js`,
  and `services/auditLogService.js`. District/statewide KPIs render inline
  on the existing `OfficerDashboard.jsx`/`AdminDashboard.jsx`.
- **Phase 11** rebuilt the frontend on Tailwind CSS v4 (the `@tailwindcss/vite`
  plugin, added to `frontend/vite.config.js`; design tokens - `brand`/
  `accent`/`priority` colors - live in a `@theme` block in
  `frontend/src/index.css`, replacing the old hand-written `App.css`/
  `index.css`). A real design system now lives at `frontend/src/components/
  ui/` (`Button`, `IconButton`, `Input`, `Select`, `Textarea`, `Checkbox`,
  `FormField`, `Card`, `Badge`, `Table`, `Alert`, `Modal`, `Drawer`, `Tabs`,
  `Breadcrumbs`, `Pagination`, `Tooltip`, `Skeleton`, `EmptyState`,
  `ErrorState`, `ConfirmDialog`, `Spinner`, `StatTile`, `DetailGrid`,
  `DetailsList` - `Modal`/`Drawer` are built on the native `<dialog>` element
  rather than a dialog library) instead of the aspirational
  `components/common/` shown above, plus `frontend/src/components/charts/`
  (`CategoryBarChart`, `TrendLineChart`, `WorkloadBarChart` - thin Recharts
  wrappers, the one new runtime dependency this phase added alongside `clsx`
  and `lucide-react`) replacing the aspirational `components/dashboard/
  *Chart.jsx` files. `frontend/src/components/layout/` gained `AppShell.jsx`
  (persistent sidebar + topbar for every authenticated route, collapsing into
  a `Drawer` on mobile), `Sidebar.jsx`, `Topbar.jsx`, `PublicLayout.jsx` (the
  lighter header/footer chrome for `/`, `/login`, `/register`),
  `PageHeader.jsx`, and `ContentContainer.jsx`, alongside the existing
  `Navbar.jsx`/`Footer.jsx`. `frontend/src/routes/AppRoutes.jsx` now nests
  routes under these two layouts as React Router layout routes;
  `ProtectedRoute.jsx`/`RoleRoute.jsx` themselves were not changed. New
  `frontend/src/utils/statusConfig.js` (canonical status/priority/role/etc.
  value-label-tone tables, superseding the inline lists that used to be
  duplicated per page) and `utils/formatters.js` (date/number formatting via
  native `Intl`) were added; `utils/complaintStatus.js` and
  `utils/permissions.js` were kept and extended rather than replaced.
  Three admin pages that had backend endpoints but no UI before this phase
  were built: `pages/admin/StaffManagement.jsx`, `pages/admin/
  Businesses.jsx` (read-only - there is no business create/edit endpoint,
  businesses are created only through citizen complaint submission), and
  `pages/admin/RagDocuments.jsx`, backed by three new services
  (`services/staffService.js`, `services/businessService.js`,
  `services/ragDocumentService.js`). `pages/public/NotFound.jsx` was added
  for the `*` route. No backend files, API contracts, or database schema
  changed in this phase.
- **Phase 12** (security/performance/reliability hardening - see
  `docs/SECURITY_AND_RBAC.md` section 18 and `docs/DEVELOPMENT_ROADMAP.md`
  Phase 12 for the full findings/fixes list) added two new `backend/app/`
  modules not in the aspirational tree above: `core/rate_limit.py` (in-memory
  per-IP rate limiting, applied to `/auth/login`, `/auth/register`,
  `/auth/refresh`, `POST /complaints`) and `utils/uploads.py`
  (bounded-memory multipart file reading). `utils/validators.py` gained
  file-content magic-byte sniffing and filename sanitization.
  `alembic/versions/a1b2c3d4e5f6_add_assignment_complaint_unique_constraint.py`
  adds a unique constraint on `assignments.complaint_id`. New tests:
  `app/tests/integration/test_hardening.py`,
  `app/tests/unit/test_evidence_analysis_repository.py`. No new top-level
  directories, no frontend changes, and no API contract/schema changes
  beyond the `assignments.complaint_id` constraint above.
- **Phase 12 follow-up** (server-side refresh-token sessions - see
  `docs/SECURITY_AND_RBAC.md` section 19) added
  `app/models/refresh_session.py` (`RefreshSession`),
  `app/repositories/refresh_session_repository.py`,
  `alembic/versions/b2c3d4e5f6a7_add_refresh_sessions.py`, and reworked
  `app/services/auth_service.py`'s login/refresh/logout flow plus
  `app/core/security.py` (opaque refresh tokens replace JWT refresh tokens;
  access tokens gained a `sid` claim) and `app/core/dependencies.py`
  (`get_current_session_id`). `app/api/admin/router.py`'s
  `update_user_status` now revokes a deactivated user's sessions. New
  tests: `app/tests/unit/test_refresh_session_repository.py`,
  `app/tests/integration/test_refresh_sessions.py`,
  `frontend/src/store/authStore.test.jsx`. The only frontend change was
  persisting the rotated refresh token in `store/authStore.jsx` after a
  silent refresh - no other frontend files changed, no UI changes, and
  `/auth/*` request/response shapes are unchanged. A second follow-up
  (`docs/SECURITY_AND_RBAC.md` section 20) added the retention/cleanup
  policy for that table: `scripts/cleanup_refresh_sessions.py` (a
  standalone script, matching the existing `scripts/create_admin.py` /
  `scripts/seed_districts.py` convention - not an API endpoint), backed by
  `auth_service.cleanup_expired_and_revoked_sessions` /
  `count_sessions_eligible_for_cleanup` and new
  `refresh_session_repository` functions
  (`count_eligible_for_cleanup`, `delete_expired_and_revoked_batch`). No
  new top-level directories, no scheduler/Celery/Redis dependency added -
  the script is intended to be invoked by cron/Task
  Scheduler/scheduled-CI, external to the application process. New tests:
  `app/tests/unit/test_refresh_session_cleanup.py`.

- **Phase 13** (Render demo deployment - see `docs/DEPLOYMENT.md` and
  `docs/DEVELOPMENT_ROADMAP.md` Phase 13) added `render.yaml` at the
  repository root (a Render Blueprint provisioning `food-safety-backend`, a
  Web Service, and `food-safety-frontend`, a Static Site, both Free Tier,
  neither Docker-based) and `.github/workflows/cleanup-refresh-sessions.yml`
  (a scheduled GitHub Actions workflow running
  `scripts/cleanup_refresh_sessions.py` daily, since Render's Cron Job
  service type is a paid feature - see `docs/SECURITY_AND_RBAC.md` section
  20.4). This is the only file under `.github/workflows/` that actually
  exists; the aspirational tree above also shows `frontend-ci.yml` and
  `backend-ci.yml`, which were not built in this phase (no CI test gate
  currently runs on push - see `docs/DEPLOYMENT.md` section 11's known
  limitations) - `deploy.yml` doesn't exist either, since deployment is
  handled by Render's own Git-triggered builds via `render.yaml`, not a
  GitHub Actions deploy step. `Backend/.env.example` gained one line,
  `RAG_STORAGE_BUCKET` - an existing `Settings` field
  (`app/core/config.py`) that was already read by
  `app/services/rag_document_service.py` but not documented alongside its
  sibling `SUPABASE_STORAGE_BUCKET`. No backend or frontend application
  code changed - this phase is deployment configuration and documentation
  only (`docs/DEPLOYMENT.md`, new).

Update this note (or remove it once the tree is fully current again) the
next time a phase changes backend or frontend structure.

---

## Architectural Boundaries

### Frontend

Responsible for UI, dashboards, map visualization, uploads, client-side validation, and API communication.

Frontend permissions are for UX only. They are not the security boundary.

### Backend

Responsible for authentication, authorization, district isolation, business rules, complaint lifecycle, inspection workflow, agent orchestration, validation, database access, and audit logging.

### Database

Supabase provides hosted PostgreSQL.

Use:

- SQLAlchemy for ORM/database access
- Alembic for migrations
- PostGIS for geographical operations
- pgvector for RAG vectors when appropriate

### Storage

Supabase Storage should hold complaint and inspection media and generated reports. PostgreSQL should store metadata and references.

### AI

Agents should use controlled tools. They must not bypass authorization or execute arbitrary SQL.

### RAG

RAG handles official regulations, inspection guidance, sampling procedures, and department SOPs. It remains separate from transactional complaint data.

---

## Maharashtra Access Model

```text
Maharashtra
└── Division
    └── District
        ├── District Officer
        ├── Inspectors
        ├── Businesses
        └── Complaints
```

The system should support the project's configured Maharashtra divisions and 36 districts.

Use database relationships for district-specific behavior. Do not create separate code paths for individual districts.

---

## Core Data Flow

```text
Citizen
  ↓
React
  ↓
FastAPI
  ↓
Authentication / RBAC
  ↓
Complaint Service
  ↓
District Resolution
  ↓
SQLAlchemy
  ↓
Supabase PostgreSQL
  ↓
Triage / Evidence AI
  ↓
Officer Review
  ↓
Inspector Assignment
  ↓
Inspection
  ↓
Resolution
```

Inspector Assistant:

```text
Inspector
  ↓
Assistant UI
  ↓
Agent API
  ↓
Inspector Assistant
  ├── Authorized complaint tools
  ├── Inspection tools
  └── RAG tool
          ↓
      pgvector
          ↓
 Official documents
          ↓
 Answer + citations
```

---

## Claude Code Rules

1. Read the relevant `docs/` files before making architectural changes.
2. Preserve existing module boundaries unless a documented reason exists.
3. Use SQLAlchemy models and Alembic migrations for schema changes.
4. Enforce authorization on the backend.
5. Enforce district isolation in backend services and agent tools.
6. Never give agents arbitrary SQL access.
7. Keep AI advisory unless a human-controlled workflow approves an action.
8. Add tests for new business logic and permission boundaries.
9. Update architecture documentation when major architecture changes.
10. Avoid unnecessary dependencies and duplicate abstractions.
11. Never create separate implementations for individual districts.
12. Keep RAG retrieval separate from transactional complaint data.
13. Keep secrets and runtime artifacts out of Git.
14. Prefer small, reviewable changes over large rewrites.

---

## Source of Truth Priority

When documentation conflicts, prefer:

```text
1. PROJECT_SPEC.md
2. SECURITY_AND_RBAC.md
3. DATABASE_SCHEMA.md
4. SYSTEM_ARCHITECTURE.md
5. API_ARCHITECTURE.md
6. AI_AGENTS_ARCHITECTURE.md
7. RAG_ARCHITECTURE.md
8. DEVELOPMENT_ROADMAP.md
9. ARCHITECTURE_TREE.md
```

Resolve architectural conflicts before implementing them.

---

## Naming Conventions

### Frontend

- Components: `PascalCase.jsx`
- Hooks: `useSomething.js`
- Services: `somethingService.js`
- Stores: `somethingStore.js`

### Backend

- Modules/files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Pydantic schemas: descriptive `PascalCase` names such as `ComplaintCreate`, `ComplaintRead`

### Database

- Tables: `snake_case`
- Columns: `snake_case`
- Foreign keys: `<entity>_id`
- Timestamps: `created_at`, `updated_at`

---

## Architecture Change Rule

Update this document when adding a new:

- top-level directory
- architectural layer
- persistent subsystem
- agent
- data domain
- infrastructure component

Do not create folders only to satisfy an individual feature without architectural justification.
