# Development Roadmap

> **Phase numbering note:** this document's phase numbers (below, from Phase
> 6 onward) diverge from `docs/PROJECT_SPEC.md` section 30, which is what was
> actually built: PROJECT_SPEC orders Complaint Triage as Phase 6 and
> Evidence Analysis as Phase 7, both ahead of RAG (Phase 8) and Investigation
> (Phase 9); this document instead orders RAG (6) and Inspector Assistant (7)
> ahead of Triage (8) and Evidence (9). `docs/ARCHITECTURE_TREE.md`'s own
> source-of-truth priority list ranks `PROJECT_SPEC.md` above this document,
> and the codebase has followed PROJECT_SPEC's ordering (Complaint Triage and
> Evidence Analysis are already built, ahead of RAG). Treat PROJECT_SPEC.md's
> phase order as authoritative for phases 6+; the section headings below are
> left as originally written rather than renumbered.

## 1. Goal

Build the Maharashtra Food Safety Complaint and Inspection Platform incrementally using Claude Code in VS Code, with every phase producing a working and testable increment.

## 2. Working Method

For every phase:

1. Read the project specification and relevant architecture docs.
2. Inspect the current codebase before changing it.
3. Implement only the defined phase scope.
4. Run lint/type checks/tests.
5. Review the git diff.
6. Update relevant documentation.
7. Commit the phase in git.

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

## 5. Phase 2 — Authentication and RBAC

Build:

- citizen registration/login
- staff login
- roles: citizen, inspector, district officer, admin
- protected routes
- backend role authorization
- staff provisioning
- district scope enforcement

Seed:

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
- complaint timeline
- status workflow
- citizen dashboard

Completion:

A citizen can create a complaint and track it from submission onward.

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
- report draft
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
- complaint markers
- district filtering
- location-based business lookup
- district derivation/validation from coordinates where feasible

Completion:

District officers see only their district on operational maps while admins can view statewide data.

## 9. Phase 6 — RAG Foundation

Build:

- approved source document storage
- parsing
- chunking
- metadata extraction
- embeddings
- pgvector tables/indexing
- retrieval API/service
- citation metadata

Start with a small high-quality corpus.

Completion:

A benchmark set of inspector questions retrieves relevant source passages with correct citations.

## 10. Phase 7 — Inspector Assistant Agent

Build:

- agent orchestrator
- Inspector Assistant
- controlled tools
- RAG integration
- complaint/inspection context retrieval
- structured responses
- citations
- human-review guardrails

Completion:

Inspector can ask a question and receive an answer grounded in approved sources and authorized case data.

## 11. Phase 8 — Complaint Triage Agent

Build:

- complaint classification
- summary generation
- entity extraction
- missing-information detection
- priority suggestion
- structured output validation

Completion:

Representative complaint test set achieves acceptable classification/extraction accuracy.

## 12. Phase 9 — Evidence Analysis Agent

Build:

- OCR
- image/vision analysis
- expiry-date extraction
- evidence summarization
- analysis metadata
- asynchronous processing

Completion:

System can analyze supported evidence types and clearly distinguish observations from confirmed findings.

## 13. Phase 10 — Investigation Agent

Build:

- controlled investigation tools
- complaint history analysis
- business history
- inspection history
- duplicate complaint detection
- investigation brief generation

Completion:

An officer can generate an investigation brief using only authorized district data.

## 14. Phase 11 — Analytics and Notifications

Build:

- district KPIs
- complaint trends
- category distribution
- resolution time metrics
- inspector workload
- notifications
- admin statewide analytics

Completion:

Dashboards show reproducible metrics sourced from the operational database.

## 15. Phase 12 — Security, Testing, and Hardening

Build/test:

- RBAC tests
- cross-district security tests
- file upload tests
- API validation tests
- agent tool authorization tests
- prompt injection tests
- performance checks
- dependency/security scans

Completion:

Critical security tests pass and no known privileged secrets are committed.

## 16. Phase 13 — Deployment

Build:

- production Docker images
- environment configuration
- CI/CD
- HTTPS
- database migration deployment process
- logging/monitoring
- backup/recovery plan

Completion:

The application can be deployed reproducibly from a clean environment.

## 17. Git Strategy

Use feature branches and small commits.

Example:

```text
phase-1-foundation
phase-2-auth-rbac
phase-3-complaints
phase-4-inspections
phase-5-maps
phase-6-rag
phase-7-inspector-agent
...
```

Avoid large unreviewed commits generated by a single AI session.

## 18. Claude Code Prompt Pattern

Each implementation prompt should include:

```text
Read:
- docs/PROJECT_SPEC.md
- docs/SYSTEM_ARCHITECTURE.md
- relevant phase documentation

Task:
Implement only Phase X.

Constraints:
- preserve existing architecture
- do not modify unrelated modules
- follow SQLAlchemy/Alembic rules
- enforce RBAC server-side
- add tests

Validation:
- run tests
- run lint/type checks
- report files changed
- report any unresolved issues
```

## 19. Definition of Done

A phase is complete only when:

- feature works end-to-end
- backend authorization is tested
- database migrations are reviewed
- frontend states are handled
- tests pass
- documentation is updated
- no unrelated unfinished changes remain
