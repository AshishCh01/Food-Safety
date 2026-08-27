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

Development:

```text
React container
FastAPI container
PostgreSQL via Supabase
```

Production should separate secrets from source control and use HTTPS. Docker is the standard local and deployment packaging mechanism.
