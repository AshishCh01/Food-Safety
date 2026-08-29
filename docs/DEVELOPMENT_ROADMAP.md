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
- local development environment
- health endpoint
- base logging/configuration
- baseline tests

Completion:

```text
frontend -> runs
backend -> runs
backend -> database connection works
alembic -> migration works
frontend/backend local services -> start successfully
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

## 16. Phase 13 — Render Demo Deployment and Production Readiness

Deployment target:

- Render Free Tier for the frontend and backend demo services
- No Docker or Docker Compose required for this deployment
- Supabase remains the managed PostgreSQL/Storage/PostGIS/pgvector platform
- Gemini API remains the external AI provider

Build/prepare:

- Render Static Site configuration for the React/Vite frontend
- Render Web Service configuration for the FastAPI backend
- native Render build/start commands (no Dockerfiles required for deployment)
- production environment variables and secret handling
- production CORS configuration
- Supabase database migration process using Alembic
- Supabase Storage configuration and private-bucket access
- Gemini API configuration
- health/readiness checks suitable for Render
- structured logging and useful runtime diagnostics
- frontend/backend API routing and deployment configuration
- refresh-session cleanup script scheduling strategy compatible with the demo deployment
- deployment documentation and smoke-test checklist

Constraints:

- Do not introduce Redis for the demo deployment.
- Keep the current in-memory rate limiter and document that it is single-process.
- Do not introduce AWS/GCP-specific infrastructure.
- Docker is optional for local experimentation but is not part of the target Render deployment.

Completion:

The application can be deployed reproducibly to Render Free Tier from the repository using native build/start commands, connects securely to Supabase and Gemini, applies Alembic migrations correctly, and passes a documented production smoke test.

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
✅ Phase 13 Render Demo Deployment and Production Readiness
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
10 in 2), re-verified against the full test suite. `npm audit` found 0
vulnerabilities in frontend production dependencies; 5 (1 critical) exist
only in `vitest`'s transitive dev-tooling chain (`esbuild`/`vite`, a
dev-server-only issue), not shipped in the production build.

**Follow-up (same day):** the remaining `starlette` CVE chain (10
vulnerabilities, pinned transitively by `fastapi==0.115.6`'s
`starlette<0.42.0` constraint) was resolved by upgrading `fastapi` to
0.141.1, which pulls `starlette` 1.6.0 - `pip-audit` now shows only the
pre-existing dev-only `pytest` finding. No application code changes were
required; the full 327-test backend suite, `pip check`, OpenAPI/`/docs`
generation, and a module-import sweep (Supabase Storage, PostGIS, pgvector,
Gemini, all four AI agents) all passed unchanged against the upgraded
stack. `pydantic==2.10.4` and `python-multipart==0.0.32` already satisfied
the new `fastapi`'s minimum constraints, so neither needed to move.
`starlette` itself is intentionally left unpinned in `requirements.txt`,
inherited from `fastapi`'s own dependency spec, per this project's
"upgrade fastapi, let it determine starlette" policy - see
`docs/SECURITY_AND_RBAC.md` section 18 for the updated finding.

No product features, UI redesign, or API contract changes were made in this
phase, per the phase's own scope.

**Follow-up (same week): server-side refresh-token sessions.** The last
remaining authentication risk from section 18's findings - stateless
refresh tokens with no server-side revocation - was fixed. Refresh tokens
are now opaque, SHA-256-hashed, database-backed sessions
(`refresh_sessions` table, `app/models/refresh_session.py`,
`alembic/versions/b2c3d4e5f6a7_add_refresh_sessions.py`) using the existing
Supabase PostgreSQL database - no Redis or other external store, per the
task's constraint. Refresh tokens rotate on every use, with reuse detection
that distinguishes benign concurrent refresh (e.g. multiple tabs) from
replay of a stale token (revokes the whole session lineage); logout and
admin account deactivation both revoke sessions server-side immediately.
Access tokens are unchanged: still short-lived, stateless JWTs, now
carrying a `sid` claim so logout can resolve the right session without a
request body. Full design in `docs/SECURITY_AND_RBAC.md` section 19 and
`docs/DATABASE_SCHEMA.md` section 4 (`refresh_sessions`).

The only required frontend change was persisting the *rotated* refresh
token after a silent refresh in `AuthProvider`
(`frontend/src/store/authStore.jsx`) - previously only the new access token
was saved, which would have made the next refresh attempt present an
already-revoked token and force an unnecessary logout. `POST /auth/logout`
needed no frontend change, since session revocation is resolved entirely
from the access token already sent.

Existing `/auth/login`, `/auth/refresh`, `/auth/logout` request/response
shapes are unchanged - this was a server-side and storage-layer change, not
an API contract change. New tests:
`app/tests/unit/test_refresh_session_repository.py`,
`app/tests/integration/test_refresh_sessions.py`,
`frontend/src/store/authStore.test.jsx`, plus additions to
`app/tests/unit/test_security.py` (opaque token generation/hashing, the new
`sid` claim). Full backend suite: 348 passing (up from 327). Frontend: 60
passing (up from 58), `oxlint` clean, production build clean. `pip check`
and `pip-audit` unchanged (no new dependencies introduced).

**Follow-up (same week): refresh-session maintenance.** The
`refresh_sessions` cleanup gap noted above was closed. Added a two-tier
retention policy (`Settings.refresh_session_retention_days` = 7 days for
expired/routinely-revoked rows, `refresh_session_reuse_detected_retention_days`
= 90 days for `reuse_detected` rows, since those carry the most
incident-investigation value) and `scripts/cleanup_refresh_sessions.py` - a
standalone script following the existing `scripts/create_admin.py` /
`scripts/seed_districts.py` convention, run via cron/Task
Scheduler/scheduled CI (no Redis, no Celery, no in-process scheduler added).
It only ever deletes rows that are already permanently unusable and past
their retention window, deletes in batches with a commit between each to
avoid long-held locks on a live database, handles the table's
self-referential FK explicitly rather than depending on `ON DELETE SET
NULL` enforcement, and supports `--dry-run`. Full policy and safety
reasoning in `docs/SECURITY_AND_RBAC.md` section 20 (new), with a pointer
from `docs/DATABASE_SCHEMA.md`'s `refresh_sessions` entry. New tests:
`app/tests/unit/test_refresh_session_cleanup.py` (10 tests: live sessions
never touched, per-reason retention windows including the extended
`reuse_detected` tier, batching/resumability, the self-referential-FK
nulling, and service-level looping). Full backend suite: 358 passing (up
from 348); no frontend changes were needed. No new dependencies - `pip
check` and `pip-audit` unaffected.

**Phase 13** prepared the application for a reproducible Render Free Tier
demo deployment - configuration and documentation only, no product features
and no application code changes. Added `render.yaml` (repository root), a
Render Blueprint provisioning `food-safety-backend` (a native-Python Web
Service - no Dockerfile involved in the deploy path) and `food-safety-frontend`
(a Static Site built from the Vite production build, with the `/* ->
/index.html` rewrite rule the client-side-routed SPA needs so deep links and
hard refreshes don't 404). Alembic migrations run via `alembic upgrade head`
chained into the start command rather than as a Render "pre-deploy command",
since that feature requires a paid plan; `alembic upgrade head` is idempotent
so re-running it on every boot is safe.

Added `.github/workflows/cleanup-refresh-sessions.yml`, a scheduled (daily)
GitHub Actions workflow that runs the existing
`scripts/cleanup_refresh_sessions.py` against the production database -
Render's own Cron Job service type is a paid feature, so this was the
lowest-friction way to keep the Phase 12 refresh-session cleanup task
scheduled without introducing Redis, Celery, or any always-on process (see
`docs/SECURITY_AND_RBAC.md` section 20.4).

Reviewed `Backend/.env.example` against `app/core/config.py` and found one
real gap: `RAG_STORAGE_BUCKET` was already a live setting (read by
`app/services/rag_document_service.py`) but undocumented alongside its
sibling `SUPABASE_STORAGE_BUCKET` - added the one missing line. Verified
(without code changes) that CORS origins, the `/health` endpoint's database
check, the global JSON error envelope, `$PORT`-based startup, and
Supabase/Gemini connectivity are all already environment-driven with no
hard-coded deployment-specific values, and that no secret is ever exposed to
the frontend bundle (`VITE_API_URL` is the only frontend env var; the
Supabase service-role key and Gemini key remain backend-only `SecretStr`
values per the Phase 12 hardening work).

New `docs/DEPLOYMENT.md` is the full walkthrough: prerequisites, the
Blueprint vs. manual setup paths, a complete environment-variable reference
per service, Supabase/PostGIS/pgvector setup, the two required private
Storage buckets, the refresh-session cleanup workflow, a production baseline
checklist, and a smoke-test checklist (backend health/auth, frontend SPA
routing/auth/refresh-rotation/logout/RBAC/responsive behavior, and a full
citizen-to-resolution workflow exercising both AI agents and the RAG
Inspector Assistant end-to-end against the deployed services).
`docs/SYSTEM_ARCHITECTURE.md` section 14 and `docs/SECURITY_AND_RBAC.md`
section 20.4 were updated to point at the concrete files instead of
describing the deployment only in the abstract; `docs/ARCHITECTURE_TREE.md`
gained a matching Build Status Note entry.

Verified via the existing test suites (no application code changed): full
backend `pytest` (358 passing) and a production `npm run build` (clean,
`dist/` output matching `render.yaml`'s `staticPublishPath`). Deployment
itself (creating the actual Render/Supabase/GitHub resources and running the
smoke-test checklist against them) requires live account access this
environment does not have, and is the next action for whoever operates the
Render/Supabase/GitHub accounts, following `docs/DEPLOYMENT.md` directly.
