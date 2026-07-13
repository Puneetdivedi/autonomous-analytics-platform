# Build Notes — What We Built and Why

This document is the narrative companion to the code: what was built, in what
order, and the reasoning behind each decision. It complements
[`ARCHITECTURE.md`](ARCHITECTURE.md) (structure) and the root
[`README.md`](../README.md) (usage).

## Goal

Build a **production-grade, multi-agent autonomous analytics platform** — not a
demo. A user asks a business question in natural language; a graph of
specialized AI agents plans, writes & validates SQL, executes it, runs
statistics, builds charts, explains findings, recommends actions, and produces a
downloadable report — all traced in LangFuse.

## Build order (and why)

We built inside-out so every layer rested on a stable contract:

1. **Foundation & contracts first.** Config, logging, security, exceptions, DB
   base/session, ORM models, and the `AnalyticsState` LangGraph contract.
   *Why:* these are imported by everything; locking them first prevents
   interface drift when work is parallelized.
2. **Pydantic schemas + LLM factory + observability + base classes.** The DTOs,
   the multi-provider LLM factory (with fallback), LangFuse wiring, and the
   `BaseAgent` contract. *Why:* they define how agents/tools/nodes talk to each
   other.
3. **Breadth in parallel.** Four independent workstreams built concurrently:
   agents+prompts, tools+data-sources+memory, repositories+services+API+Alembic,
   and the React frontend. *Why:* these are large but well-isolated once the
   contracts exist.
4. **Integration glue (built last, by hand).** Graph nodes, the supervisor graph
   builder, the streaming runner, and the analytics/chat services that bind the
   graph to persistence and SSE. *Why:* this is where all layers meet, so it was
   written against the *real* signatures the parallel work produced and verified
   end-to-end.

## Key design decisions

| Decision | Why |
|---|---|
| **Clean Architecture + Repository/Service layers** | Testable, swappable persistence; the graph never touches the ORM directly. |
| **`AnalyticsState` as a `TypedDict` with `operator.add` reducers** | LangGraph merges partial node updates safely; append-only channels (`executions`, `events`, `errors`) never clobber each other across retries. |
| **Agents = structured-output LLM units (`BaseAgent[TOut]`)** | Every agent returns a validated Pydantic model, so downstream nodes get typed data, not free text. Retries (tenacity) + fallback LLM live in the base class. |
| **Deterministic numeric core, LLM interprets** | `statistics_tool` computes the numbers; the Python Analyst agent *interprets* them. The model never invents statistics. |
| **Uniform `DataSourceAdapter`** | CSV/Excel are loaded into in-memory SQLite so the exact same SQL pipeline runs over files and real databases. |
| **SQL safety is defense-in-depth** | A deterministic `validate_sql` (SELECT-only, single-statement, auto-`LIMIT`) runs *and* an LLM validator reviews; both must pass. |
| **Two graph retry loops** | `sql_validator → sql_generator` (fix bad SQL) and `reflection → planner` (improve a weak answer), each capped by a retry budget and a hard `MAX_GRAPH_ITERATIONS`. |
| **Everything optional degrades gracefully** | Redis, Qdrant and LangFuse being down never crashes the app — memory/tracing simply no-op. |
| **SSE streaming** | The runner streams `node_start`/`node_end`/`artifact`/`done` events so the ChatGPT-style UI shows the agents working live. |

## Notable fixes made during verification

- **`passlib` → direct `bcrypt`.** `passlib` 1.7 is incompatible with modern
  `bcrypt`; we hash with `bcrypt` directly (with correct 72-byte handling).
- **`EmailStr` rejects reserved TLDs.** Seed/test emails moved off `.local`
  (reserved) to a valid domain so registration validates.
- **CSV `"NA"` preserved.** pandas silently turns `"NA"` into `NaN`; since the
  flagship example is *North America*, we preserve `NA`/`N/A` as literal strings.

## Verification performed

- Whole backend byte-compiles; the full FastAPI app imports and assembles.
- The LangGraph supervisor compiles with all 13 nodes.
- **21 passing tests** (unit + integration): security/JWT, SQL-tool safety,
  statistics engine, graph build, and the auth + projects APIs over an in-memory
  DB.
- End-to-end offline data path proven: CSV → in-memory SQLite → schema
  introspection → aggregate SQL.
- `ruff check` and `ruff format --check` clean across `app` and `tests`.

## What requires real credentials to run fully

The LLM-driven nodes (intent → planner → SQL → insight → recommendation →
reflection) need a provider key (`OPENAI_API_KEY`, etc.). Set one in `.env` and
run `docker compose up` to exercise the complete autonomous flow. All
deterministic layers (auth, data sources, SQL execution, statistics, charts,
report generation, observability plumbing) run without any model key.
