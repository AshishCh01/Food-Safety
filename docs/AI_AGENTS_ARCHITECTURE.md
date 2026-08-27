# AI Agents Architecture

## 1. Purpose

The AI layer assists citizens and department staff with classification, evidence analysis, investigation support, regulatory retrieval, and report preparation.

AI is an assistant layer. Final regulatory, enforcement, inspection, or legal decisions remain with authorized human staff.

## 2. Agent Set

Initial agents:

1. Complaint Triage Agent
2. Evidence Analysis Agent
3. Investigation Agent
4. Inspector Assistant Agent
5. Report Generation Agent

These should share infrastructure and controlled tools rather than being duplicated applications.

## 3. Orchestration

Use an explicit orchestrator/state machine rather than unrestricted agent-to-agent conversation.

```text
Event / User Request
       |
       v
 Agent Orchestrator
       |
  +----+-----+---------+----------------+
  |          |         |                |
  v          v         v                v
Triage    Evidence  Investigation   Inspector
Agent      Agent       Agent         Assistant
```

The orchestrator should track:

- agent/task ID
- user ID
- role
- district scope
- input references
- selected tools
- tool results
- final structured result
- citations where relevant
- status/error
- latency/token metadata where available

## 4. Complaint Triage Agent

### Goal

Convert unstructured citizen complaints into structured information.

### Inputs

- complaint text
- selected category, if any
- location/business information
- optional evidence metadata

### Outputs

```json
{
  "category": "spoiled_food",
  "summary": "Potentially spoiled food reported by citizen.",
  "priority_suggestion": "high",
  "entities": {
    "business_name": "...",
    "product": "..."
  },
  "missing_information": ["purchase_date"],
  "confidence": 0.86
}
```

The priority is a recommendation for staff review, not an enforcement decision.

## 5. Evidence Analysis Agent

### Goal

Assist with evidence interpretation.

Capabilities may include:

- OCR extraction.
- Expiry/best-before date extraction.
- Image observation.
- Basic metadata validation.
- Evidence summarization.

Example pipeline:

```text
Image
 -> OCR
 -> vision analysis
 -> normalized observations
 -> evidence record
```

Never state an uncertain model output as a confirmed legal violation.

## 6. Investigation Agent

### Goal

Produce an investigation brief from authorized application data.

Tools:

- `get_business_details`
- `get_complaint_history`
- `get_inspection_history`
- `find_similar_complaints`
- `get_case_timeline`
- `search_regulations`
- `get_evidence_summary`

The agent must receive the authenticated user's scope and all database tools must enforce that scope.

## 7. Inspector Assistant Agent

### Goal

Help inspectors interpret relevant procedures and organize an inspection.

Examples:

- "What should I check for an expired packaged food complaint?"
- "Show the relevant inspection procedure."
- "Summarize this case before my inspection."
- "Prepare an inspection checklist based on the complaint type."

It should combine:

- complaint data
- inspection data
- evidence summaries
- RAG results

## 8. Report Generation Agent

### Goal

Generate a draft report from verified structured information and inspector notes.

Rules:

- Never invent findings.
- Never create unsupported facts.
- Preserve source data exactly where legal/operational wording matters.
- Mark generated prose as draft until an authorized person approves it.

## 9. Agent Tools

Agents should call narrow, typed tools.

Examples:

```text
get_complaint(id)
get_business(id)
get_complaint_history(business_id)
get_inspection_history(business_id)
search_regulations(query, filters)
find_similar_complaints(complaint_id)
get_evidence(evidence_id)
create_inspection_checklist(case_id)
create_report_draft(inspection_id)
```

There must not be a general-purpose `execute_sql` tool.

## 10. Tool Authorization

Every tool invocation should enforce:

```text
authenticated user
       +
role permission
       +
district scope
       +
resource ownership/authorization
```

The LLM cannot override these constraints.

## 11. Structured Outputs

Prefer JSON schema/Pydantic models for machine-consumed agent outputs.

This reduces parsing failures and makes validation/testability easier.

## 12. Human-in-the-Loop Rules

Require human confirmation for:

- complaint rejection/closure
- final violation determination
- regulatory enforcement action
- official inspection findings when entered into the record
- penalties or legal notices
- permanent deletion of evidence/cases

Agents can recommend, summarize, draft, and surface anomalies.

## 13. Memory

Do not give an agent unrestricted long-term memory.

Store durable facts in the application database. Agent conversation context should be scoped to the case/user and should not silently become operational truth.

## 14. Evaluation

Create a test set of representative complaints and expected structured results.

Measure:

- classification accuracy
- extraction accuracy
- evidence observation accuracy
- retrieval relevance
- citation correctness
- hallucination rate
- tool authorization failures
- response latency

## 15. Failure Handling

When confidence is low or sources conflict:

1. Do not fabricate.
2. Tell the user/inspector that confidence is low.
3. Show available evidence/source material.
4. Route the case to human review where appropriate.

## 16. Agent Logging

Log metadata, not secrets:

- execution ID
- agent name/version
- user and role
- district scope
- tools invoked
- retrieval sources
- output validation status
- duration
- error reason

Avoid storing sensitive prompts/evidence beyond required retention policies.
