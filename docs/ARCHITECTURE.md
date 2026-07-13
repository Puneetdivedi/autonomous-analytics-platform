# Architecture

This document explains how the **Enterprise Autonomous Analytics Platform (EAAP)**
is structured and how a question flows through the system.

## 1. Layered (Clean) Architecture

```
API (FastAPI routers, middleware, DI)
      │  depends on
Services (use-cases, transactions, orchestration)
      │  depends on
Agents / Graph (LangGraph supervisor, agents, tools)   Repositories (persistence)
      │                                                        │
      └────────────────► Domain models / schemas ◄─────────────┘
                                   │
        Infrastructure: PostgreSQL · Redis · Qdrant · LLM providers
```

**Dependency rule:** inner layers never import outer layers. Routers depend on
services; services depend on repositories and the graph runner; the graph depends
on agents/tools; agents/tools depend on schemas and the LLM factory.

## 2. Request lifecycle (a question)

```
POST /api/v1/chats/{id}/messages { question, datasource_id, stream:true }
   │
   ▼
ChatService.ask()
   │  persists user Message, creates trace_id
   ▼
AnalyticsService.run()
   │  resolves DataSource -> adapter, introspects schema
   │  builds initial AnalyticsState
   ▼
LangGraph Supervisor.astream()
   │  nodes execute, each emits StreamEvents + records AgentExecution
   ▼
SSE stream back to the client (node_start/node_end/artifact/token/done)
   │
   ▼
Final assistant Message persisted with artifacts + trace_id
```

## 3. The Supervisor Graph

Nodes (each in `app/graphs/nodes/`):

| # | Node | Agent | Produces |
|---|------|-------|----------|
| 1 | intent_detection | IntentAgent | `intent` |
| 2 | planner | PlannerAgent | `plan` |
| 3 | metadata | MetadataAgent | `relevant_tables` |
| 4 | sql_generator | SQLGeneratorAgent | `sql_query` |
| 5 | sql_validator | SQLValidatorAgent | `sql_valid` (+ retry edge) |
| 6 | execution | (SQL tool / adapter) | `result_rows` |
| 7 | statistical_analysis | PythonAnalystAgent + stats tool | `statistics` |
| 8 | visualization | ChartGeneratorAgent + chart tool | `charts` |
| 9 | insight | BusinessInsightAgent | `insights` |
| 10 | recommendation | RecommendationAgent | `recommendations` |
| 11 | reflection | ReflectionAgent | `reflection` (+ retry edge) |
| 12 | report_generator | PDF/DOCX/XLSX tools | `report` |
| 13 | langfuse_logger | — | flush trace |

**Conditional edges**

- `sql_validator`: if invalid and `retry_count < max_retries` → back to `sql_generator`; else continue (or error).
- `reflection`: if `needs_retry` and budget remains → jump to `reflection.retry_target` (usually `planner`); else → `report_generator`.

## 4. State

`AnalyticsState` (a `TypedDict`) is threaded through every node. Append-only
channels (`executions`, `errors`, `events`, `completed_tasks`) use
`operator.add` reducers so parallel/retry writes merge safely.

## 5. Observability

Every node run creates an `AgentExecution` row (status, attempt, latency,
tokens, cost, error) **and** a LangFuse span via the LangChain callback handler.
The Trace Viewer page reads these back.

## 6. Resilience

- **Retry:** tenacity exponential backoff inside each agent.
- **Fallback LLM:** `get_llm()` wraps the primary model with a secondary
  provider via `with_fallbacks`.
- **Graph-level recovery:** validator & reflection retry loops with a hard
  iteration cap (`MAX_GRAPH_ITERATIONS`).
- **Graceful degradation:** Redis/Qdrant/LangFuse are optional; the app boots
  and runs without them.

## 7. Data sources

A uniform `DataSourceAdapter` abstracts CSV, Excel, PostgreSQL, MySQL and
SQLite. Uploaded files are loaded into an in-memory SQLite so the SQL pipeline
works identically across sources.
