# Maharashtra Food Safety Complaint & Inspection Platform

Phase 1 (Project Foundation) is implemented: a FastAPI backend, a React (Vite) frontend, SQLAlchemy + Alembic wired to Supabase PostgreSQL, Docker, and baseline tests.

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

Run tests:

```bash
cd Backend
pytest
```

## Frontend

```bash
cd Frontend
npm install
cp .env.example .env
npm run dev
```

Run tests:

```bash
cd Frontend
npm test
```

## Docker

```bash
docker compose up --build
```

This starts the backend on `:8000` and the frontend dev server on `:5173`. Both containers read their configuration from `Backend/.env` and `Frontend/.env`, so create those from the `.env.example` files first.

## Database migrations

Schema changes go through Alembic:

```bash
cd Backend
alembic revision --autogenerate -m "description"
alembic upgrade head
```

Always review generated migrations before applying them.
