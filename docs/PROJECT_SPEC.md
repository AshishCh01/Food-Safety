# Maharashtra Food Safety Complaint & Inspection Platform

## 1. Project Overview

The Maharashtra Food Safety Complaint & Inspection Platform is a web-based system for citizens to report suspected food-safety violations and for Food Safety Department personnel to review, investigate, inspect, and resolve those complaints.

The platform will support district-level operations across Maharashtra. The architecture must support 36 districts without creating district-specific code paths.

The system combines:

- Citizen complaint submission
- Evidence upload and management
- Location-aware complaint routing
- District-based officer and inspector access
- Complaint verification and inspection workflows
- AI-assisted complaint triage
- AI-assisted evidence analysis
- RAG-based Inspector Assistant
- Investigation assistance using controlled tools
- Analytics and dashboards
- Audit logging

AI is an assistant to authorized personnel. It must not independently make final legal or regulatory decisions.

---

## 2. Primary Goals

1. Make it easy for citizens to report food-safety concerns.
2. Automatically route complaints to the appropriate district.
3. Give district officers a secure view of complaints belonging to their district.
4. Allow inspectors to manage assigned inspections and submit findings.
5. Provide AI-assisted triage, evidence analysis, investigation support, and regulatory knowledge retrieval.
6. Maintain traceability through audit logs and complaint timelines.
7. Build the system so it can scale from a college/demo deployment to a larger production architecture.

---

## 3. Non-Goals

The first version must not attempt to:

- Automatically declare a business legally guilty of a violation.
- Automatically issue penalties or enforcement orders without authorized human review.
- Allow an LLM to execute arbitrary SQL.
- Give AI unrestricted access to all citizen or government data.
- Build separate codebases for each district.
- Introduce multiple databases without a concrete architectural need.

---

## 4. Technology Stack

### Frontend

- React
- Vite
- React Router
- Tailwind CSS
- Leaflet for maps
- OpenStreetMap as map data/tile source where appropriate

### Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic
- JWT-based authentication or an equivalent secure token mechanism

### Database and Storage

- Supabase PostgreSQL
- PostGIS for geospatial operations
- pgvector for RAG embeddings where appropriate
- Supabase Storage for images, videos, and documents

### AI

- LLM provider selected through a backend abstraction layer
- Vision model for evidence analysis where available
- OCR for printed/packaged food information
- Embedding model for RAG
- Optional reranker for improved retrieval quality

### Infrastructure

- Docker
- Docker Compose for local development
- Environment variables for secrets
- Git and GitHub
- CI/CD can be added in a later phase

---

## 5. High-Level Architecture

```text
Citizen / Staff
      |
      v
React Frontend
      |
      v
FastAPI API
      |
      +--------------------+
      |                    |
      v                    v
Application Services    AI Agent Layer
      |                    |
      v             +------+-------+
SQLAlchemy          |              |
      |        Complaint       Evidence
      v        Agent           Agent
Supabase             |              |
PostgreSQL           +------+-------+
 + PostGIS                  |
 + pgvector                 v
 + Storage            Investigation
                           Agent
                             |
                             v
                       Inspector Agent
                             |
                     +-------+--------+
                     |                |
                     v                v
                  RAG / KB        Controlled
                  Retrieval        DB Tools
```

The frontend must never connect directly to PostgreSQL for application operations. Application data access goes through the backend APIs. Supabase Storage can be used through controlled backend or signed-upload flows.

---

## 6. Organizational Hierarchy

The logical administrative hierarchy is:

```text
Maharashtra
  |
  +-- Division
       |
       +-- District
            |
            +-- District Officer
            |
            +-- Inspectors
                 |
                 +-- Businesses
                      |
                      +-- Complaints
                           |
                           +-- Inspections
```

The system must support 36 districts through data, not hard-coded logic.

Each district should have one district officer account for the initial demo/seed environment. The model must allow multiple officers or reassignment later if business requirements change.

Each district may have multiple inspectors. Do not hard-code one inspector per district.

---

## 7. User Roles and Permissions

### 7.1 Citizen

Can:

- Register an account
- Log in
- Create complaints
- Upload evidence
- Provide business and location details
- Track own complaints
- View complaint status and timeline
- Respond to requests for additional information

Cannot:

- View another citizen's private complaint data
- Access officer/inspector dashboards
- Modify inspection findings
- Access internal investigation notes

### 7.2 Inspector

Belongs to a district.

Can:

- View assigned complaints
- View permitted complaint evidence
- Perform inspections
- Record inspection findings
- Upload inspection evidence
- Use the Inspector Assistant
- Submit inspection reports
- View relevant inspection history for authorized cases

Cannot:

- Access unrelated districts' confidential data
- Change system-level roles
- Override administrative permissions

### 7.3 District Officer

Belongs to exactly one district in the normal operational model.

Can:

- View complaints for their district
- Review complaints
- Verify or reject complaints according to workflow rules
- Assign inspectors in their district
- View district businesses
- View inspection history for authorized district cases
- Use AI investigation assistance
- View district analytics
- Review inspector reports

Cannot:

- Access another district's restricted data
- Create system administrators
- Modify global platform configuration

### 7.4 Admin

Can:

- Manage districts
- Manage staff accounts
- Create/disable officer and inspector accounts
- Assign staff to districts
- Manage complaint categories
- View statewide analytics
- View system audit logs
- Manage system configuration

Admin access must be tightly protected.

---

## 8. Authentication and Authorization

Use one authentication implementation with role-based access control (RBAC), not separate authentication systems for every role.

The authenticated identity should contain at least:

```text
user_id
role
status
 district_id (when applicable)
```

Authorization must be enforced on the backend.

### District isolation rule

A district officer should only be able to retrieve records that belong to their district.

Do not rely on frontend route hiding for authorization.

Example:

```text
Pune Officer
  -> district_id = Pune
  -> can query Pune complaints
  -> cannot query Nagpur complaints
```

The same principle applies to inspectors, except inspectors should normally be restricted to cases assigned to them plus any explicitly authorized district data.

AI tools must inherit the same authorization boundary. The agent must not be able to bypass application permissions.

---

## 9. Complaint Lifecycle

The main complaint workflow should support states similar to:

```text
SUBMITTED
    |
    v
UNDER_REVIEW
    |
    +----> NEEDS_INFORMATION
    |
    v
VERIFIED
    |
    v
INSPECTOR_ASSIGNED
    |
    v
INSPECTION_SCHEDULED
    |
    v
INSPECTION_COMPLETED
    |
    v
ACTION_REQUIRED
    |
    v
RESOLVED
```

Alternative terminal or non-progress states may include:

```text
REJECTED
DUPLICATE
INSUFFICIENT_EVIDENCE
CANCELLED
```

Every state change should be auditable.

---

## 10. Complaint Data

A complaint should support at least:

- Internal database ID
- Human-readable complaint number
- Citizen/user ID
- Business ID or business details
- District ID
- Complaint category
- Description
- Priority/severity
- Latitude and longitude
- Address or location description
- Submission timestamp
- Status
- Verification data
- Evidence references
- Assignment information
- Resolution information

Human-readable complaint numbers should follow a district-aware format, for example:

```text
MH-PUN-2026-000123
MH-NGP-2026-000087
```

The complaint number is for users; the internal database primary key remains separate.

---

## 11. Location and District Assignment

Citizen complaints should support location capture.

Preferred flow:

```text
Citizen location
      |
      v
Latitude / Longitude
      |
      v
Geospatial lookup
      |
      v
District
      |
      v
Complaint routing
```

Use PostGIS for reliable spatial queries where practical.

Do not trust a citizen-provided district field as the sole source of routing truth.

If GPS is unavailable, allow manual address selection and an officer correction workflow.

---

## 12. Core Database Entities

The initial schema should include at least:

```text
users
roles / role definitions
states
divisions
districts
staff_profiles
businesses
complaint_categories
complaints
complaint_status_history
evidence
assignments
inspections
inspection_findings
notifications
audit_logs
documents
document_chunks
```

Relationships must use foreign keys and appropriate indexes.

District, status, timestamp, and business relationships should be indexed for common queries.

---

## 13. Evidence Handling

Evidence may include:

- Images
- Videos
- PDFs or receipts
- Other permitted supporting documents

Files should be stored in Supabase Storage.

Database records should store metadata and a secure storage reference/path rather than large binary payloads.

Evidence metadata should include, where applicable:

```text
file_id
complaint_id
storage_path
file_type
file_size
uploaded_by
uploaded_at
hash/checksum when practical
```

Use signed URLs or equivalent controlled access for private evidence.

---

## 14. AI Agent Architecture

The project should use specialized agents or workflows with limited responsibilities instead of one unrestricted general-purpose agent.

### 14.1 Complaint Triage Agent

Responsibilities:

- Classify complaint category
- Extract structured fields from free text
- Generate a concise summary
- Suggest priority
- Detect missing information

The agent should return structured data validated by Pydantic schemas.

It may recommend priority but must not make final regulatory decisions.

### 14.2 Evidence Analysis Agent

Responsibilities:

- Analyze uploaded evidence
- Run OCR when appropriate
- Extract visible dates, labels, and other relevant text
- Identify visual observations
- Summarize evidence

Example observation:

```text
Possible expired date visible in image.
```

Avoid making unsupported legal conclusions.

### 14.3 Investigation Agent

Responsibilities:

- Retrieve authorized complaint history
- Retrieve business history
- Find potentially related/duplicate complaints
- Retrieve relevant evidence summaries
- Retrieve relevant regulatory guidance
- Generate an investigation brief

The agent must use controlled backend tools.

### 14.4 Inspector Assistant Agent

Responsibilities:

- Answer inspection-related questions
- Retrieve applicable regulations and SOPs
- Suggest inspection checks based on complaint category
- Explain retrieved guidance
- Cite source documents and page/section metadata
- Help structure inspector notes

The agent should be RAG-first for regulatory/procedural questions.

### 14.5 Report Generation Agent

Responsibilities:

- Convert verified structured inspection data into a professional report
- Use only supplied facts and authorized findings
- Never invent observations, dates, legal findings, or penalties

---

## 15. Agent Tools

Agents should access application data only through narrow, explicit tools.

Examples:

```text
get_complaint(complaint_id)
get_business(business_id)
get_complaint_history(business_id)
get_inspection_history(business_id)
get_assigned_inspections(inspector_id)
find_similar_complaints(complaint_id)
search_regulations(query, filters)
get_evidence_metadata(complaint_id)
analyze_evidence(evidence_id)
create_investigation_draft(data)
```

Do not provide a generic tool such as:

```text
execute_arbitrary_sql(query)
```

Tool results must be authorization-aware.

---

## 16. RAG Knowledge Base

The initial knowledge base should prioritize official and department-approved material.

Suggested categories:

```text
knowledge_base/
|
+-- laws/
+-- regulations/
+-- inspection_guidelines/
+-- hygiene_guidelines/
+-- licensing/
+-- sampling_procedures/
+-- food_recall_procedures/
+-- enforcement_guidelines/
+-- department_sops/
```

Potential source categories include official Food Safety and Standards Authority of India material and department-provided SOPs.

Do not use unofficial blogs or random web pages as primary regulatory truth.

Every indexed chunk should carry metadata such as:

```text
document_id
title
source
category
business_type
section
page_number
effective_date
version
```

---

## 17. RAG Pipeline

```text
Official documents
      |
      v
Document loader/parser
      |
      v
Cleaning / normalization
      |
      v
Chunking
      |
      v
Metadata enrichment
      |
      v
Embeddings
      |
      v
Supabase pgvector
      |
      v
Retriever
      |
      v
Optional reranker
      |
      v
Inspector Assistant
      |
      v
Answer + citations
```

Retrieval should support metadata filtering.

Example:

```text
business_type = restaurant
category = inspection
```

The assistant should prefer newer/effective documents when version metadata is available.

---

## 18. AI Safety and Governance Rules

1. AI output is advisory unless explicitly approved by an authorized human workflow.
2. AI must not invent facts.
3. AI must not invent citations.
4. AI should identify uncertainty when evidence is insufficient.
5. AI tools must enforce the current user's authorization context.
6. Sensitive internal data must not be exposed to unauthorized roles.
7. Regulatory answers should cite the retrieved source document and relevant section/page when possible.
8. Important workflow actions should require explicit user confirmation.
9. Agent actions should be logged for auditability.

---

## 19. Officer Dashboard

Each district officer dashboard should be scoped automatically to the officer's district.

Dashboard metrics may include:

- Total complaints
- Pending complaints
- High-priority complaints
- Verified complaints
- Complaints under inspection
- Resolved complaints
- Average resolution time
- Complaints by category
- Complaints by area
- Complaint trends

A map should visualize authorized complaints using Leaflet/PostGIS-backed location data.

---

## 20. Inspector Dashboard

Inspector dashboard should include:

- Assigned cases
- Today's inspections
- Upcoming inspections
- Overdue inspections
- Inspection history
- Case details
- Evidence
- Inspection checklist
- Inspector Assistant
- Report generation

---

## 21. Admin Dashboard

Admin dashboard should include statewide/system-level information:

- District counts
- Officer/inspector counts
- Complaint trends across districts
- Category trends
- Resolution metrics
- User/staff management
- Audit logs
- System health metrics

Do not expose private complaint details more broadly than required.

---

## 22. Frontend Structure Principles

Frontend should separate:

- Pages
- Reusable components
- API services
- State management
- Route protection
- Role-aware navigation
- Form validation
- Map components
- Agent UI

Role routes must be protected on the frontend for user experience, but backend authorization remains the source of truth.

---

## 23. Backend Structure Principles

Use this layering convention:

```text
API Route
   |
   v
Service
   |
   v
Repository
   |
   v
SQLAlchemy
   |
   v
PostgreSQL
```

For agents:

```text
Agent
  |
  v
Tool
  |
  v
Service / Repository
  |
  v
Authorized data
```

Do not put complex database logic directly in route handlers.

Do not put business rules inside frontend components.

---

## 24. SQLAlchemy and Alembic Rules

- SQLAlchemy is the ORM/database access layer.
- Alembic is the schema migration system.
- Production schema changes must go through Alembic migrations.
- Avoid manual production schema edits.
- Keep models, schemas, services, and repositories separated.
- Add appropriate database indexes.
- Use foreign keys and constraints to preserve data integrity.

Typical migration workflow:

```bash
alembic revision --autogenerate -m "create complaints table"
alembic upgrade head
```

Migration files must be reviewed before applying them.

---

## 25. API Design Principles

Use versioned APIs where practical:

```text
/api/v1/auth
/api/v1/complaints
/api/v1/businesses
/api/v1/inspections
/api/v1/assignments
/api/v1/admin
/api/v1/agents
```

Use Pydantic request/response models.

Return consistent error structures.

Do not expose internal ORM objects directly from API handlers.

---

## 26. Audit Logging

Audit logs should record sensitive operational events such as:

- Login/security events where required
- Complaint status changes
- Complaint assignment
- Inspection submission
- Role/account changes
- Important admin actions
- Agent-triggered actions or tool calls

A useful audit record contains:

```text
actor_id
actor_role
action
entity_type
entity_id
timestamp
request_id or correlation_id when practical
metadata
```

Audit logs should be append-oriented and protected from ordinary users.

---

## 27. Notifications

The initial system can support in-app notifications.

Later phases may add:

- Email
- SMS
- Push notifications

Examples:

```text
Complaint submitted
Complaint status changed
Inspector assigned
Inspection scheduled
Additional information requested
Complaint resolved
```

---

## 28. Security Requirements

Minimum requirements:

- Passwords must be securely hashed if application-managed authentication is used.
- Secrets must come from environment variables/secrets management.
- JWT/session validation must be centralized.
- RBAC must be enforced server-side.
- District isolation must be enforced server-side.
- File uploads require validation and size limits.
- Private files require controlled access.
- API inputs require validation.
- Rate limiting should be considered for public complaint and authentication endpoints.
- CORS must be configured intentionally.
- SQL injection must be prevented through parameterized ORM/database access.
- Logs must not leak passwords, tokens, or unnecessary personal data.

---

## 29. Testing Strategy

Every phase should include tests.

### Unit tests

- Services
- Authorization functions
- Validation
- Agent tool wrappers
- RAG retrieval utilities

### Integration tests

- Database operations
- API endpoints
- Authentication flows
- Complaint workflow
- Inspector assignment

### AI tests

- Structured output validity
- Retrieval quality test cases
- Prompt/tool contract tests
- Hallucination safeguards
- Authorization boundary tests

The AI layer should not be considered correct merely because a demo prompt produces a good answer.

---

## 30. Development Phases

### Phase 0 — Specification

Deliver:

- Project specification
- Architecture document
- Database design
- API contract
- Agent design
- Development roadmap

### Phase 1 — Foundation

Build:

- React application
- FastAPI application
- SQLAlchemy
- Alembic
- Supabase PostgreSQL connection
- Docker development setup
- Environment configuration
- Logging
- Health endpoint

### Phase 2 — Authentication and RBAC

Build:

- Citizen registration/login
- Staff account creation
- Role model
- Role-aware routes
- District-aware authorization

### Phase 3 — Complaint Management

Build:

- Businesses
- Complaint categories
- Complaint creation
- Complaint tracking
- Complaint status history
- Evidence metadata
- Supabase Storage integration

### Phase 4 — Officer and Inspector Workflow

Build:

- Officer dashboard
- Inspector dashboard
- Assignment workflow
- Inspection workflow
- Findings
- Reports
- Audit logs

### Phase 5 — Maharashtra Geography

Build:

- Divisions
- 36 districts
- District staff seed data
- PostGIS queries
- District routing
- Map visualization

### Phase 6 — Complaint Triage Agent

Build:

- Complaint classification
- Structured extraction
- Priority recommendation
- Missing-information detection

### Phase 7 — Evidence Agent

Build:

- OCR
- Vision analysis
- Evidence summarization
- Product date extraction

### Phase 8 — RAG and Inspector Assistant

Build:

- Document ingestion
- Chunking
- Embeddings
- pgvector retrieval
- Metadata filtering
- Source citations
- Inspector Assistant UI

### Phase 9 — Investigation Agent

Build:

- Controlled database tools
- Complaint history retrieval
- Business history
- Similar/duplicate complaint detection
- Investigation briefs

### Phase 10 — Analytics and Notifications

Build:

- Dashboards
- Charts
- Trends
- In-app notifications

### Phase 11 — Security and Quality

Build:

- Security hardening
- Authorization tests
- AI safety tests
- Performance testing
- Error monitoring

### Phase 12 — Deployment

Build:

- Production Docker configuration
- CI/CD
- Environment separation
- Database migration strategy
- Production logging and monitoring

---

## 31. Claude Code Development Rules

Claude Code must treat this document as a source of truth.

Before implementing a feature:

1. Read the relevant project documentation.
2. Inspect the existing codebase.
3. Reuse existing abstractions when possible.
4. Do not introduce a new framework or database without justification.
5. Implement one bounded feature at a time.
6. Run tests and relevant checks after changes.
7. Review the diff for accidental changes.
8. Update documentation when architecture changes.

Claude Code must not:

- Rewrite the entire project to solve a local issue.
- Replace SQLAlchemy with another ORM without an explicit architectural decision.
- Bypass Alembic migrations.
- Give agents arbitrary SQL access.
- Bypass RBAC or district isolation.
- Store secrets in source control.
- Invent regulatory content when official sources are unavailable.
- Add large dependencies without explaining the reason.

---

## 32. Definition of Done for a Feature

A feature is considered complete only when:

- The implementation matches the architecture.
- Authorization is enforced correctly.
- Database changes are migrated through Alembic.
- API validation exists.
- Relevant frontend states are handled.
- Tests are present for important logic.
- Errors are handled cleanly.
- Documentation is updated when necessary.

---

## 33. Initial Repository Structure

```text
food-safety-platform/
├── frontend/
├── backend/
├── docs/
├── data/
├── scripts/
├── nginx/
├── docker-compose.yml
├── .env.example
├── CLAUDE.md
└── README.md
```

The repository may grow into more detailed modules, but the separation of frontend, backend, documentation, data/knowledge-base ingestion, and infrastructure should remain clear.

---

## 34. Success Criteria

The completed project should demonstrate this end-to-end flow:

```text
Citizen
  |
  v
Submit complaint + evidence + location
  |
  v
Complaint created and routed to district
  |
  v
District Officer reviews complaint
  |
  v
AI triage/evidence assistance
  |
  v
Officer verifies and assigns Inspector
  |
  v
Inspector performs inspection
  |
  +----> Inspector Assistant retrieves official guidance
  |
  v
Inspector submits findings
  |
  v
Officer reviews outcome
  |
  v
Complaint resolved / further action
```

The strongest demonstration is not the number of AI features. It is a secure, traceable workflow where AI improves the work of citizens, officers, and inspectors without replacing human authority.
