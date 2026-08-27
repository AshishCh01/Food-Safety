# Security and RBAC

## 1. Purpose

This document defines access control and security requirements for the Maharashtra Food Safety Complaint and Inspection Platform.

## 2. Roles

```text
Citizen
Inspector
District Officer
Admin
```

## 3. Role Permissions

### Citizen

Can:

- register/login
- create complaints
- upload complaint evidence
- view own complaints
- view own complaint timeline
- receive notifications

Cannot:

- access another user's complaint records
- access staff dashboards
- assign inspectors
- modify official findings
- access private regulatory/admin data unless exposed through an approved public workflow

### Inspector

Can:

- view assigned inspections
- view authorized complaint/evidence data
- create/update inspection records
- upload inspection evidence
- add findings
- use Inspector Assistant
- draft inspection reports

Cannot:

- access unrelated districts
- assign themselves arbitrary cases
- modify another inspector's cases without explicit authorization
- make admin account changes
- finalize regulatory enforcement decisions reserved for officers

### District Officer

Can:

- view complaints within their district
- review/verify/reject complaints
- assign inspectors in their district
- view district analytics
- review inspection reports
- use investigation/inspector assistance tools available to the role

Cannot:

- access another district's operational data
- manage statewide admin settings
- create arbitrary admin accounts

### Admin

Can:

- manage users and staff
- manage districts and business master data
- view statewide analytics
- manage approved RAG documents
- inspect audit logs
- configure system-level settings

Admin access should be tightly controlled and auditable.

## 4. District Isolation

District isolation is a mandatory server-side rule.

Every district-scoped staff identity has a `district_id`.

Example:

```text
Pune Officer
 -> district_id = PUNE
 -> permitted complaint scope = PUNE
```

A request such as:

```text
GET /officer/complaints?district_id=NAGPUR
```

must not allow a Pune officer to switch scope.

The backend must derive scope from the authenticated user.

## 5. Authorization Layers

Use defense in depth:

```text
Authentication
   -> role check
   -> district scope check
   -> object ownership/assignment check
   -> business rule check
   -> database action
```

## 6. Authentication Security

- Use strong password hashing if application passwords are used.
- Never store plaintext passwords.
- Use secure, expiring access tokens.
- Rotate refresh tokens where supported.
- Verify email/phone according to the chosen authentication design.
- Rate-limit login and password reset endpoints.
- Implement account disablement.

## 7. Staff Account Provisioning

Citizens may self-register.

Staff accounts should be provisioned through controlled admin or departmental onboarding workflows.

Never let a public registration parameter such as `role=admin` create an elevated account.

## 8. Evidence Security

Complaint photos and videos may contain sensitive information.

Requirements:

- authorize access before serving evidence
- use private storage buckets where appropriate
- use short-lived signed URLs when needed
- validate file type and size
- scan/validate uploads where operationally feasible
- prevent path traversal
- record uploader and timestamps

## 9. AI Security

AI agents must not bypass RBAC.

Bad design:

```text
Agent -> arbitrary SQL -> database
```

Good design:

```text
Agent
 -> controlled tool
 -> authorization-aware service
 -> repository
 -> database
```

Agents must not independently:

- promote their own permissions
- delete cases
- change staff roles
- issue enforcement actions
- expose data from other districts

## 10. Prompt Injection Defense

Treat user complaint text, uploaded documents, and retrieved text as untrusted content.

Do not let embedded instructions in evidence or retrieved documents override system/tool authorization.

Tools should verify permissions independently of model instructions.

## 11. API Security

- HTTPS in production.
- Strict CORS configuration.
- Request size limits.
- Input validation.
- Rate limiting for abuse-prone endpoints.
- Safe error handling.
- Security headers at the edge.
- Dependency vulnerability monitoring.

## 12. Audit Logging

Record security-sensitive events:

- login success/failure
- account activation/deactivation
- role changes
- district assignments
- case assignment changes
- status changes
- evidence access/deletion where required
- admin actions
- AI tools that perform operational mutations

## 13. Secret Management

Never commit:

- database passwords
- JWT secrets
- Supabase service-role secrets
- AI provider keys
- storage credentials

Use `.env` locally and managed secret storage in production.

## 14. Supabase Key Separation

Keep public client-side keys separate from privileged server credentials.

Privileged service-role credentials must never be shipped to the frontend.

## 15. Data Retention

Define retention rules for:

- complaints
- evidence
- inspection reports
- AI logs
- audit logs
- RAG documents

Retention must follow the actual department/legal requirements once those are provided by the project authority.

## 16. Security Testing

Minimum test categories:

- unauthorized endpoint access
- cross-district access attempts
- cross-user complaint access
- privilege escalation
- token/session misuse
- file upload abuse
- prompt injection attempts
- agent tool authorization
- SQL injection/input validation

## 17. Security Principle

The LLM, frontend, and client are all untrusted from an authorization perspective. The backend is the enforcement boundary.
