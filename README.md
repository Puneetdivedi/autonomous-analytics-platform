# Enterprise Autonomous Analytics Platform

> A production-grade, multi-agent AI analytics platform where specialized AI agents
> collaborate to answer business questions from structured enterprise data —
> autonomously planning, inspecting schemas, generating & validating SQL, executing
> queries, running statistics, generating charts, producing insights, recommending
> actions, and generating downloadable reports — with full LangFuse observability.

**🔗 Live demos** (hosted on GitHub Pages — self-contained, no backend / no API key):

- **▶ Working app** — upload a CSV and watch the pipeline run:
  **https://puneetdivedi.github.io/autonomous-analytics-platform/analyzer.html**
- **📊 Observability dashboard** — snapshot of a traced run:
  **https://puneetdivedi.github.io/autonomous-analytics-platform/dashboard.html**
- **Landing page:** https://puneetdivedi.github.io/autonomous-analytics-platform/
- **🚀 Full app, fully wired (Vercel):** https://autonomous-analytics-frontend.vercel.app
  — the real product UI, connected to a live serverless backend
  (https://autonomous-analytics-backend.vercel.app). Opens with no sign-in
  (auto guest) and runs the complete 13-agent pipeline in keyless `stub` mode.
  _Free-tier notes: first request has a ~10 s cold start; the demo DB is
  ephemeral SQLite (data resets on redeploy). Add `OPENAI_API_KEY` +
  `LLM_PROVIDER=openai` in the backend project for real LLM answers._

Auto-deployed on every push via
[`.github/workflows/deploy-pages.yml`](.github/workflows/deploy-pages.yml).
Sources: [`docs/analyzer.html`](docs/analyzer.html), [`docs/dashboard.html`](docs/dashboard.html).

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Agent Graph (LangGraph Supervisor)](#agent-graph-langgraph-supervisor)
4. [Tech Stack](#tech-stack)
5. [Folder Structure](#folder-structure)
6. [Installation](#installation)
7. [Environment Variables](#environment-variables)
8. [Running the Platform](#running-the-platform)
9. [API Documentation](#api-documentation)
10. [Flow Diagram](#flow-diagram)
11. [Screenshots](#screenshots)
12. [Testing](#testing)
13. [Deployment Guide](#deployment-guide)
14. [License](#license)

---

## Overview

**Enterprise Autonomous Analytics Platform (EAAP)** is an AI system that turns
natural-language business questions into rigorous, explained, chart-backed answers.

**Example**

> _"Why did revenue decrease in North America last month?"_

The platform autonomously:

1. **Understands** the request (intent detection)
2. **Plans** an execution strategy
3. **Inspects** the database schema
4. **Generates** SQL
5. **Validates** the SQL (safety + correctness)
6. **Executes** the SQL
7. **Analyzes** returned data (statistics, correlation, regression, forecasting)
8. **Generates** charts (auto-selected chart type)
9. **Explains** the findings (executive summary, root-cause analysis)
10. **Recommends** business actions (risks & opportunities)
11. **Reflects** on quality and retries when needed
12. **Generates** a downloadable report (PDF / Word / Excel)
13. **Tracks** everything in **LangFuse**

---

## Architecture

The backend follows **Clean Architecture** + **Domain-Driven Design**:

```
┌──────────────────────────────────────────────────────────────────┐
│                         API Layer (FastAPI)                        │
│  routers · middleware · dependency injection · auth · streaming    │
├──────────────────────────────────────────────────────────────────┤
│                        Service Layer                               │
│   orchestrates use-cases · transaction boundaries · agent runner   │
├──────────────────────────────────────────────────────────────────┤
│                     Agent / Graph Layer                            │
│   LangGraph Supervisor · specialized agents · tools · prompts      │
├──────────────────────────────────────────────────────────────────┤
│                      Repository Layer                              │
│         persistence abstraction over SQLAlchemy models             │
├──────────────────────────────────────────────────────────────────┤
│              Infrastructure (Postgres · Redis · Qdrant)            │
└──────────────────────────────────────────────────────────────────┘
```

**Key principles**

- Dependencies point **inward**: API → Service → Repository → Model.
- Agents/tools depend only on abstractions (LLM factory, data-source adapters).
- Everything async where I/O bound; Pydantic V2 for all boundaries.
- Full observability: every LLM call, agent node, retry & failure traced.

---

## Agent Graph (LangGraph Supervisor)

```
                    ┌─────────────────┐
                    │  Intent Detect  │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │     Planner     │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │    Metadata     │  (schema inspection)
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  SQL Generator  │◄────────┐
                    └────────┬────────┘         │ retry
                             ▼                  │
                    ┌─────────────────┐         │
                    │  SQL Validator  │─────────┘
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │    Execution    │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │   Statistical   │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  Visualization  │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │     Insight     │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Recommendation  │
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │   Reflection    │──── needs work? ──► back to Planner
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │ Report Generator│
                    └────────┬────────┘
                             ▼
                    ┌─────────────────┐
                    │  LangFuse Log   │
                    └────────┬────────┘
                             ▼
                            END
```

Each node lives in its own file under `backend/app/graphs/nodes/`.

---

## Tech Stack

**Backend:** FastAPI · Python 3.12 · LangChain · LangGraph · LangFuse ·
SQLAlchemy 2 · Alembic · PostgreSQL · Redis · Qdrant · Pydantic V2 · JWT · Docker

**Frontend:** React · TypeScript · TailwindCSS · React Query · React Router ·
Recharts · Axios

**LLM Providers:** OpenAI · Anthropic · Gemini · Groq · Ollama (pluggable factory)

---

## Folder Structure

```
backend/
  app/
    api/            # FastAPI routers + deps
    agents/         # specialized agents
    graphs/         # supervisor graph + nodes
    services/       # use-case orchestration
    repositories/   # persistence abstraction
    database/       # session, base, seeds
    models/         # SQLAlchemy ORM models
    schemas/        # Pydantic DTOs
    middleware/     # request/exception/logging middleware
    core/           # config, security, logging, DI
    prompts/        # agent system prompts
    tools/          # LangChain tools
    memory/         # conversation/project/long-term memory
    observability/  # LangFuse integration
    utils/          # shared helpers
  alembic/          # migrations
  tests/            # pytest unit + integration
frontend/
  src/
    components/ pages/ hooks/ services/ context/ types/
```

---

## Installation

### Prerequisites

- Docker & Docker Compose
- (Local dev) Python 3.12, Node.js 20+

### Quick start (Docker)

```bash
cp .env.example .env          # fill in your keys
docker compose up --build
```

- Backend → http://localhost:8000 (docs at `/docs`)
- Frontend → http://localhost:5173
- LangFuse → http://localhost:3000

### Try it with no API key (stub LLM)

Set `LLM_PROVIDER=stub` to run the **entire agent graph** without any provider
key — the stub returns deterministic, schema-valid outputs by reading the real
schema/rows/statistics from each prompt, so SQL executes against your data and
charts/reports are generated for real. Great for demos, CI, and tests.

```bash
LLM_PROVIDER=stub uvicorn app.main:app --reload
```

### Local dev (backend)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # win: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload
```

### Local dev (frontend)

```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables

See [`.env.example`](.env.example). Highlights:

| Variable | Description |
|---|---|
| `SECRET_KEY` | JWT signing secret |
| `DATABASE_URL` | Postgres DSN (app metadata) |
| `REDIS_URL` | Redis DSN (cache/memory/streaming) |
| `QDRANT_URL` | Qdrant vector store URL |
| `LLM_PROVIDER` | `openai` \| `anthropic` \| `gemini` \| `groq` \| `ollama` |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` / `GROQ_API_KEY` | provider keys |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | observability |

---

## Running the Platform

```bash
docker compose up --build        # everything
docker compose up postgres redis qdrant   # infra only, run app locally
```

---

## API Documentation

Interactive OpenAPI docs are served at `http://localhost:8000/docs`.

| Group | Endpoints |
|---|---|
| Auth | `POST /api/v1/auth/register`, `/login`, `/refresh`, `GET /me` |
| Projects | CRUD `/api/v1/projects` |
| Upload | `POST /api/v1/datasources/upload` (CSV/Excel), connection registration |
| Chat | `POST /api/v1/chats`, `POST /api/v1/chats/{id}/messages` (SSE stream) |
| Reports | `GET /api/v1/reports`, `GET /api/v1/reports/{id}/download` |
| Agents | `GET /api/v1/agents/executions`, status |
| Tracing | `GET /api/v1/traces` (LangFuse proxy) |

---

## Flow Diagram

See [Agent Graph](#agent-graph-langgraph-supervisor) above and
`docs/ARCHITECTURE.md` for sequence diagrams.

---

## Screenshots

> _Placeholders — replace with real screenshots after first run._

| Page | Screenshot |
|---|---|
| Dashboard | `docs/screenshots/dashboard.png` |
| Chat | `docs/screenshots/chat.png` |
| Trace Viewer | `docs/screenshots/traces.png` |
| Reports | `docs/screenshots/reports.png` |

---

## Testing

```bash
cd backend
pytest                     # all
pytest -m unit             # unit only
pytest -m integration      # integration
pytest --cov=app           # coverage
```

---

## Deployment Guide

Full instructions: **[`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)**.

The platform deploys as two services:

- **Frontend → Vercel.** The Vite SPA has a committed
  [`frontend/vercel.json`](frontend/vercel.json); import the repo with
  **Root Directory = `frontend`** and set `VITE_API_BASE_URL` to your backend
  URL. Optional auto-deploy workflow at
  [`.github/workflows/deploy-frontend.yml`](.github/workflows/deploy-frontend.yml).
- **Backend → container.** Build [`backend/Dockerfile`](backend/Dockerfile) and
  run it on Fly.io / Render / Railway / a VM with managed Postgres, Redis and
  Qdrant; set `BACKEND_CORS_ORIGINS` to the Vercel domain. Migrations run on
  boot (`alembic upgrade head`).

Single-host demo: `docker compose up --build` (see [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md)).

---

## License

MIT © 2026 Puneet Divedi — see [LICENSE](LICENSE).
