# Development Roadmap

## 1. Goal

Build the Maharashtra Food Safety Complaint and Inspection Platform incrementally using Claude Code in VS Code, with every phase producing a working and testable increment.

The roadmap reflects the actual implementation order used by the project. `PROJECT_SPEC.md` remains the primary product specification; this document defines the practical development sequence.

## 2. Working Method

For every phase:

1. Read the project specification and relevant architecture docs.
2. Inspect the current codebase before changing it.
3. Implement the defined phase scope while preserving the existing architecture.
4. Run relevant tests, lint, build, and migration checks.
5. Review the git diff.
6. Update relevant documentation.
7. Commit the completed phase in git.

Do not ask Claude Code to implement the whole project in one prompt.

## 3. Phase 0 — Specification and Repository Setup

Deliverables:

- repository structure
- `CLAUDE.md`
- project specification
- architecture documents
- environment variable template
- Git workflow

Completion:

- docs are internally consistent
- architecture is agreed before major coding

## 4. Phase 1 — Backend and Frontend Foundation

Build:

- React/Vite frontend
- FastAPI backend
- SQLAlchemy configuration
- Alembic configuration
- Supabase PostgreSQL connection
- Docker development environment
- health endpoint
- base logging/configuration
- baseline tests

Completion:

```text
frontend -> runs
backend -> runs
backend -> database connection works
alembic -> migration works
Docker -> services start successfully
```

## 5. Phase 2 — Authentication, RBAC, and Maharashtra District Structure

Build:

- citizen registration/login
- staff login
- roles: citizen, inspector, district officer, admin
- protected routes
- backend role authorization
- staff provisioning
- district scope enforcement

Seed/configure:

- six divisions
- 36 districts
- one district officer per district for the initial environment
- at least one inspector per district for demo/testing

Completion:

- cross-district authorization tests pass
- citizens cannot access staff dashboards
- staff cannot self-escalate roles

## 6. Phase 3 — Core Complaint Management

Build:

- business records
- complaint categories
- complaint creation
- complaint numbers
- evidence metadata
- Supabase Storage evidence pipeline
- complaint timeline
- status workflow
- citizen dashboard
- reusable centralized Gemini AI service foundation

Completion:

A citizen can create a complaint, attach evidence, and track it from submission onward.

## 7. Phase 4 — Officer and Inspector Operations

Build:

- officer dashboard
- district complaint queue
- complaint review
- verification/rejection
- inspector assignment
- inspector dashboard
- inspection records
- findings
- inspection evidence
- inspection lifecycle
- audit history

Completion:

A complaint can move through the full manual workflow:

```text
Submitted -> Review -> Verified -> Assigned -> Inspection -> Resolution
```

## 8. Phase 5 — Maps and Geographic Intelligence

Build:

- PostGIS support
- Leaflet map
- OpenStreetMap integration
- complaint markers
- district filtering
- location-based business/complaint lookup
- incident location selection
- reverse geocoding where appropriate
- district derivation/validation from coordinates

Current implementation note:

- The current district resolver uses nearest district centroid approximation where real district polygons are not yet available.
- The long-term GIS improvement is point-in-polygon resolution using authoritative Maharashtra district boundary data and PostGIS `ST_Contains` or equivalent.

Completion:

District officers see only their district on operational maps while admins can view statewide data, and location-aware complaints can be created and queried.

## 9. Phase 6 — Complaint Triage Agent

Build:

- complaint classification using the existing database taxonomy
- summary generation
- business/product entity extraction
- missing-information detection
- priority/severity suggestion
- structured Gemini output validation
- AI uncertainty handling
- retry/error normalization
- persisted triage results separate from the original complaint
- officer-facing triage result

Completion:

A representative complaint can be analyzed into a validated advisory triage result without changing the original citizen complaint or official workflow state.

## 10. Phase 7 — Evidence Analysis Agent

Build:

- multimodal Gemini analysis
- OCR/text extraction from supported evidence
- product/manufacturer/batch/date extraction where visible
- expiry/best-before extraction
- packaging and hygiene observations
- confidence/uncertainty
- deterministic possible-expiry evaluation from extracted date data
- persisted evidence-analysis results separate from raw evidence
- officer/inspector-facing evidence analysis

Completion:

The system can analyze supported evidence types and clearly distinguish AI observations from confirmed findings.

## 11. Phase 8 — RAG and Inspector Assistant

Build:

- approved source document storage
- parsing
- heading-aware/page-aware chunking
- metadata extraction
- Gemini embeddings
- pgvector tables and indexing
- vector retrieval
- source/page/section citation tracking
- Inspector Assistant
- controlled application-data tools
- case-scoped and general assistant conversations
- citation validation
- human-review guardrails

Knowledge base should initially focus on a small, high-quality corpus such as:

- FSSAI laws and regulations
- hygiene and inspection guidance
- sampling procedures
- recall procedures
- licensing/registration requirements
- approved department SOPs

Completion:

An authorized inspector can ask a question and receive an answer grounded in approved sources and authorized case data with valid citations.

## 12. Phase 9 — Investigation Agent

Build:

- controlled investigation tools
- complaint history analysis
- business history
- inspection history
- current evidence/evidence-analysis context
- complaint triage context
- relevant regulatory guidance retrieval
- investigation brief generation
- uncertainty and missing-information handling
- cached investigation results and explicit re-investigation

Completion:

A district officer can generate an investigation brief using only authorized district data and retrieved authoritative guidance.

## 13. Phase 10 — Operational Intelligence, Notifications, and Audit

Build:

- district KPIs
- complaint trends
- category distribution
- resolution-time metrics
- inspector workload
- business complaint-history views
- statewide admin analytics
- notification events and delivery handling
- useful audit-log views and filters

Analytics should be derived from operational data with reproducible queries. AI should not be required for basic reporting metrics.

Completion:

District officers and admins can monitor operational performance, workload, complaint trends, and important workflow events from reproducible database-backed metrics.

## 14. Phase 11 — UI/UX and Design System Refinement

Build/refine:

- consistent design system across citizen, officer, inspector, and admin areas
- typography hierarchy
- spacing and layout system
- navigation and responsive behavior
- form controls
- tables and filters
- status/priority indicators
- map presentation
- loading, empty, success, and error states
- accessibility and contrast
- mobile/responsive behavior
- visual consistency across AI features

Design direction:

- modern public-service product
- clean and professional
- restrained color palette
- information-dense officer workflows
- subtle borders and shadows
- purposeful use of cards
- no unnecessary gradients, glassmorphism, glowing effects, oversized hero sections, or repetitive AI-chat styling

AI output should feel integrated into the case-management workflow rather than presented as a generic chatbot unless a conversational assistant is actually appropriate.

Completion:

The application looks and behaves like one coherent product rather than a collection of independently generated screens.

## 15. Phase 12 — Security, Testing, Performance, and Hardening

Build/test:

- RBAC tests
- cross-district security tests
- object/file access tests
- API validation tests
- agent tool authorization tests
- prompt-injection tests
- secret-management checks
- dependency/security scans
- database query/performance checks
- rate-limit handling where required
- error handling and observability improvements

Completion:

Critical security tests pass, privileged secrets are not committed, and major permission boundaries have automated coverage.

## 16. Phase 13 — Deployment and Production Readiness

Build:

- production Docker images
- production environment configuration
- CI/CD
- HTTPS
- database migration deployment process
- structured logging
- monitoring/health checks
- backup/recovery plan
- deployment documentation
- production smoke-test checklist

Completion:

The application can be deployed reproducibly from a clean environment and the production migration/runtime process is documented.

## 17. Git Strategy

Use feature branches and small commits.

Suggested branch sequence:

```text
phase-1-foundation
phase-2-auth-rbac
phase-3-complaints
phase-4-inspections
phase-5-maps
phase-6-complaint-triage
phase-7-evidence-ai
phase-8-rag-inspector-assistant
phase-9-investigation-agent
phase-10-analytics-notifications
phase-11-ui-ux
phase-12-security-hardening
phase-13-deployment
```

Avoid large unreviewed commits generated by a single AI session.

## 18. Claude Code Prompt Pattern

Each implementation prompt should include:

```text
Read:
- CLAUDE.md
- docs/PROJECT_SPEC.md
- relevant architecture documents
- docs/DEVELOPMENT_ROADMAP.md

Task:
Implement only Phase X.

Guidance:
- inspect the existing code first
- preserve existing architecture where practical
- avoid unnecessary restructuring
- follow SQLAlchemy/Alembic rules
- enforce RBAC server-side
- add tests
- update relevant documentation

Validation:
- run tests
- run lint/build/type checks where applicable
- verify migrations
- report files changed
- report unresolved issues
```

## 19. Definition of Done

A phase is complete only when:

- feature works end-to-end for its intended scope
- backend authorization is tested where relevant
- database migrations are reviewed and applied to a real development database when required
- frontend states are handled
- tests pass
- documentation is updated
- no unrelated unfinished changes remain
- known limitations are explicitly recorded

## 20. Current Project Status

As of the current roadmap update:

```text
✅ Phase 0  Specification and Repository Setup
✅ Phase 1  Backend and Frontend Foundation
✅ Phase 2  Authentication, RBAC, and Maharashtra District Structure
✅ Phase 3  Core Complaint Management
✅ Phase 4  Officer and Inspector Operations
✅ Phase 5  Maps and Geographic Intelligence
✅ Phase 6  Complaint Triage Agent
✅ Phase 7  Evidence Analysis Agent
✅ Phase 8  RAG and Inspector Assistant
✅ Phase 9  Investigation Agent
✅ Phase 10 Operational Intelligence, Notifications, and Audit
✅ Phase 11 UI/UX and Design System Refinement
✅ Phase 12 Security, Testing, Performance, and Hardening
⬜ Phase 13 Deployment and Production Readiness
```

Phase 11 delivered a Tailwind CSS v4 design system (`frontend/src/components/ui/`),
a responsive app shell with sidebar/topbar/mobile drawer navigation
(`components/layout/AppShell.jsx`), restrained Recharts-based analytics
visualizations (`components/charts/`), and every existing page rebuilt on
these primitives with consistent loading/empty/error states. It also closed
three frontend integration gaps that had backend endpoints but no UI: admin
staff management, a read-only business directory, and RAG knowledge-base
document management (upload/list/ingest/deactivate) - see
`docs/ARCHITECTURE_TREE.md`'s Build Status Note for the full file list. No
backend behavior, API contracts, or database schema changed. Verified via
the frontend unit/integration test suite (58 passing), `oxlint`, a
production `vite build`, the full backend `pytest` suite (308 passing,
unaffected), and manual browser verification (citizen, admin, and district
officer/inspector flows exercised end-to-end against a running backend at
desktop/tablet/mobile viewport widths).

Phase 12 audited Phases 1-11 as a security/performance review rather than
adding product features. It confirmed the existing authorization
architecture (server-derived district/inspector/citizen scope, no raw SQL,
AI tools taking only pre-scoped objects) was already sound, then fixed real
issues found by the audit:

**Security:** added per-IP rate limiting on `/auth/login`, `/auth/register`,
`/auth/refresh`, and `POST /complaints` (`app/core/rate_limit.py`, in-memory
- see `docs/SECURITY_AND_RBAC.md` section 18 for the multi-worker
limitation); closed a login timing side-channel that let an attacker
distinguish "unknown email" from "wrong password" by response time; hardened
evidence/RAG-document uploads with file-content magic-byte sniffing,
filename sanitization, and bounded-memory reads (`app/utils/validators.py`,
`app/utils/uploads.py`) - previously only the client-supplied `Content-Type`
header was checked, and a raw client filename was interpolated into the
storage key/URL; added a database-level unique constraint on
`assignments.complaint_id` (a race between two concurrent assign-inspector
requests could otherwise create two rows for one complaint and crash later
reads - see `docs/DATABASE_SCHEMA.md` section 14); stopped vendor error text
from Gemini reaching API clients verbatim; switched `gemini_api_key` and
`supabase_service_role_key` to Pydantic `SecretStr`; added a global
exception-handling middleware so every response (including genuine bugs)
uses the same JSON error envelope, ordered correctly relative to
`CORSMiddleware` so error responses still carry CORS headers for the React
frontend (this ordering is a real Starlette subtlety - see the docstring on
`error_handling_middleware` in `app/main.py`); added baseline security
headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`) to
every response. Full findings list, including reviewed-but-not-changed
items (stateless refresh tokens, the statewide business directory), are in
`docs/SECURITY_AND_RBAC.md` section 18.

**Performance:** fixed an N+1 query in the Inspector Assistant's and
Investigation Agent's `get_evidence_analysis` tool (one query per evidence
item on a case, now a single batched query -
`evidence_analysis_repository.get_latest_by_evidence_ids`); added a
process-local cache for RAG query embeddings so a repeated inspector
question doesn't pay for a fresh Gemini embedding call every time
(`app/rag/retrieval.py`); rewrote `analytics_repository.average_resolution_hours`
(hit by every officer/admin dashboard load) to aggregate in SQL on
PostgreSQL instead of pulling every resolved complaint's timestamps into
Python, keeping the existing Python fallback for the SQLite test database;
configured explicit SQLAlchemy connection-pool sizing
(`app/core/database.py`) instead of relying on defaults; switched
`storage_service.py`'s Supabase Storage calls from a fresh `httpx` client
per request to one shared, connection-pooling client.

**Reliability:** the assignment race fix above also covers a reliability
gap (an unhandled `IntegrityError`/500 on the losing request, now a clean
409 via `assignment_service.assign_inspector` catching it).

**Testing:** added `app/tests/integration/test_hardening.py` (rate limiting,
the global error envelope, CORS-on-error, security headers),
`app/tests/unit/test_evidence_analysis_repository.py` (the batched N+1 fix),
and expanded `app/tests/unit/test_evidence_validation.py` (magic-byte
sniffing, filename sanitization, extension/type mismatch) and
`app/tests/integration/test_assignments.py` (the concurrent-assignment race
and the underlying database constraint). Full backend suite: 327 passing
(up from 308). Frontend: 58 passing, `oxlint` clean, production `vite build`
clean - no frontend code changes were needed (token storage in
`localStorage`, JWT bearer auth, and the existing route guards were
reviewed and found to already match the documented architecture; no XSS
sinks such as `dangerouslySetInnerHTML` exist in the codebase).

**Dependencies:** `pip-audit` found 66 known vulnerabilities across 6
backend packages; `pyjwt`, `python-dotenv`, `python-multipart`, and `pypdf`
were bumped to current patched versions (66 vulnerabilities in 6 packages ->
10 in 2), re-verified against the full test suite. Two are left as
documented technical debt rather than force-fixed in this pass: `starlette`
is pinned transitively by `fastapi==0.115.6`'s `starlette<0.42.0` constraint
- fixing it needs a coordinated `fastapi` upgrade spanning ~26 minor
versions (0.115 -> 0.141+) with dedicated regression testing, which is
out of scope for a contained hardening pass; `pytest` is a dev-only tool
never shipped to production. `npm audit` found 0 vulnerabilities in
frontend production dependencies; 5 (1 critical) exist only in `vitest`'s
transitive dev-tooling chain (`esbuild`/`vite`, a dev-server-only issue),
not shipped in the production build.

No product features, UI redesign, or API contract changes were made in this
phase, per the phase's own scope.

The next implementation phase is **Phase 13**.
