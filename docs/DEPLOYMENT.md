# Deployment Guide — Render Demo Deployment

## 1. Purpose and Scope

This document is the practical companion to `docs/DEVELOPMENT_ROADMAP.md`
Phase 13 and `docs/SYSTEM_ARCHITECTURE.md` section 14. It describes how to
deploy the Maharashtra Food Safety Complaint and Inspection Platform to
**Render Free Tier** for demonstration and evaluation.

This is a **demo deployment**, not a large-scale production deployment.
Deliberately out of scope, per `docs/DEVELOPMENT_ROADMAP.md` Phase 13's
constraints:

- Docker / Docker Compose (existing `Dockerfile`s remain for local
  experimentation only — see section 9)
- Redis, Celery, or any task queue
- Kubernetes
- AWS- or GCP-specific infrastructure

The deployed system is:

```text
Render Static Site  --->  Render Web Service  --->  Supabase (PostgreSQL,
(React/Vite build)        (FastAPI, native            PostGIS, pgvector,
                           Python runtime)             Storage)
                                |
                                v
                           Gemini API
```

## 2. Prerequisites

- A GitHub repository containing this project (Render deploys from a Git
  repository).
- A Supabase project with:
  - PostgreSQL (any tier — the free Supabase tier is sufficient for a demo)
  - The `postgis` and `vector` extensions enabled (see section 5)
  - A **private** Storage bucket for complaint/inspection evidence
    (`complaint-evidence` by default — matches `SUPABASE_STORAGE_BUCKET`)
  - A second **private** Storage bucket for RAG source documents
    (`rag-documents` by default — matches `RAG_STORAGE_BUCKET`)
- A Google Gemini API key (`GEMINI_API_KEY`).
- A Render account (Free Tier).

## 3. Deployment Options

### Option A — Blueprint (recommended, reproducible)

The repository root contains `render.yaml`, a Render Blueprint that defines
both services (`food-safety-backend`, `food-safety-frontend`) as
infrastructure-as-code. In the Render dashboard: **New → Blueprint**, point
it at this repository, and Render creates both services from the committed
spec. This is the reproducible path referenced by Phase 13's completion
criteria — re-deploying from a clean Render account only requires re-running
the blueprint and filling in the secrets in section 4.

### Option B — Manual service creation

Equivalent to the blueprint, created by hand in the Render dashboard:

**Backend (Web Service):**

| Setting | Value |
|---|---|
| Runtime | Python 3 |
| Root Directory | `Backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips='*'` |
| Health Check Path | `/health` |
| Plan | Free |

**Frontend (Static Site):**

| Setting | Value |
|---|---|
| Root Directory | `Frontend` |
| Build Command | `npm install && npm run build` |
| Publish Directory | `dist` |
| Redirect/Rewrite Rule | `/*` → `/index.html`, type **Rewrite** |
| Plan | Free (static sites have no paid tier on Render) |

The rewrite rule is required: this is a client-side-routed single-page app
(React Router, `Frontend/src/routes/AppRoutes.jsx`), so a hard refresh or
deep link on any non-root route (e.g. `/citizen/complaints/42`) must still
resolve to `index.html` and let the router take over, or the static file
server would 404 on a path it has no matching file for.

Both options produce the same two services; pick whichever fits how the
team wants to manage the Render account.

## 4. Environment Variables

None of these are hard-coded anywhere in the codebase — `app/core/config.py`
(backend) and `import.meta.env.VITE_API_URL` (frontend) are the only places
that read them. Set the values below on the corresponding Render service
("Environment" tab), never in a committed file.

### 4.1 Backend (`food-safety-backend`)

Reviewed from `Backend/.env.example`, the source of truth for what the
backend reads.

| Variable | Required | Example / notes |
|---|---|---|
| `APP_NAME` | optional | `Food Safety Platform API` |
| `ENVIRONMENT` | **yes** | `production` |
| `LOG_LEVEL` | optional | `INFO` |
| `DATABASE_URL` | **yes, secret** | Supabase Postgres connection string, `postgresql+psycopg2://...`. Use the Supabase **Transaction pooler** connection string for a single small backend instance. |
| `CORS_ORIGINS` | **yes** | Comma-separated allowed origins. Set to the frontend's exact deployed URL, e.g. `https://food-safety-frontend.onrender.com` (plus a custom domain if one is added). Never `*` — the backend sends credentialed CORS responses (`allow_credentials=True`), which browsers reject alongside a wildcard origin. |
| `JWT_SECRET_KEY` | **yes, secret** | Generate with `python -c "import secrets; print(secrets.token_urlsafe(48))"`, or let Render's `generateValue: true` (already set in `render.yaml`) create one. |
| `JWT_ALGORITHM` | optional | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | optional | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | optional | `7` — ceiling on a refresh session's lifetime; see `docs/SECURITY_AND_RBAC.md` section 19 for the rotation/reuse-detection design. |
| `SUPABASE_URL` | **yes, secret** | `https://<project-ref>.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | **yes, secret** | Supabase project settings → API → `service_role` key. **Backend-only** — see section 6. |
| `SUPABASE_STORAGE_BUCKET` | optional | `complaint-evidence` |
| `RAG_STORAGE_BUCKET` | optional | `rag-documents` |
| `GEMINI_API_KEY` | **yes, secret** | Google AI Studio / Gemini API key. |
| `GEMINI_MAIN_MODEL` | optional | `gemini-3.7-flash` |
| `GEMINI_REASONING_MODEL` | optional | `gemini-3.1-pro` |
| `GEMINI_EMBEDDING_MODEL` | optional | `gemini-embedding-2-preview` |
| `GEMINI_REQUEST_TIMEOUT_SECONDS` | optional | `20` |
| `ENABLE_REVERSE_GEOCODING` | optional | `true` |
| `NOMINATIM_BASE_URL` | optional | `https://nominatim.openstreetmap.org` |
| `NOMINATIM_USER_AGENT` | optional | Set a real contact address per Nominatim's usage policy if request volume grows. |

`PORT` is provided automatically by Render at runtime — do not set it
manually; the start command reads it as `$PORT`.

A few additional tuning knobs exist only in `Settings`
(`app/core/config.py`) with sensible defaults and are not required for a
demo deployment: `DB_POOL_SIZE`, `DB_MAX_OVERFLOW`, `DB_POOL_RECYCLE_SECONDS`
(connection pool sizing), `REFRESH_TOKEN_REUSE_GRACE_SECONDS`,
`REFRESH_SESSION_RETENTION_DAYS`,
`REFRESH_SESSION_REUSE_DETECTED_RETENTION_DAYS` (see section 7),
`MAX_REQUEST_BODY_SIZE_MB` (default `25` — the global request-size cap
enforced by `app/core/middleware.py`; raise this only if
`RAG_MAX_UPLOAD_SIZE_MB` is ever configured above the default and would
otherwise be rejected by this lower-level cap first), and the `RAG_*`
chunking/retrieval parameters (`docs/RAG_ARCHITECTURE.md`). Set them only if
the defaults need to change.

`GEMINI_EMBEDDING_DIMENSIONS` (default `768`) deserves its own callout rather
than folding into that list: it sets the output dimensionality requested from
`GEMINI_EMBEDDING_MODEL`, and it must match the fixed size of the
`rag_document_chunks.embedding` pgvector column (`EMBEDDING_DIM = 768` in
`Backend/alembic/versions/7c3f1a9d2e4b_add_rag_and_assistant_tables.py`) —
these are two independently-set values with no runtime check that they agree.
If `GEMINI_EMBEDDING_MODEL` is ever changed to a model with a different
native embedding size, either leave `GEMINI_EMBEDDING_DIMENSIONS` at `768`
(current Gemini embedding models support configurable output
dimensionality), or write a new migration to resize the column — and
re-embed every existing `rag_document_chunks` row — before changing this
value. Getting this out of sync doesn't corrupt data (pgvector rejects a
dimension mismatch at the database level), but it surfaces as a cryptic
`expected 768 dimensions, not N` Postgres error on the next ingestion or
retrieval query rather than a clear validation message pointing at this
setting — worth knowing before you're debugging it live.

### 4.2 Frontend (`food-safety-frontend`)

Reviewed from `Frontend/.env.example`.

| Variable | Required | Notes |
|---|---|---|
| `VITE_API_URL` | **yes** | The backend's public base URL, e.g. `https://food-safety-backend.onrender.com` (no trailing slash, no `/api/v1` suffix — `Frontend/src/services/api.js` appends that itself). |

Vite only inlines `VITE_`-prefixed variables, and only the values present
**at build time** — there is no runtime environment lookup in the deployed
static bundle. If the backend URL ever changes, update `VITE_API_URL` and
trigger a new Render build; the previous build's bundle would otherwise keep
pointing at the old URL.

No Supabase or Gemini secret is ever set on the frontend service. The
frontend only talks to the backend's own API — it never calls Supabase or
Gemini directly (`docs/SYSTEM_ARCHITECTURE.md` section 4: "the frontend must
never be treated as the source of authorization" applies equally to secret
handling).

## 5. Database: Supabase, PostGIS, pgvector, and Migrations

```text
Render backend deployment
        v
Alembic migration  (alembic upgrade head)
        v
Supabase PostgreSQL
        v
PostGIS + pgvector
```

1. In the Supabase SQL editor, enable the two extensions this project's
   migrations depend on (only needs to be done once per Supabase project):

   ```sql
   create extension if not exists postgis;
   create extension if not exists vector;
   ```

   These back the location columns added in
   `Backend/alembic/versions/014114ea0cea_add_postgis_and_location_columns.py`
   and the RAG embedding columns added in
   `Backend/alembic/versions/7c3f1a9d2e4b_add_rag_and_assistant_tables.py`.

2. `alembic upgrade head` runs on every backend start (see the
   `startCommand` in section 3/`render.yaml`), so a fresh Supabase database
   is brought to the latest schema automatically on first deploy, and any
   later deploy that adds a new migration applies it on the next restart.
   Alembic migrations are idempotent to re-run — applying an already-current
   database is a no-op.

   Render's **pre-deploy command** (a separate step that runs once per
   deploy, before traffic switches over) would normally be the cleaner place
   for this, but it requires a paid plan and this project targets the Free
   Tier — see `render.yaml`'s comment on `startCommand` for why migrations
   are chained into the start command instead.

3. After the first successful deploy, seed the Maharashtra district
   structure and an initial admin/staff user from a machine with network
   access to the Supabase database (a local shell pointed at the same
   `DATABASE_URL`, not something that runs inside the Render service):

   ```bash
   cd Backend
   venv/Scripts/python.exe -m scripts.seed_districts
   venv/Scripts/python.exe -m scripts.seed_complaint_categories
   venv/Scripts/python.exe -m scripts.seed_staff        # district officers/inspectors
   venv/Scripts/python.exe -m scripts.create_admin      # at least one admin account
   ```

   These are the same one-shot scripts used in local development
   (`docs/DEVELOPMENT_ROADMAP.md` Phase 2) — nothing deployment-specific
   about them, they just need to point at the production `DATABASE_URL`.

## 6. Supabase Storage

Two **private** buckets are required (never public — evidence and inspection
records are not meant to be publicly readable):

- `complaint-evidence` (`SUPABASE_STORAGE_BUCKET`) — complaint/inspection
  evidence uploads.
- `rag-documents` (`RAG_STORAGE_BUCKET`) — uploaded regulatory/SOP source
  documents for the RAG pipeline (`docs/RAG_ARCHITECTURE.md`).

`Backend/app/services/storage_service.py` accesses both using the
`service_role` key, which bypasses Supabase's Row Level Security and must
only ever exist as a backend environment variable — it is read via
`Settings.supabase_service_role_key` (a Pydantic `SecretStr`, so it is never
accidentally logged) and is never sent to, or readable by, the frontend.
Evidence the frontend needs to display is served through short-lived signed
URLs generated by the backend (`create_signed_url`), never a bucket made
public.

## 7. Refresh-Session Cleanup

`Backend/scripts/cleanup_refresh_sessions.py` deletes `refresh_sessions` rows
that are expired/revoked and past their retention window
(`docs/SECURITY_AND_RBAC.md` section 20). It is a standalone script, not an
API endpoint or in-process scheduler, and needs to run on a recurring
schedule in production.

This deployment uses **`.github/workflows/cleanup-refresh-sessions.yml`**, a
scheduled GitHub Actions workflow (daily at 03:00 UTC), because:

- Render's own Cron Job service type carries a minimum $1/month charge —
  incompatible with a Free Tier-only deployment.
- This project has no Celery/Redis/in-process scheduler by design
  (`docs/DEVELOPMENT_ROADMAP.md` Phase 13 constraints), and this task does
  not need one — running the script periodically *is* the mechanism.
- It adds no new always-on service; the workflow only runs for the seconds
  it takes to execute the script.

Setup: add a `DATABASE_URL` repository secret (GitHub repo → Settings →
Secrets and variables → Actions) with the same Supabase connection string
used on the Render backend service. The workflow is also runnable on demand
via its `workflow_dispatch` trigger, e.g. after a manual retention-policy
change, without waiting for the next scheduled run.

## 8. Storage Bucket Privacy Check

`Backend/scripts/check_storage_bucket_privacy.py` verifies that both
Supabase Storage buckets (section 6) are actually configured private.
Evidence/RAG-document authorization is enforced entirely in the backend API
(ownership/district/role checks before a signed URL is ever generated) —
none of that matters if the underlying bucket itself is ever misconfigured
public (a single checkbox in the Supabase dashboard), which nothing in the
running application would otherwise notice on its own, since normal request
handling never has a reason to call the bucket-config endpoint
(`docs/SECURITY_AND_RBAC.md` section 8, `docs/PROJECT_AUDIT_REPORT.md`
finding 1.5).

This deployment uses **`.github/workflows/check-storage-bucket-privacy.yml`**,
a scheduled GitHub Actions workflow (daily at 04:00 UTC — offset from the
refresh-session cleanup workflow's 03:00 UTC run), for the same reasons as
section 7's cleanup workflow: no Render Cron Job (paid feature), no new
always-on service. It exits non-zero (failing the workflow run, which
GitHub surfaces as a failed Action) if a bucket is confirmed public **or**
if a check could not be completed at all (e.g. Supabase unreachable) — a
broken check must not silently look like a passing one.

Setup: add `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` repository secrets
with the same values used on the Render backend service. Also runnable on
demand via `workflow_dispatch`, e.g. right after creating the buckets during
initial setup (section 6), to confirm they're private before any real
evidence is uploaded.

## 9. Docker

`Backend/Dockerfile`, `Frontend/Dockerfile`, and `docker-compose.yml` are
retained for local containerized experimentation only. They are **not**
part of the Render deployment path described above — Render builds and runs
both services natively from source (`pip install` / `npm install` +
`npm run build`), with no image build step. Do not add a `render.yaml`
`dockerfilePath` or otherwise wire these files into the Render services.

## 10. Production Baseline Checklist

- [ ] HTTPS — automatic on both Render service types, no action needed.
- [ ] `CORS_ORIGINS` set to the exact deployed frontend origin(s), not `*`.
- [ ] No secret (`DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`,
      `JWT_SECRET_KEY`) present in any committed file, Docker file, or log
      line — the repository root `.gitignore` excludes `.env`;
      `DATABASE_URL`, `JWT_SECRET_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, and
      `GEMINI_API_KEY` are all Pydantic `SecretStr` so they cannot be
      accidentally interpolated into a log message or error response either
      (`docs/SECURITY_AND_RBAC.md` section 18); production additionally
      refuses to boot at all if `JWT_SECRET_KEY` is still the checked-in
      development default.
- [ ] `/health` returns `200` with `"database": "connected"`.
- [ ] Unhandled backend errors return the generic JSON envelope
      (`app/main.py`'s `error_handling_middleware`), never a stack trace —
      verified by `app/tests/integration/test_hardening.py`.
- [ ] Alembic is at the latest revision (`alembic current` matches
      `alembic heads` when run against the production `DATABASE_URL`).
- [ ] Both Supabase Storage buckets exist and are private, not public —
      verified by running `scripts/check_storage_bucket_privacy.py` (section 8)
      manually, not just assumed from the dashboard.
- [ ] The refresh-session cleanup workflow's `DATABASE_URL` secret is set
      and a manual `workflow_dispatch` run succeeds.
- [ ] The storage bucket privacy check workflow's `SUPABASE_URL` /
      `SUPABASE_SERVICE_ROLE_KEY` secrets are set and a manual
      `workflow_dispatch` run succeeds (section 8).

## 11. Smoke Test Checklist

Run through this after every deploy, or after standing up a fresh
environment from scratch.

**Backend**

1. `GET https://<backend>.onrender.com/health` → `200`,
   `{"status": "ok", "environment": "production", "database": "connected"}`.
2. `GET https://<backend>.onrender.com/docs` loads the OpenAPI UI (confirms
   the app booted and routing works).
3. `POST /api/v1/auth/login` with a seeded admin/staff account → `200` with
   an access and refresh token.
4. A request to a protected endpoint with no `Authorization` header → `401`,
   not a `500`.

**Frontend**

5. Load the frontend root URL → the public Home page renders (confirms the
   static build and rewrite rule work for the root path).
6. Log in as a citizen → redirected to `/citizen`, and reloading that exact
   URL (deep link / hard refresh) still renders the dashboard rather than a
   404 (confirms the SPA rewrite rule, not just client-side navigation from
   `/`).
7. Log in as a district officer and as an inspector in separate
   sessions/browsers → each lands on their own role's dashboard, and
   navigating directly to the other role's route (e.g. an inspector to
   `/officer`) is redirected/blocked rather than rendering
   (`RoleRoute`/backend RBAC both enforce this — see
   `docs/SECURITY_AND_RBAC.md`).
8. Let an access token expire (or reduce
   `ACCESS_TOKEN_EXPIRE_MINUTES` temporarily) and confirm a subsequent
   request triggers a silent refresh (`AuthProvider` in
   `frontend/src/store/authStore.jsx`) rather than an unexpected logout, and
   that the *new* rotated refresh token is what gets used on the next
   refresh (a stale-token bug here would surface as being logged out after
   exactly one silent refresh).
9. Log out → both tokens are cleared client-side and the corresponding
   `refresh_sessions` row is revoked server-side (a captured pre-logout
   refresh token can no longer be used to obtain a new access token).
10. Resize to a mobile viewport width and confirm the sidebar collapses into
    the mobile drawer (`AppShell.jsx`) and forms/tables remain usable.

**End-to-end workflow**

11. Citizen submits a complaint with a photo → complaint appears in the
    correct district officer's queue → officer reviews and assigns an
    inspector → inspector completes an inspection → citizen sees the
    updated status on their own dashboard/timeline.
12. Trigger the Complaint Triage agent and the Evidence Analysis agent on
    that complaint → both return a result without erroring (confirms
    `GEMINI_API_KEY`/Supabase Storage connectivity from the deployed
    backend, not just local dev).
13. As an inspector, ask the Inspector Assistant a regulation question that
    should be answerable from the seeded RAG corpus → response includes a
    valid source citation (confirms pgvector retrieval end-to-end).

## 12. Known Limitations (carried forward from Phase 12/13, not regressions)

- **Single-process rate limiting.** `app/core/rate_limit.py` is an in-memory
  limiter. Render Free Tier runs one instance, so this is correct for the
  current deployment target; it would need a shared store (e.g. Redis) only
  if scaled to multiple backend instances, which is explicitly out of scope
  here (`docs/SECURITY_AND_RBAC.md` section 11, `docs/SYSTEM_ARCHITECTURE.md`
  section 14). The limiter keys on `request.client.host`, which is only the
  real visiting client's IP because the start command above passes
  `--proxy-headers --forwarded-allow-ips='*'` to uvicorn - without those
  flags, every request behind Render's edge proxy would report the same
  internal proxy address, collapsing the per-IP limit into one shared bucket
  for all users. Confirm both flags are present on any manually-created
  service (Option B above) or on any deployment target other than Render.
- **Render Free Tier instances spin down after inactivity** and take a short
  time to spin back up on the next request — expected behavior for the free
  plan, not an application bug. The first request after idle time (e.g. the
  smoke test's first `/health` call) may take noticeably longer.
- **No automated CI pipeline** runs the test suite or this smoke test on
  every push. The only scheduled automation is the refresh-session cleanup
  workflow (section 7). Adding `frontend-ci.yml`/`backend-ci.yml`-style test
  gating remains a candidate for future work, not required by Phase 13's
  completion criteria.
