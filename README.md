# Maharashtra Food Safety Complaint & Inspection Platform

A FastAPI backend and React (Vite) frontend, backed by Supabase (PostgreSQL + PostGIS + pgvector + Storage) and the Google Gemini API, implementing citizen complaint intake, officer/inspector workflows, and AI-assisted triage, evidence analysis, RAG-grounded inspector assistance, and investigation briefs. Phases 1-12 (foundation through security/performance hardening) are complete - see [`docs/DEVELOPMENT_ROADMAP.md`](docs/DEVELOPMENT_ROADMAP.md) for the full phase history.

See [`docs/PROJECT_SPEC.md`](docs/PROJECT_SPEC.md) and [`docs/ARCHITECTURE_TREE.md`](docs/ARCHITECTURE_TREE.md) for the full project design and later phases.

## Prerequisites

- Python 3.13
- Node.js 22+
- Docker Desktop (optional, for containerized dev)
- A Supabase PostgreSQL connection string

## Backend

```bash
cd Backend
python -m venv venv          # already created in this repo
venv/Scripts/activate         # Windows
pip install -r requirements.txt
cp .env.example .env          # then set DATABASE_URL to your Supabase connection string
alembic upgrade head
uvicorn app.main:app --reload
```

Health check: `GET http://localhost:8000/health`

## Frontend

```bash
cd Frontend
npm install
cp .env.example .env
npm run dev
```

## Docker (local experimentation only)

```bash
docker compose up --build
```

This starts the backend on `:8000` and the frontend dev server on `:5173`. Both containers read their configuration from `Backend/.env` and `Frontend/.env`, so create those from the `.env.example` files first.

Docker is **not** part of the deployment path (see below) - it exists only as an optional way to run both services locally without installing Python/Node directly.

## Deployment

The project deploys to **Render Free Tier** (no Docker) with Supabase remaining the managed PostgreSQL/Storage/PostGIS/pgvector platform and Gemini as the external AI provider. The repository root's [`render.yaml`](render.yaml) is a Render Blueprint that provisions both services as infrastructure-as-code.

See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for the full setup walkthrough, the required environment variables, and the production smoke-test checklist.

## Database migrations

Schema changes go through Alembic:

```bash
cd Backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

Always review generated migrations before applying them.
