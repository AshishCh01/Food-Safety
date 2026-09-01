# System Architecture

## 1. Purpose

This document defines the technical architecture for the Maharashtra Food Safety Complaint and Inspection Platform.

The system supports citizens submitting food-safety complaints and department staff reviewing, investigating, inspecting, and resolving those complaints. AI agents provide assistance for triage, evidence analysis, investigation, and inspector support.

## 2. Architecture Principles

- API-first architecture.
- Frontend and backend are independently deployable.
- FastAPI is the backend framework.
- PostgreSQL is the system of record.
- SQLAlchemy is the ORM/data-access abstraction.
- Alembic is the schema migration system.
- Supabase provides managed PostgreSQL, Storage, and optional pgvector.
- Server-side RBAC is mandatory.
- District isolation is enforced in backend queries and service/tool layers.
- AI assists staff but does not make final regulatory enforcement decisions.
- Agents access application capabilities through controlled tools, never unrestricted SQL.
- All important state changes are auditable.

## 3. High-Level Architecture

```text
Citizen / Inspector / Officer / Admin
                |
                v
        React Web Application
                |
             HTTPS/REST
                |
                v
             FastAPI
                |
      +---------+----------+
      |                    |
      v                    v
 Business Services      Agent Layer
      |                    |
      |            +-------+--------+
      |            |                |
      v            v                v
 SQLAlchemy   AI Agents          RAG Services
      |            |                |
      +------------+----------------+
                   |
                   v
           Supabase PostgreSQL
            + PostGIS/pgvector
                   |
          +--------+---------+
          |                  |
          v                  v
 Supabase Storage       Audit/Metadata
```

## 4. Frontend Architecture

The frontend uses React and should be organized around role-based applications within one codebase.

### Major areas

- Public pages
- Authentication
- Citizen dashboard
- Inspector dashboard
- District Officer dashboard
- Admin dashboard
- Shared complaint components
- Shared map components
- Shared analytics components
- Inspector Assistant interface

### Frontend responsibilities

- Form validation and user interaction.
- Displaying authenticated role-specific views.
- Uploading evidence through backend-controlled flows.
- Calling backend APIs.
- Rendering complaint status timelines.
- Rendering maps and district-specific complaint markers.
- Showing agent responses and source citations.

The frontend must never be treated as the source of authorization. Hidden buttons/routes are not security controls.

## 5. Backend Architecture

The backend follows a layered structure:

```text
API Route
   -> Authentication / Authorization
   -> Service Layer
   -> Repository / Data Access
   -> SQLAlchemy
   -> PostgreSQL
```

AI flows use:

```text
API Route
   -> Agent Service
   -> Agent Orchestrator
   -> Controlled Tool
   -> Service / Repository / RAG
```

### Core backend modules

- `api/` — HTTP endpoints.
- `core/` — configuration, database, security, logging, dependencies.
- `models/` — SQLAlchemy models.
- `schemas/` — Pydantic request/response schemas.
- `services/` — business logic.
- `repositories/` — data access.
- `agents/` — agent definitions and orchestration.
- `rag/` — ingestion, embeddings, retrieval, reranking.
- `tools/` — safe capabilities exposed to agents.

## 6. Storage Architecture

### PostgreSQL

Use PostgreSQL for:

- Users and roles.
- District hierarchy.
- Businesses.
- Complaints.
- Evidence metadata.
- Assignments.
- Inspections.
- Findings.
- Notifications.
- Audit logs.
- RAG document metadata and chunks.

### Supabase Storage

Use object storage for:

- Complaint photos.
- Complaint videos where supported.
- Inspector evidence.
- Inspection reports.
- Uploaded department documents.

Database records store storage paths/URLs and metadata rather than binary media.

## 7. Geographic Architecture

Use PostGIS for location-aware operations.

Core concepts:

```text
Maharashtra
  -> Division
      -> District
          -> Staff
          -> Businesses
          -> Complaints
```

A complaint should have a geographic point and district association. The system should validate or derive the district from the reported location rather than trusting arbitrary client input.

## 8. District Data Isolation

Each district officer can access only their district's operational data.

The backend derives the user's effective district scope from the authenticated identity and applies it to service/repository/tool queries.

Example:

```text
current_user.role = officer
current_user.district_id = PUNE
        |
        v
complaint query WHERE district_id = PUNE
```

Admins may have statewide access.

Inspectors normally have one home district and access only to authorized assigned cases within that district.

## 9. Request Flow: Complaint Creation

```text
Citizen
  -> React Complaint Form
  -> POST /complaints
  -> Auth + Validation
  -> Complaint Service
  -> District Resolution
  -> SQLAlchemy
  -> PostgreSQL
  -> Complaint ID returned
  -> Evidence upload flow
```

After creation, asynchronous AI triage may run and store a structured analysis for staff review.

## 10. Request Flow: Officer Review

```text
District Officer
   -> Officer Dashboard
   -> Complaint API
   -> RBAC + District Scope
   -> Complaint Service
   -> PostgreSQL
```

The frontend must never send an arbitrary district ID and expect the server to trust it for authorization.

## 11. Request Flow: Inspector Assistant

```text
Inspector
   -> Assistant UI
   -> POST /agent/inspector-assistant
   -> Authorization
   -> Agent Orchestrator
       -> complaint tools
       -> inspection tools
       -> RAG search
       -> controlled database tools
   -> response + citations
```

## 12. Asynchronous Workloads

Use background jobs or a task queue for workloads that should not block HTTP requests, such as:

- OCR processing.
- Vision analysis.
- Large document ingestion.
- Embedding generation.
- Duplicate complaint analysis.
- Report generation.
- Notifications.

The first implementation may use a simple background worker; introduce a heavier queue only when justified.

## 13. Observability

Log:

- API request identifiers.
- Authentication events.
- Authorization failures.
- Complaint state changes.
- Assignment changes.
- AI agent executions.
- Tool calls.
- RAG retrieval metadata.
- Errors and processing times.

Do not log passwords, access tokens, private evidence contents, or sensitive secrets.

## 14. Deployment

### Demo deployment target

The current target is a simple Render Free Tier deployment for demonstration and evaluation. Docker is not required for the target deployment.

```text
                    Internet
                       |
             +---------+---------+
             |                   |
             v                   v
      Render Static Site    Render Web Service
       React/Vite build        FastAPI
             |                   |
             +---------+---------+
                       |
                       v
                  Supabase
          +------------+-------------+
          |            |             |
      PostgreSQL    Storage      PostGIS/pgvector
                       
                       +
                       v
                  Gemini API
```

### Frontend

Deploy the Vite production build as a Render Static Site. The frontend receives the public backend base URL through the appropriate build-time environment variable. No Supabase service-role secret is exposed to the frontend.

### Backend

Deploy FastAPI as a Render Web Service using native Python build/start commands. The backend connects to Supabase PostgreSQL/Storage and the Gemini API through server-side environment variables.

Typical runtime command:

```text
uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'
```

`--proxy-headers --forwarded-allow-ips='*'` is required behind Render's edge proxy so `request.client.host` (used by the per-IP rate limiter, `app/core/rate_limit.py`) reflects the real client rather than Render's internal proxy address for every request - see `docs/DEPLOYMENT.md` section 12.

The exact Render build/start configuration should match the repository's actual package manager and dependency files.

### Secrets and configuration

Production secrets must remain outside source control, including:

- Supabase service-role credentials
- database credentials where used
- Gemini API key
- JWT/authentication secrets

### Database and migrations

Run Alembic migrations from a trusted deployment environment against the Supabase database before or as part of release preparation. The deployed application must point to the latest verified migration head.

### Rate limiting

The current demo deployment intentionally uses the existing in-memory, single-process rate limiter. This is acceptable for a single Render Web Service instance but is not a distributed rate-limiting solution. Redis is not required for the current demo target.

### Refresh-session maintenance

The refresh-session cleanup remains a standalone script
(`scripts/cleanup_refresh_sessions.py`) and is run through an external
scheduler rather than an in-process application scheduler. The demo
deployment schedules it with `.github/workflows/cleanup-refresh-sessions.yml`
(a daily GitHub Actions workflow), since Render's own Cron Job service type
requires a paid plan. See `docs/SECURITY_AND_RBAC.md` section 20.4 and
`docs/DEPLOYMENT.md` section 7.

### Docker

Docker is not part of the target Render deployment architecture. Existing Docker files, if retained for local experimentation, must not be treated as required deployment infrastructure.

### Production baseline

The demo deployment should still use HTTPS, production CORS restrictions, secure secret handling, health checks, and production-safe error responses.

### Reference

The full deployment walkthrough - environment variable reference, Supabase/PostGIS/pgvector setup, Storage bucket configuration, and the production smoke-test checklist - lives in `docs/DEPLOYMENT.md`. The repository root's `render.yaml` is the Render Blueprint (infrastructure-as-code) that provisions both services described above.
