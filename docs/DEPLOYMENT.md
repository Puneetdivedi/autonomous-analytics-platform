# Deployment Guide

This platform deploys as **two independent services**:

| Service | Best host | Why |
|---|---|---|
| **Frontend** (Vite SPA) | **Vercel** | Static build, global CDN, instant previews — a perfect Vercel fit. |
| **Backend** (FastAPI + LangGraph) | **Container host** (Fly.io / Render / Railway / your VM) | Needs Postgres, Redis, Qdrant, persistent disk (uploads/reports), long-lived SSE streaming, and a heavy scientific stack — best run as the Docker image we already ship. |

The two connect through one setting: the frontend's build-time
`VITE_API_BASE_URL` points at the backend's public URL, and the backend's
`BACKEND_CORS_ORIGINS` allows the frontend's domain.

> **Why not the backend on Vercel Functions too?** Vercel now runs FastAPI well
> via Fluid Compute, but this backend bundles `pandas + numpy + scipy +
> scikit-learn + statsmodels + matplotlib + reportlab`, which blows past the
> serverless function size budget, and it relies on persistent local files
> (uploads/reports) plus long-running SSE agent streams. Those are container
> workloads. Deploy the **frontend** to Vercel and the **backend** as a
> container. (If you must go all-Vercel, move file storage to Vercel Blob and
> the databases to Marketplace add-ons — Neon Postgres, Upstash Redis — and
> slim the analytics deps; that's a larger change, out of scope here.)

---

## 1. Deploy the frontend to Vercel

Config already committed: [`frontend/vercel.json`](../frontend/vercel.json)
(framework `vite`, SPA rewrite, asset caching).

### Option A — Vercel Dashboard (simplest)

1. Push this repo to GitHub.
2. In Vercel → **Add New… → Project** → import the repo.
3. Set **Root Directory** to `frontend`. Vercel auto-detects Vite
   (build `npm run build`, output `dist`).
4. Add an **Environment Variable**:
   - `VITE_API_BASE_URL` = `https://<your-backend-domain>/api/v1`
5. **Deploy**. You get a production URL like `https://<project>.vercel.app`.

> `VITE_*` vars are inlined at **build time** — after changing it, redeploy.

### Option B — Vercel CLI

```bash
npm i -g vercel                 # if not installed
cd frontend
vercel login                    # interactive (run this yourself)
vercel link                     # link/create the project
vercel env add VITE_API_BASE_URL production   # paste your backend URL
vercel --prod                   # deploy
```

> In Claude Code you can run the interactive login inline by typing:
> `! vercel login`

### Option C — GitHub Actions (auto-deploy on push)

Workflow committed at
[`.github/workflows/deploy-frontend.yml`](../.github/workflows/deploy-frontend.yml).
It is **disabled by default**. To enable:

1. Repo → **Settings → Secrets and variables → Actions**.
2. Add **secrets**: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
   (org/project IDs come from `vercel link`, written to `.vercel/project.json`).
3. Add **variable** `ENABLE_VERCEL_DEPLOY` = `true`.

Every push to `main` that touches `frontend/**` then builds and deploys to prod.

---

## 2. Deploy the backend (container)

The backend image is defined by [`backend/Dockerfile`](../backend/Dockerfile).
Two turnkey paths are committed:

### Option A — Render (one click, includes Postgres)

A blueprint is committed at [`render.yaml`](../render.yaml): a Docker web service
+ a free Postgres, migrations on deploy, CORS pre-pointed at the Vercel frontend,
and `LLM_PROVIDER=stub` so it works with **no API key**.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/Puneetdivedi/autonomous-analytics-platform)

1. Click the button (or Render dashboard → **New + → Blueprint** → pick the repo).
2. Render provisions Postgres, builds the image, runs `alembic upgrade head`, and
   serves it — you get `https://eaap-backend.onrender.com`.
3. For real LLM answers, add `OPENAI_API_KEY` and set `LLM_PROVIDER=openai` in the
   service's Environment tab.

> Free Postgres/instances sleep when idle (≈50 s cold start) and the filesystem is
> ephemeral (uploads reset on redeploy) — fine for a demo; use paid plans + a disk
> for anything real.

### Option B — Fly.io

Config at [`backend/fly.toml`](../backend/fly.toml) (Postgres attach, release-time
migrations, a persistent `/data` volume). Commands are in the file header:
`fly launch --no-deploy` → `fly postgres create/attach` → `fly secrets set …` → `fly deploy`.

### Manual container (any host)

### Provision managed data services

- **PostgreSQL** (Neon, Supabase, RDS, …) → `DATABASE_URL`
  (`postgresql+asyncpg://user:pass@host:5432/db`)
- **Redis** (Upstash, ElastiCache, …) → `REDIS_URL`
- **Qdrant** (Qdrant Cloud or self-hosted) → `QDRANT_URL` (+ `QDRANT_API_KEY`)

Redis and Qdrant are optional — the app degrades gracefully without them.

### Required backend environment

| Variable | Example |
|---|---|
| `SECRET_KEY` | a long random string |
| `DATABASE_URL` | `postgresql+asyncpg://…` |
| `BACKEND_CORS_ORIGINS` | `https://<project>.vercel.app` |
| `LLM_PROVIDER` | `openai` (or `stub` for a keyless demo) |
| `OPENAI_API_KEY` | your key (omit if `LLM_PROVIDER=stub`) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` | optional tracing |

### Run

```bash
docker build -t eaap-backend ./backend
docker run -d -p 8000:8000 --env-file backend.env \
  -v eaap-data:/data eaap-backend
# migrations run automatically via the container command (alembic upgrade head),
# or run manually:  docker exec <container> alembic upgrade head
```

Host this on **Fly.io** (`fly launch` from `backend/`), **Render** (Docker
service), **Railway**, or any VM/orchestrator. Point the frontend's
`VITE_API_BASE_URL` at the resulting `https://…/api/v1`.

---

## 3. Wire the two together

1. Deploy the backend → note its public URL, e.g. `https://api.example.com`.
2. Set backend `BACKEND_CORS_ORIGINS=https://<project>.vercel.app`.
3. Set frontend `VITE_API_BASE_URL=https://api.example.com/api/v1` and redeploy.
4. Visit the Vercel URL, register, create a project, upload a CSV, and ask a
   question — the streaming chat will call your backend.

### Post-deploy checklist

- [ ] `GET https://api.example.com/health` returns `{"status":"ok"}`
- [ ] Frontend loads and `/api/v1/auth/register` succeeds (no CORS errors)
- [ ] `alembic upgrade head` has run against the production DB
- [ ] `LLM_PROVIDER` + provider key set (or `stub` for a no-key demo)
- [ ] SSE streaming works (the chat shows the live agent timeline)

---

## 4. Hosting the static demo pages

`docs/index.html`, `docs/analyzer.html` and `docs/dashboard.html` are **fully
self-contained** (all CSS/JS inline, no external requests) — they run on any
static host. Pick one:

| Host | How | Cost |
|---|---|---|
| **GitHub Pages** (recommended) | Push repo → **Settings → Pages → Source = GitHub Actions**. The included [`deploy-pages.yml`](../.github/workflows/deploy-pages.yml) publishes `docs/` on every push. URL: `https://<user>.github.io/<repo>/analyzer.html` | Free |
| **Netlify** | Drag the `docs/` folder onto [app.netlify.com/drop](https://app.netlify.com/drop) — instant URL, no repo needed | Free |
| **Cloudflare Pages** | Connect the repo, set **build output directory = `docs`**, no build command | Free |
| **Vercel** | New project → set **Root Directory = `docs`**, framework "Other", no build step | Free |

The **working app** (`analyzer.html`) does all parsing, aggregation, statistics
and charting **in the browser**, so it needs no server. The **full product** (with
the LLM agents, Postgres persistence and multi-user auth) is the FastAPI backend +
React frontend in sections 1–3.

> These demos were **not** hosted on Claude; if you previously published them as
> Claude Artifacts, remove them at `claude.ai/code/artifacts`.

---

## Quick all-in-one (single host, no Vercel)

For a demo on one machine, skip Vercel and run everything with Docker Compose:

```bash
cp .env.example .env      # add a provider key, or set LLM_PROVIDER=stub
docker compose up --build
```

Frontend → `:5173`, backend → `:8000`, LangFuse → `:3000`.
