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
│       │   ├── agent.py           # ComplaintTriageRead, EvidenceAnalysisRead
│       │   └── common.py
│       │
│       ├── api/
│       │   ├── router.py
│       │   ├── health.py
│       │   ├── businesses.py
│       │   ├── reference.py
│       │   ├── auth/
│       │   ├── citizen/
│       │   ├── officer/           # includes /triage and /evidence/{id}/analysis endpoints
│       │   ├── inspector/         # includes /evidence/{id}/analysis endpoints
│       │   └── admin/
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
│       │   └── ai_service.py          # centralized Gemini text/structured/multimodal wrapper
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
│       │   └── audit_log_repository.py
│       │
│       ├── agents/
│       │   ├── complaint_triage/
│       │   │   └── agent.py       # Phase 6 - module functions, not a class
│       │   └── evidence_analysis/
│       │       └── agent.py       # Phase 7 - module functions, not a class
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

The tree above is updated through Phase 7 (Evidence Analysis Agent) for the
`backend/app/` subtree specifically, since that is what recent phases
actually touch. A few items shown are still aspirational rather than built
yet:

- `data/`, `scripts/`, `nginx/`, and `.github/` do not exist in the
  repository yet.
- `backend/app/agents/` currently contains only `complaint_triage/` (Phase 6)
  and `evidence_analysis/` (Phase 7), each as plain module functions - there
  is no `orchestrator.py`, `state.py`, `investigation/`,
  `inspector_assistant/`, or `report_generation/` yet (see
  `docs/DEVELOPMENT_ROADMAP.md` for when those are planned).
- `backend/app/rag/` and `backend/app/tools/` do not exist yet (Phase 8+).
- `notifications`/`document`/`document_chunk` models do not exist yet.

Update this note (or remove it once the tree is fully current again) the
next time a phase changes backend structure.

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
