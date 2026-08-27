# RAG Architecture

## 1. Purpose

The RAG system provides the Inspector Assistant with grounded access to authoritative food-safety regulations, inspection guidance, sampling procedures, and department SOPs.

## 2. Source Priority

Prefer sources in this order:

1. Current department SOPs supplied by the relevant authority.
2. Current official FSSAI regulations/guidance.
3. Official Maharashtra government/departments documents.
4. Other authoritative public-sector material approved for the project.

Do not treat arbitrary web pages as regulatory truth.

## 3. Knowledge Categories

Recommended document groups:

```text
knowledge_base/
├── laws/
├── regulations/
├── inspection_guidelines/
├── hygiene_guidelines/
├── sampling_procedures/
├── recall_procedures/
├── licensing/
└── department_sops/
```

## 4. Ingestion Pipeline

```text
PDF / DOCX / Approved Web Source
        |
        v
Document validation
        |
        v
Text extraction
        |
        v
Section-aware parsing
        |
        v
Chunking
        |
        v
Metadata enrichment
        |
        v
Embedding generation
        |
        v
Supabase PostgreSQL + pgvector
```

## 5. Metadata

Every chunk should contain enough metadata to identify and filter its source.

Example:

```json
{
  "document_id": "...",
  "title": "Restaurant Inspection Guidance",
  "source_organization": "FSSAI",
  "document_type": "inspection_guideline",
  "version": "...",
  "effective_date": "...",
  "page_number": 12,
  "section_title": "Personal Hygiene",
  "business_type": "restaurant",
  "jurisdiction": "India"
}
```

## 6. Chunking

Do not blindly chunk by fixed character count.

Prefer section-aware chunks that preserve:

- heading
- subsection
- definitions
- lists
- procedure steps
- tables where extraction is reliable

Chunk size should be empirically evaluated based on retrieval quality.

## 7. Embeddings

Use one embedding model consistently within a collection/version.

Store the embedding alongside chunk metadata in pgvector when using Supabase PostgreSQL.

When changing embedding models, rebuild the affected collection rather than mixing incompatible vectors without a documented plan.

## 8. Retrieval

The Inspector Assistant should use a retrieval pipeline such as:

```text
User question
   |
   v
Query understanding
   |
   +--> metadata filters
   |
   v
Vector search
   |
   +--> optional keyword/hybrid search
   |
   v
Reranking
   |
   v
Top relevant chunks
   |
   v
LLM answer generation
```

Filters can include:

- document type
- business type
- jurisdiction
- document version
- effective date

## 9. Citation Requirements

Every regulatory answer should expose source information:

```text
Source: document title
Page: 12
Section: Personal Hygiene
```

The agent must not present a regulatory statement as sourced if retrieval did not return supporting evidence.

## 10. Freshness and Versioning

Documents should maintain:

- version
- effective date
- publication date where available
- superseded status
- source URL/path
- checksum

When a newer official document replaces an older one, mark the old document as superseded rather than deleting it if historical traceability is required.

## 11. Ingestion Safety

Before a document enters the production knowledge base:

- verify source authority
- verify file integrity
- record source metadata
- detect duplicate checksums
- review parsing quality
- validate page/section references

## 12. RAG Administration

Admin or authorized knowledge managers should be able to:

- upload documents
- inspect metadata
- trigger ingestion
- see ingestion status
- deactivate a source
- inspect retrieval failures

## 13. Retrieval Evaluation

Create a benchmark of realistic inspector questions and expected source sections.

Measure:

- recall@k
- precision@k
- source correctness
- citation correctness
- answer groundedness
- refusal/uncertainty behavior

## 14. RAG and Agent Boundary

RAG retrieves knowledge. The agent decides how to use the retrieved context within its workflow.

The application still enforces authorization and case scope outside the LLM.
