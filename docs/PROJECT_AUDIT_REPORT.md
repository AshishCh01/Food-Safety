# Project Audit Report — Maharashtra Food Safety Complaint & Inspection Platform

**Date:** 2026-09-01
**Scope:** Full-stack audit — backend (FastAPI/SQLAlchemy/Alembic), frontend (React/Vite), database (PostgreSQL/PostGIS/pgvector via Supabase), authentication/RBAC/district isolation, file uploads/storage, AI agents (Gemini) and RAG, analytics/notifications, and Render deployment configuration.
**Method:** Full read of `docs/CLAUDE.md` and all `docs/*.md`; direct inspection of critical auth/middleware/rate-limit code; six parallel deep-dive reviews (auth/RBAC, uploads/storage, AI/RAG, database/migrations, frontend, deployment/config); execution of the available automated checks (`alembic heads`/`history`, backend app import, `vite build`, `oxlint`); git-history analysis. Every finding below is anchored to a specific file/line and was independently verified against the current code, not assumed from documentation claims.
**Reviewer stance:** Documentation in this repo (`docs/SECURITY_AND_RBAC.md`, `docs/DEVELOPMENT_ROADMAP.md`) makes extensive claims about prior "Phase 12 hardening" fixes and a 358-test backend / 60-test frontend suite. This audit treated every such claim as unverified until checked against actual code, and found the *implementation* claims were almost all accurate — but the *test suite that would have proven it* no longer exists (see Finding 1). Findings below reflect the state of the code as of the current `main` branch (HEAD `71c9a9b`).

---

## 0. Headline Finding

**The entire automated test suite — backend and frontend — was deliberately deleted in commit `44db9e9` ("all test files are removed", 2026-08-29, 10 commits before current HEAD).** This is not a gitignore artifact or an accident: the commit explicitly removes ~50 backend test files (`Backend/app/tests/**`, `pytest`/`pytest-cov` from `requirements.txt`, the `[tool.pytest.ini_options]` block from `pyproject.toml`) and ~15 frontend test files plus `vitest`/`@testing-library` from `package.json`/`package-lock.json`. Only stale `.pyc` bytecode remnants (dated Aug 27–29) remain on disk as evidence the tests once existed and passed. `git ls-files` confirms zero test files are tracked; `pytest` now collects 0 tests; `npm test` has no script to run. See Finding 1 for full detail and impact.

Everything else in this report should be read with that context: the codebase is materially better-engineered than "no tests" usually implies (see §4, Confirmed-Good Areas), but none of it currently has a regression safety net, and every prior "verified by N passing tests" claim in the roadmap doc is now unverifiable by the artifact it cites.

---

## 1. Findings

Each finding lists: **Severity**, **Area**, **Evidence**, **Why it matters**, **Reproduction**, **Recommended fix**, **Blocks demo/deployment?**

### 1.1 — [CRITICAL] Entire automated test suite deleted; no regression coverage exists
- **Area:** Testing / Process / all areas transitively
- **Evidence:** `git log --oneline` shows commit `44db9e9718afb5e30d14b69c85f5d9783b3a1eac` — "all test files are removed", authored by the repo's own primary author, 2026-08-29 23:46. `git show --stat 44db9e9` lists 71 files changed, deleting: all of `Backend/app/tests/unit/*.py` and `Backend/app/tests/integration/*.py` (`conftest.py`, `factories.py`, and ~48 `test_*.py` files covering auth, RBAC, district isolation, complaints, inspections, assignments, all four AI agents, RAG parsing/chunking/retrieval, refresh-session rotation/cleanup, evidence validation, hardening); `pytest`/`pytest-cov` from `Backend/requirements.txt`; the `[tool.pytest.ini_options]` block from `Backend/pyproject.toml`; all of `Frontend/src/**/*.test.{js,jsx}` (auth store, route guards, agent panels, services); `vitest`/`@testing-library`/`jsdom` from `Frontend/package.json` and the 5,332-line diff in `package-lock.json`; `Frontend/vite.config.js`'s test config; and the "Run tests" sections of both `README.md` files. Confirmed independently: `venv/Scripts/python.exe -m pytest -q` → "no tests ran in 0.03s"; `Frontend/package.json` has no `test` script and no `vitest` dependency; `git ls-files Backend/app/tests` returns nothing.
- **Why it matters:** `docs/DEVELOPMENT_ROADMAP.md` §20 (Phase 12/13 status) repeatedly cites specific test counts ("358 passing", "60 passing", "327 passing (up from 308)") as the verification method for security-critical fixes: rate limiting, the login timing side-channel fix, refresh-token rotation/reuse-detection, the assignment race-condition constraint, evidence upload validation, and the CORS/error-handling middleware ordering. None of that is checkable anymore. Every future change to this codebase — including fixes to the findings in this report — has zero automated protection against regressing any previously-fixed bug (e.g., silently reintroducing the login timing leak, breaking refresh-token rotation, or loosening district isolation). The project's own `docs/DEVELOPMENT_ROADMAP.md` §19 "Definition of Done" requires "tests pass" for every phase; that bar is currently unmeetable.
- **Reproduction:** `cd Backend && venv/Scripts/python.exe -m pytest -q` → "no tests ran in 0.03s". `cd Frontend && npm test` → `npm error Missing script: "test"`.
- **Recommended fix:** Restore the deleted test suite from the parent commit (`git show 30a0c06:Backend/app/tests/... ` etc., or `git checkout 30a0c06^{tree} -- Backend/app/tests Frontend/src/**/*.test.*` followed by restoring the removed dependencies) unless there was a specific, deliberate reason to remove it that should instead be documented; if the removal was intentional (e.g. moving to a different test strategy), that strategy needs to actually exist before this can be called "tested." At minimum, before any further deployment, re-add `pytest`/`pytest-cov` and `vitest`/`@testing-library` and rebuild coverage for: auth/refresh rotation, district isolation, file upload validation, and the AI agent tool-authorization boundary — the highest-consequence areas if a regression slips in silently.
- **Blocks demo/deployment?** Does not block a demo running successfully (the app itself works — see §4). **Blocks confident/safe deployment and any further iteration**, since there is currently no way to verify a change hasn't broken authorization, auth, or data isolation before it ships.

### 1.2 — [HIGH] Rate limiter is keyed on the raw TCP peer address with no reverse-proxy trust; collapses to a single shared bucket on the actual Render deployment, enabling a trivial platform-wide denial of service
- **Area:** Backend / Security / Deployment
- **Evidence:** `Backend/app/core/rate_limit.py:44-46` — `InMemoryRateLimiter.__call__` keys solely on `request.client.host`. `render.yaml:39` sets `startCommand: alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT` with no `--proxy-headers`/`--forwarded-allow-ips` flag, and there is no `ProxyHeadersMiddleware` or equivalent anywhere in `Backend/app/main.py` or the rest of the codebase (confirmed by repo-wide search). Render terminates TLS and proxies every request to the app through its own infrastructure, so in production `request.client.host` reflects Render's internal proxy address for effectively all inbound traffic, not the visiting browser's real IP.
- **Why it matters:** `login_rate_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60)` (and the register/refresh/complaint-creation limiters) is meant to throttle *one abusive client*. With the proxy-IP collapse, the limiter instead throttles *the entire user base as one client*: any single script sending 10 bogus `POST /auth/login` requests in 60 seconds exhausts the shared bucket and returns `429` to every other real user attempting to log in, register, refresh their session, or file a complaint for the rest of that sliding window — repeatable indefinitely by re-sending every ~60 seconds. This is the opposite of the intended security control: it turns a defensive feature into a zero-cost, unauthenticated denial-of-service vector against the whole platform, and it simultaneously *fails* to actually rate-limit a distributed attacker (who now shares quota with legitimate traffic instead of being isolated by IP).
- **Reproduction:** Deploy to Render (or any environment behind a reverse proxy that doesn't forward the real client IP), then from any single machine send 10 `POST /auth/login` requests with bad credentials within 60 seconds; verify a legitimate login attempt from a *different* machine is rejected with `429` immediately after. Locally this is invisible because `request.client.host` correctly reflects `127.0.0.1`/direct connections in dev.
- **Recommended fix:** Run uvicorn with `--proxy-headers --forwarded-allow-ips='*'` (or Render's documented egress range) so `request.client.host` is resolved from `X-Forwarded-For`, or add Starlette's `ProxyHeadersMiddleware` explicitly ahead of the rate limiter. Verify post-fix that `request.client.host` reflects distinct real client IPs when tested through the actual Render URL, not just `localhost`.
- **Blocks demo/deployment?** **Yes — should be fixed before production/public deployment.** A demo behind a shared link is lower-risk short-term, but this is a same-day, zero-skill DoS against login for anyone who finds the URL.

### 1.3 — [HIGH] Frontend has no handling for mid-session access-token expiry; users hit a generic broken state instead of silent refresh or redirect-to-login
- **Area:** Frontend / Auth / UX-as-security-boundary interaction
- **Evidence:** `Frontend/src/store/authStore.jsx` only performs a refresh once, inside the mount-time `restoreSession()` effect (lines ~26–60). `Frontend/src/services/api.js`'s `apiRequest` (lines ~26–47) has no response interceptor for `401`; it attaches whatever `getAccessToken()` currently returns and throws a generic `Error` on any non-2xx response. Once a user's 30-minute access token (`ACCESS_TOKEN_EXPIRE_MINUTES` default, `render.yaml`) expires while they remain on an already-loaded page (no full reload), every subsequent API call 401s and is caught individually by whatever page happens to be open, e.g. `OfficerDashboard.jsx:38`'s `catch(err) => setError(err.message)`.
- **Why it matters:** A district officer or inspector mid-shift, actively using the dashboard for more than 30 minutes without a page reload, will start seeing an opaque "request failed" error on every action — not a redirect to `/login` and not a silent background refresh — until they manually reload the page (which re-triggers `restoreSession` and recovers). This is a real usability break for exactly the staff roles this platform is built for, and during a live demo that runs past 30 minutes it will visibly break without an obvious explanation.
- **Reproduction:** Log in, artificially shorten `ACCESS_TOKEN_EXPIRE_MINUTES` (or wait 30 min), then perform any authenticated action without reloading the page — observe a generic error rather than a silent refresh-and-retry or redirect.
- **Recommended fix:** Add a centralized `401` handler in `api.js` — on a `401`, attempt one refresh (single-flight, see 1.3b) and retry the original request once; on refresh failure, clear the session and redirect to `/login` with a "session expired" message rather than surfacing a raw error to the calling page.
- **Blocks demo/deployment?** Not a hard blocker for a short demo, but should be fixed before any real staff usage — this is the exact failure mode a district officer would hit during normal daily use.

### 1.3b — [MEDIUM, forward-looking] No single-flight guard exists for concurrent refresh calls
- **Area:** Frontend / Auth
- **Evidence:** Today there is exactly one refresh call site (mount-time), so this cannot currently race itself. However, `authStore.jsx`'s refresh persists a **rotated** refresh token (correctly implemented — see §4), meaning presenting the same refresh token twice concurrently will have exactly one caller win and the other get rejected/logged-out (by design, per `docs/SECURITY_AND_RBAC.md` §19's reuse-detection). The moment Finding 1.3 is fixed by adding refresh-on-401 from arbitrary call sites (e.g. `OfficerDashboard`'s `Promise.all` of 3 parallel calls all 401ing at once), multiple simultaneous refresh attempts become possible and — without a shared in-flight promise/mutex — would force a spurious logout on legitimate concurrent-tab-safe usage.
- **Why it matters:** This is not exploitable today, but is a near-certain regression the moment 1.3 is fixed naively. Flagging it now so the two fixes are done together correctly.
- **Recommended fix:** When implementing the 1.3 fix, wrap the refresh call in a shared/deduped in-flight promise so concurrent 401s trigger exactly one `/auth/refresh` call, with all callers awaiting the same result.
- **Blocks demo/deployment?** No — purely a note for the 1.3 fix.

### 1.4 — [HIGH] JWT signing secret and database URL are plain `str`, not `SecretStr`; no startup guard against the checked-in insecure default in production
- **Area:** Backend / Secret management
- **Evidence:** `Backend/app/core/config.py:14` (`database_url: str`) and `:21` (`jwt_secret_key: str = "insecure-development-secret-change-me"`) are both plain `str` fields, while `gemini_api_key` and `supabase_service_role_key` were deliberately switched to Pydantic `SecretStr` per `docs/SECURITY_AND_RBAC.md` §18's own stated rationale ("defense-in-depth against a future debug log or unhandled-exception traceback accidentally printing one"). The JWT signing secret is the single most consequential value in the system — anyone who obtains it can forge a valid access token for any user, any role, any district, including `admin`, entirely offline — yet it's the one left unprotected. There is also no `Settings` validator anywhere that refuses to start when `environment == "production"` and `jwt_secret_key` still equals the checked-in placeholder default (a value that is now part of git history and thus effectively public).
- **Why it matters:** If a future unhandled exception or debug log ever prints the `Settings` object (a common accident — e.g. `logger.error(f"Startup failed: {settings}")` or an uncaught exception's local-variable dump in a traceback), the JWT secret and DB connection string would be written to logs/monitoring in plaintext. Separately, if `JWT_SECRET_KEY` is ever left unset in a non-Render deployment path (e.g. someone runs the Docker Compose files directly for something beyond local experimentation, or a future deployment target is added without carrying over `render.yaml`'s `generateValue: true`), the app boots silently with the known default and full authentication is bypassable.
- **Reproduction:** `grep jwt_secret_key Backend/app/core/config.py` shows the plaintext default; no code path validates it's been overridden before serving requests.
- **Recommended fix:** Wrap `jwt_secret_key` and `database_url` in `SecretStr`, unwrapping only where actually needed (`jwt.encode`/`jwt.decode` in `core/security.py`; the SQLAlchemy engine constructor in `core/database.py`). Add a `model_validator` on `Settings` that raises at import time if `environment == "production"` and `jwt_secret_key` still equals the default value.
- **Blocks demo/deployment?** Render's own blueprint (`generateValue: true`) avoids the insecure-default scenario for the *primary* deployment path, so this doesn't block that specific deployment today — but it's a real gap for any other environment and should be closed before this becomes a template for other deployments.

### 1.5 — [MEDIUM] Evidence/RAG-document Supabase Storage bucket privacy is a fully manual setup step with no code-level enforcement or verification
- **Area:** File uploads / Storage / Security
- **Evidence:** `docs/DEPLOYMENT.md` §2 instructs the operator to manually create two Supabase Storage buckets and mark them private. Nothing in `Backend/app/services/storage_service.py` (or anywhere else) verifies bucket ACL at startup or runtime — the app always calls the non-public `/storage/v1/object/...` and `/object/sign/...` endpoints using the service-role key, which functions identically regardless of whether the bucket is actually configured private.
- **Why it matters:** All the ownership/RBAC checks this audit verified as correctly enforced (§4) only govern the backend API. If the underlying bucket is ever toggled public — a single checkbox in the Supabase console, easy to fumble on a fresh project setup or during a later config change — every complaint/inspection evidence photo and video becomes directly fetchable at `{supabase_url}/storage/v1/object/public/{bucket}/{path}` with zero backend authorization involved. The UUID-prefixed storage path (not sequential/enumerable) limits casual discovery, but this is architecturally "one misconfiguration away from full evidence exposure" with no code-level safety net.
- **Reproduction:** Toggle either Storage bucket to public in the Supabase dashboard; fetch a known `storage_path` (e.g. from a captured API response) via the public object URL — succeeds without any auth header.
- **Recommended fix:** Add a startup or periodic health check that queries the bucket's configuration via the Supabase Storage/Management API and fails loudly (or alerts) if `public: true` is detected on either bucket. Document this as a release/monitoring gate, not just a one-time setup instruction.
- **Blocks demo/deployment?** No — but should be added before evidence containing real citizen-submitted photos is handled at any scale.

### 1.6 — [MEDIUM] "Bounded-chunk" upload reads don't actually bound the request at the point that matters; no request-size limit is enforced before the body is fully received
- **Area:** File uploads / Backend / Availability
- **Evidence:** `Backend/app/utils/uploads.py`'s docstring/design claims chunked reading prevents buffering an arbitrarily large body into memory before the size check runs. In practice, by the time an endpoint handler (and therefore `read_upload_bounded`) executes, Starlette/`python-multipart` has already fully received and spooled the entire multipart body (to a `SpooledTemporaryFile`, disk-backed past a small threshold). There is no ASGI-level `Content-Length`-rejecting middleware in `Backend/app/main.py`, and `docs/DEPLOYMENT.md` documents no reverse-proxy/gateway body-size cap on the Render side either. `read_upload_bounded`'s chunk loop only bounds a second, in-process copy of data Starlette already received in full.
- **Why it matters:** A client can force the server to fully receive and disk-spool a multi-gigabyte request before ever getting a size-limit rejection, which is a real (if not severe, given Render Free Tier's own resource caps) disk/bandwidth exhaustion vector — and it partially contradicts the explicit "Request size limits" requirement in `docs/SECURITY_AND_RBAC.md` §11, which the code doesn't fully deliver on. Related: there is no rate limiting at all on the evidence/RAG-document upload endpoints (only `/auth/*` and `POST /complaints` are covered by `app/core/rate_limit.py`), so repeated large authenticated uploads have no throttle either.
- **Reproduction:** Send a multipart upload with a body far exceeding the intended limit to an evidence-upload endpoint; observe the full body is received/spooled before any size-related rejection occurs.
- **Recommended fix:** Reject based on the `Content-Length` header before the body is read where possible, or add an ASGI-level max-body-size middleware; consider a reverse-proxy-level cap as well. Add rate limiting to evidence/RAG-document upload endpoints.
- **Blocks demo/deployment?** No — low real-world severity on Render's own resource-constrained free tier, but worth fixing before higher-traffic use.

### 1.7 — [MEDIUM] Uncommitted OCR retry logic in `app/rag/parsing.py` retries the wrong exception class and silently drops page content on failure with no logging
- **Area:** RAG ingestion / AI
- **Evidence:** `git diff -- Backend/app/rag/parsing.py` (uncommitted local change, not yet part of any commit) adds a 2-attempt retry loop around `_ocr_page_image` that only catches `GeminiRequestError`. Per `Backend/app/services/ai_service.py:100-128`, `GeminiRequestError` is raised for non-retryable failures (bad request, schema/safety rejection) *and* for a genuinely empty response — while the actually-transient failure modes the retry comment describes wanting to handle (`GeminiRateLimitedError` for 429s, `GeminiUnavailableError` for timeouts/5xxs) are a different exception class entirely and are **not** caught by this retry loop, so a real transient hiccup still aborts the whole multi-page ingestion exactly as before. Conversely, after the second `GeminiRequestError` in a row, the function does `return ""` (silently treating the page as having no legible text) with no `logger` import or call anywhere in the file — so a *persistent* cause (e.g., a document repeatedly tripping Gemini's safety filter, or a bad API key) silently drops real regulatory-document content from the RAG knowledge base on every ingestion attempt, with zero operator-visible signal.
- **Why it matters:** This directly undermines `docs/RAG_ARCHITECTURE.md` §11's ingestion-safety requirement to "review parsing quality" — there's currently nothing to review against, since the failure is invisible. It also means the retry's own stated purpose (per its code comment, "rather than failing the entire multi-page document over one flaky page") doesn't actually cover the flaky-page case it was written for.
- **Reproduction:** Not directly reproducible without a way to force `GeminiRequestError` twice in a row on a given page (e.g. a page that trips Gemini's safety filter); code inspection is sufficient to confirm the exception-class mismatch.
- **Recommended fix:** Change the caught exception set to `(GeminiRateLimitedError, GeminiUnavailableError)` to match the pattern already used consistently in every agent's own `_call_gemini_with_retry` helper; keep `GeminiRequestError` non-retried (raise immediately, as before); add a `logger.warning(...)` call before the final `return ""` fallback so a silently-empty page is at least observable in logs/ingestion-status review. No infinite-loop risk exists (bounded at 2 attempts) and `InvalidAiResponseError` handling for malformed JSON is unaffected and correct.
- **Blocks demo/deployment?** No — this is an uncommitted, in-progress change; flagging it now so it's fixed before being committed, since it currently silently under-delivers on its own intent.

### 1.8 — [MEDIUM] Missing composite database indexes recommended by the project's own schema documentation
- **Area:** Database / Performance
- **Evidence:** `docs/DATABASE_SCHEMA.md` §22 recommends composite indexes on `assignments.assigned_to_staff_id + status` and `inspections.inspector_id + inspection_status`. Neither exists: `Backend/app/models/assignment.py` and `alembic/versions/30824dc06f71_add_inspection_assignment_workflow.py` only create single-column indexes (`ix_assignments_assigned_to_staff_id`, `ix_inspections_inspector_id`). These are exactly the columns `assignment_repository.list_by_inspector` and `inspection_repository.list_by_inspector` filter on together (staff_id equality + optional status equality) — the query pattern behind every inspector's "my active cases" dashboard load.
- **Why it matters:** At current/demo data volumes this has no visible effect; as `assignments`/`inspections` grow, these paginated per-inspector queries will do a single-column index scan plus a heap re-check for the status filter instead of an efficient composite index scan — a straightforward, low-risk performance fix identified but not yet applied.
- **Recommended fix:** Add `Index("ix_assignments_staff_status", "assigned_to_staff_id", "status")` and `Index("ix_inspections_inspector_status", "inspector_id", "inspection_status")`, each with a corresponding Alembic migration.
- **Blocks demo/deployment?** No.

### 1.9 — [MEDIUM] `docs/DEPLOYMENT.md`'s production baseline checklist cites a test file that no longer exists
- **Area:** Documentation / Deployment process
- **Evidence:** `docs/DEPLOYMENT.md`'s Production Baseline Checklist cites `app/tests/integration/test_hardening.py` as the verification artifact for "unhandled errors never leak a stack trace." That file was deleted in commit `44db9e9` (Finding 1.1); only stale `.pyc` remnants remain.
- **Why it matters:** A deployer following this checklist literally will hit a dead reference. The underlying behavior it describes is still correctly implemented in code (verified directly in `app/main.py` — see §4), so this is a documentation-accuracy issue, not a live security gap — but it's a symptom of the same root cause as Finding 1.1 and should be corrected alongside it.
- **Recommended fix:** Either restore the cited test (see Finding 1.1's fix) or edit the checklist to describe direct verification steps instead of citing a nonexistent file.
- **Blocks demo/deployment?** No.

### 1.10 — [LOW] District-from-coordinates resolution has no maximum-distance sanity bound
- **Area:** Geographic / PostGIS
- **Evidence:** `Backend/app/services/district_service.py:14-34` (`resolve_district_for_point`) performs pure nearest-centroid matching over all active Maharashtra districts with no cutoff distance. `Backend/app/utils/geo.py:21-31` (`validate_coordinates`) only checks the global-valid range (±90 lat/±180 lon), not proximity to Maharashtra. This nearest-centroid approach is itself a documented, intentional interim design (`docs/DEVELOPMENT_ROADMAP.md` Phase 5 note, pending real polygon-based `ST_Contains` resolution) — the gap flagged here is narrower: there's no upper bound at all.
- **Why it matters:** A coordinate typo, a client-side geolocation glitch, or a complaint genuinely filed from outside Maharashtra will silently resolve to whichever district centroid happens to be nearest and get routed into that district's real operational queue, rather than being flagged as unresolvable/out-of-jurisdiction.
- **Recommended fix:** Add a maximum-distance guard (e.g., reject or flag as `district_uncertain` if the nearest centroid is >150km away) so clearly out-of-state/invalid coordinates surface for review instead of being silently misfiled.
- **Blocks demo/deployment?** No.

### 1.11 — [LOW] RAG PDF ingestion has no page-count cap on the per-page OCR path
- **Area:** RAG ingestion / Availability
- **Evidence:** `Backend/app/rag/parsing.py`'s `_ocr_pdf_page`/PDF-page loop renders every text-less page to an image and calls Gemini OCR once per page, with no maximum page count. Mitigated by admin-only upload gating and the existing `rag_max_upload_size_mb` (20MB) file-size cap, but a crafted PDF with many blank/no-text-layer pages within that size limit would still trigger a correspondingly large number of Gemini API calls in one ingestion request.
- **Why it matters:** Low exploitability (admin-only feature), but worth a bound given it's an unmetered per-document API-call multiplier.
- **Recommended fix:** Add a page-count or total-OCR-call cap per ingestion run.
- **Blocks demo/deployment?** No.

### 1.12 — [LOW] Filename sanitization truncates before computing the file extension, which can false-reject legitimate long filenames
- **Area:** File uploads
- **Evidence:** `Backend/app/utils/validators.py`'s `sanitize_filename` truncates to 150 characters (line ~59) before `_extension_of()` runs. A legitimate filename whose extension falls past the 150-character cut point gets its extension sliced off or mangled, producing a false "extension does not match declared type" rejection.
- **Why it matters:** Fails safe (over-rejects rather than mis-validates), so this is a correctness/UX bug rather than a security hole — but it's a real edge case for descriptive camera/device-generated filenames.
- **Recommended fix:** Truncate the filename stem while preserving the extension, or compute/validate the extension before truncating.
- **Blocks demo/deployment?** No.

### 1.13 — [INFO] Minor documentation/config drift
- `GEMINI_EMBEDDING_DIMENSIONS` (`Backend/app/core/config.py`, default 768) is undocumented in both `Backend/.env.example` and `docs/DEPLOYMENT.md`'s tuning-knobs list — a deployer who changes `GEMINI_EMBEDDING_MODEL` to a model with a different native dimensionality has no signal that this setting exists and needs to match, which would silently break pgvector column dimensions.
- `config.py`'s in-code defaults for `gemini_main_model`/`gemini_reasoning_model` are both the placeholder `"gemini-3.6-flash"` (identical to each other), differing from `render.yaml`'s explicit `gemini-3.7-flash`/`gemini-3.1-pro` values — harmless in the actual Render deployment (which always sets these explicitly) but a stale/confusing fallback for local dev runs without `.env` values populated.
- `docs/DEPLOYMENT.md` states "`Backend/.gitignore` excludes `.env`" — no `Backend/.gitignore` file exists; the exclusion is actually in the root `.gitignore`. Functionally correct, just a misattributed path in the doc.
- Two intentionally-redundant re-checks exist in `assignment_service`/`inspection_service` (re-verifying district scope the caller already validated one line earlier) — harmless defense-in-depth, noted only for completeness.
- Frontend notification unread-count badge only syncs within the same browser tab (a `window` `CustomEvent`, not cross-tab) — cosmetic, not a bug.
- Frontend error normalization (`api.js`'s `parseErrorMessage`) only produces a string message, with no structured HTTP status code attached to thrown errors — this is what forces the ad hoc per-page error handling behind Finding 1.3; worth fixing together with that finding (e.g., a custom `ApiError` carrying `.status`).

---

## 2. Confirmed-Good Areas

The following were independently verified against the actual current code (not merely asserted by documentation) and found to be correctly implemented:

**Authorization / RBAC / District isolation**
- Every officer/inspector endpoint derives district/ownership scope from a fresh server-side DB read (`get_current_staff_profile` → `staff.district_id`, or complaint/inspection ownership fields), never from a client-supplied query/body parameter — verified across officer, inspector, citizen, and admin routers, enforced again at the service layer as defense in depth.
- `get_current_user` re-fetches the `User` row from the database on every request and checks `is_active` live; role checks (`require_roles`) use the live DB-resolved role, not a JWT claim — a demoted or deactivated user cannot exploit stale token claims mid-lifetime.
- Registration (`RegisterRequest`) has no `role`/`district_id` field; staff creation validates role is restricted to inspector/district_officer and is gated behind `require_admin`; admin account creation is out-of-band (`scripts/create_admin.py`), not reachable over HTTP.
- One-active-district-officer-per-district is enforced by a genuine partial unique database index (`uq_one_active_officer_per_district`, verified present in both `staff_profile.py` and migration `0536e568a656`) — not just an application-level check.
- `assignments.complaint_id` / `inspections.complaint_id` both carry real unique constraints; `assignment_service.assign_inspector` correctly catches the resulting `IntegrityError` and converts it to a clean `409`, exactly as documented.
- No general-purpose SQL execution tool exists anywhere in `app/agents`; every AI agent tool takes pre-scoped ORM objects or district-parameterized repository calls (verified at the SQL `WHERE`-clause level, not just by docstring) — cross-district data leakage via an agent tool was not found.
- Citation validation genuinely drops any RAG citation whose source chunk wasn't actually retrieved, rather than persisting an unverifiable citation, in both the Investigation Agent and Inspector Assistant.

**Authentication**
- Refresh-token rotation uses a single atomic conditional `UPDATE ... WHERE id=:id AND revoked_at IS NULL`, genuinely race-safe; reuse-detection correctly distinguishes benign concurrent refresh (multi-tab) from stale-token replay and escalates to full session-family revocation on replay.
- Login timing side-channel is closed — `authenticate()` always runs a bcrypt comparison (against a precomputed dummy hash) even for a nonexistent email.
- Logout and account-deactivation both correctly revoke server-side refresh sessions immediately.
- Frontend correctly persists the *rotated* refresh token after every refresh (not just the new access token).

**File uploads / storage**
- Magic-byte content sniffing, filename sanitization (path separators/`..`/null bytes/unicode all handled), and extension-vs-declared-type cross-checking are all genuinely implemented as documented; no path-traversal or IDOR was found in evidence upload/retrieval across citizen/officer/inspector flows. Storage paths are always built from server-verified IDs plus a UUID prefix, never raw client input.

**Database / migrations**
- `alembic heads` shows a single linear head with no branching; every model checked (`assignment`, `refresh_session`, `complaint`, `district`, `staff_profile`, `inspection`) matches its migrations exactly, including columns, FKs with correct `ondelete` behavior, and the composite `complaints.district_id+status`/`district_id+priority` indexes recommended in the schema doc.
- No raw or string-interpolated SQL exists anywhere in the repository layer.
- Analytics aggregation is genuinely done in SQL (not pulled into Python row-by-row), with correct NULL/zero handling; no N+1 query patterns found in the repository layer.
- Database sessions are always closed via `try/finally`; connection pool settings are explicit and reasonable.
- Cascade/RESTRICT/SET NULL foreign-key behavior is deliberate and consistent — no unintended orphaning or cascade chains.

**AI / RAG**
- No hardcoded Gemini API keys or model names anywhere; the centralized `ai_service.py` layer is used consistently, and vendor error text is never leaked to API clients.
- Every agent prompt includes an explicit "treat as data, never as instructions" guardrail around citizen-submitted text, retrieved RAG content, and OCR'd image text (a real, consistent prompt-injection defense).
- Structured outputs are validated by Pydantic on top of Gemini's own JSON-schema constraint — a malformed model response is a hard failure, never silently coerced.
- Every agent prompt explicitly forbids stating a confirmed violation/enforcement conclusion, matching the human-in-the-loop requirement in `docs/AI_AGENTS_ARCHITECTURE.md` §12.

**Frontend**
- Zero instances of `dangerouslySetInnerHTML`, `innerHTML`, `eval`, or `new Function` anywhere in `Frontend/src` — all AI-generated and user-submitted text (triage summaries, evidence-analysis observations, investigation briefs, assistant chat) is rendered exclusively via escaped JSX text interpolation, eliminating stored-XSS risk from untrusted content.
- Production `vite build` completes cleanly (2,533 modules, no errors); `oxlint` reports no issues.
- Route guards (`ProtectedRoute`, `RoleRoute`) correctly treat the backend as the real authorization boundary and are explicitly commented as UX-only.
- Frontend role constants exactly match backend role enum values — no mismatch found.
- The most recent commit (`71c9a9b`, notification-handling refactor) was reviewed line-by-line and found correct: proper effect cleanup, no stale closures, no memory leak.

**Deployment / configuration**
- Every `render.yaml` environment variable maps to a real `Settings` field with no dead config; `RAG_STORAGE_BUCKET` (a previously-noted documentation gap) is now correctly present in `.env.example`.
- CORS configuration is correct: never wildcarded, paired correctly with `allow_credentials=True`.
- Middleware ordering genuinely achieves what its own docstring claims — `CORSMiddleware` ends up outermost (a non-obvious Starlette behavior), so even a 500-error response carries proper CORS headers.
- Security headers (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`) are set on every response, both at the backend middleware level and the Render static-site edge config for the frontend.
- No secrets are ever logged; `core/logging.py` only calls `logging.basicConfig`, and a repo-wide review of every `logger.*()` call found none logging request bodies, headers, or tokens.
- `alembic upgrade head && uvicorn ...` as the Render start command is genuinely idempotent, safe to re-run on every boot.
- The GitHub Actions refresh-session cleanup workflow correctly sources `DATABASE_URL` from a repo secret, never hardcoded or echoed.
- Dependency versions (`fastapi==0.141.1`, `pydantic==2.10.4`, `pyjwt==2.13.0`, `python-multipart==0.0.32`) show no obviously outdated or known-CVE-affected pins based on available knowledge (a live `pip-audit`/`npm audit` run is still recommended periodically, since this review has no network access to check post-training-cutoff CVEs).

---

## 3. Known Limitations (already documented, reviewed and found reasonable)

- **Single-process, in-memory rate limiter** (beyond the proxy-header bug in Finding 1.2) — a documented, accepted limitation for the single-Render-instance demo target; would need a shared store (Redis) for a genuinely multi-instance deployment.
- **Nearest-district-centroid geographic resolution** rather than true point-in-polygon — documented as an intentional interim approach pending real Maharashtra district boundary data.
- **`GET /businesses` is not district-scoped** — reviewed and documented as an intentional design choice (businesses are a public-directory-style entity, not private case data), not a bug.
- **Docker files are local-experimentation-only**, not part of the actual Render deployment path — internally consistent but not the audited production path.
- **No distributed tracing/APM** — acceptable for the current demo scale; would matter more at production traffic volumes.

---

## 4. Fix Priority

**P0 — before any further development or deployment:**
1. Restore or replace the deleted automated test suite (Finding 1.1) — this is the precondition for safely making any of the other fixes below without risking a silent regression.
2. Fix the rate-limiter proxy-header issue (Finding 1.2) — trivial, low-effort platform-wide DoS otherwise.

**P1 — before real (non-demo) staff usage:**
3. Add mid-session 401/token-refresh handling on the frontend (Finding 1.3), together with the single-flight refresh guard (Finding 1.3b).
4. Wrap `jwt_secret_key` and `database_url` in `SecretStr`; add a startup guard against the insecure default secret in production (Finding 1.4).

**P2 — before scaling beyond the current demo/pilot:**
5. Add code-level verification/monitoring of Supabase Storage bucket privacy (Finding 1.5).
6. Enforce real request-size limiting before the body is fully received; rate-limit upload endpoints (Finding 1.6).
7. Fix the OCR retry-logic exception mismatch and add logging for silently-dropped RAG pages (Finding 1.7).
8. Add the two missing composite database indexes (Finding 1.8).
9. Fix the dead test-file reference in the deployment checklist (Finding 1.9).

**P3 — low-priority polish:**
10–13. District-resolution distance bound, RAG OCR page-count cap, filename-truncation-before-extension bug, and the documentation/config drift items in §1.13.

---

## 5. Final Readiness Assessment

**Demo readiness: Ready.** The application builds cleanly end-to-end (backend imports and serves without error, frontend production build and lint are clean, Alembic migration history is linear and consistent), and the core citizen → officer → inspector → resolution workflow, along with all four AI agents and the RAG-grounded Inspector Assistant, are implemented with genuinely correct authorization scoping at every layer this audit checked.

**Deployment readiness: Conditional.** The underlying architecture is sound and most of the "Phase 12 hardening" claims in the project's own documentation were independently verified as actually implemented correctly (refresh-token rotation, upload validation, CORS/middleware ordering, login timing-attack mitigation, district isolation). However, deployment to a real, publicly-reachable Render instance should not proceed until **Finding 1.2 (rate-limiter DoS)** is fixed — it is a same-day, zero-skill denial-of-service against the login flow for anyone who finds the URL — and **Finding 1.1 (test suite)** should be restored before any further changes are made to authorization-sensitive code, so that the fixes above (and everything already claimed-fixed in the docs) have an actual regression safety net again.

**Security readiness: Good architecture, undermined by two concrete gaps.** Every authorization boundary this audit tested — district isolation, role checks, AI agent tool scoping, file upload ownership, refresh-token revocation — enforces correctly and consistently at the server/database layer, with no raw SQL, no cross-district leakage, and no stored-XSS vector found anywhere in the frontend. The two things standing between this and a genuinely strong security posture are the rate-limiter/proxy-header bug (Finding 1.2, high-impact but a small, well-understood fix) and the complete absence of regression tests (Finding 1.1, which doesn't itself introduce a vulnerability but removes the ability to trust that today's correct state stays correct tomorrow).

---

## 6. Summary of Findings by Severity

| Severity | Count | Findings |
|---|---|---|
| Critical | 1 | 1.1 (deleted test suite) |
| High | 3 | 1.2 (rate-limiter DoS), 1.3 (frontend token-expiry handling), 1.4 (JWT secret not `SecretStr` / no prod-default guard) |
| Medium | 6 | 1.3b (refresh single-flight, forward-looking), 1.5 (storage bucket privacy), 1.6 (upload size limiting), 1.7 (OCR retry logic), 1.8 (missing indexes), 1.9 (dead doc reference) |
| Low | 3 | 1.10 (district-distance bound), 1.11 (RAG OCR page cap), 1.12 (filename truncation) |
| Info | 6 | 1.13 (documentation/config drift items) |
| **Total** | **19** | |

**Most important actions needed, in order:**
1. Restore or intentionally replace the deleted backend and frontend test suites.
2. Fix the rate limiter's client-IP resolution (add proxy-header trust) before any public deployment.
3. Add frontend handling for access-token expiry during an active session.
4. Upgrade `jwt_secret_key`/`database_url` to `SecretStr` and add a production-default guard.
5. Everything else in §4's P2/P3 lists, roughly in the order given.
