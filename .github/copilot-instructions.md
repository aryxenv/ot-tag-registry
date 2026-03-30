# Copilot Instructions — OT Tag Registry

## Architecture

Industrial IoT tag registry with three layers and an orchestrated agent system:

- **`server/`** — Python FastAPI backend. Domain models (Pydantic), Cosmos DB query logic (repository layer), REST API, deterministic naming validator, suggest-name orchestrator. **Standalone deployable** — never imports from `services/`.
- **`client/`** — React 19 + TypeScript + Vite frontend. Fluent UI v9 component library. Dev server proxies `/api/*` to `localhost:8000`.
- **`services/`** — Local-only Python modules for Azure service setup and configuration. **Not deployed** — used during development to create infrastructure, seed data, and configure external services. Has its own `requirements.txt` and venv.
  - `services/database/` — Cosmos DB setup: container creation (`cosmos_setup.py`) and data seeding (`seed.py`).
  - `services/search/` — Azure AI Search: vector index creation, golden tag seeding, hybrid suggest-name queries.
  - `services/language/` — Language detection and normalisation to English.
- **`.github/agents/`** — Copilot agent orchestration. `ot-builder` orchestrator delegates to `ob--backend-api`, `ob--frontend`, and `ob--ai-search` subagents.

Data flows: Frontend → FastAPI (`/api/*`) → Cosmos DB. FastAPI → `services/search/` → Azure AI Search (vector index). Pydantic models in `server/src/models/` are the single source of truth for data shapes.

## Build & Run

```bash
# Backend
cd server && uv venv && uv pip install -r requirements.txt
cd server && uv run uvicorn src.main:app --reload --port 8000

# Frontend
cd client && npm install
cd client && npm run dev          # Vite dev server on port 5173

# Services (local-only setup tools)
cd services && uv venv && uv pip install -r requirements.txt

# Seed sample data into Cosmos DB
cd services && uv run python -m database.seed

# AI Search services
cd services/search && uv venv && uv pip install -r requirements.txt
cd services/search && uv run python create_index.py
cd services/search && uv run python seed_index.py
```

## Lint & Test

```bash
# Frontend
cd client && npm run lint         # ESLint (TS + React hooks + React refresh rules)
cd client && npm run build        # Type-check (tsc) then Vite build

# Backend
cd server && uv run pytest tests/ -v              # Full suite
cd server && uv run pytest tests/test_tags.py -v  # Single file
cd server && uv run pytest tests/ -k "test_name"  # Single test by name
```

## Key Conventions

### Server vs. Services Separation

- **`server/`** is a **standalone deployable API**. It contains only runtime logic: routes, models, repository (query layer), validators. It never imports from `services/`.
- **`services/`** is **local-only** — used during development for infrastructure setup (DB container creation, data seeding, AI Search index creation). Not deployed with the server.
- Non-API service configurations (Cosmos DB setup, AI Search index management, data seeding) always live in `services/`, never in `server/`.

### Python (server + services)

- **Always use `uv`** — never raw `pip` or `python`. Commands: `uv run`, `uv pip install`.
- **Pydantic `BaseModel`** for all data models. Python `enum.Enum` for status/criticality/datatype.
- **Type hints** on all functions (Python 3.12+ syntax).
- **IDs**: UUID v4 as strings (`Field(default_factory=lambda: str(uuid4()))`).
- **Timestamps**: `createdAt` and `updatedAt` as UTC `datetime`. Update `updatedAt` on every mutation.
- **Soft deletes**: Tags are retired (`status="retired"`), never hard-deleted.
- **Error responses**: `{"error": str, "details": list[str] | None}`.
- **HTTP status codes**: 201 for creation, 204 for deletion, 400 for validation errors.
- **All routes prefixed `/api/`**. Use FastAPI dependency injection for the Cosmos client.
- **Environment variables** via `python-dotenv`; never hardcode credentials.

### TypeScript / React (client)

- **Fluent UI v9 only** — `@fluentui/react-components` and `@fluentui/react-icons`. Never use v8 (`@fluentui/react`).
- **Styling**: `makeStyles` from Fluent UI with `tokens` for all colours. No CSS files, no inline styles, no hardcoded colours.
- **Typography**: Fluent text components (`Title1`, `Title2`, `Text`) — no raw HTML headings.
- **Icons**: `@fluentui/react-icons`, Regular weight by default, Filled for active states.
- **Theming**: App wrapped in `<FluentProvider theme={webLightTheme}>`.
- **API calls**: Use `fetch` against `/api/*` (Vite proxy handles routing to backend).
- **File naming**: PascalCase for components (`TagTable.tsx`), camelCase with `use` prefix for hooks (`useApi.ts`).
- **React Compiler** is enabled via Babel plugin — avoid manual `useMemo`/`useCallback` unless profiling shows a need.

### Cosmos DB

| Container | Partition Key | Content |
|-----------|--------------|---------|
| assets | `/site` | Equipment hierarchy (site → line → equipment) |
| tags | `/assetId` | Tag definitions |
| sources | `/systemType` | Data source configurations (PLC, SCADA, etc.) |
| l1Rules | `/tagId` | Range validation rules (min/max, spike, missing-data) |
| l2Rules | `/tagId` | Operational state profiles (Running/Idle/Stop) |

### Tag Naming Schema

Deterministic format: `<SITE>.<LINE>.<EQUIPMENT>.<MEASUREMENT>` — e.g., `MUN.L2.PMP001.OutletPressure`. The naming validator enforces this schema; AI suggestions are always optional and must pass the validator before acceptance.

### AI Search (suggest-name)

Hybrid query pattern: OData filter (site + line) → semantic text (description + unit) → Azure OpenAI embedding (ada-002, 1536 dims) → vector search (HNSW, cosine) → ranked suggestions. Index name: `golden-tags`.

## Agent Boundaries

Each agent owns specific directories — respect these when making changes:

- **`ob--backend-api`** owns `server/` — never modifies `client/` or `services/`.
- **`ob--frontend`** owns `client/` — never modifies `server/` or `services/`.
- **`ob--ai-search`** owns `services/` — never modifies `client/`; coordinates with backend for the `/api/tags/suggest-name` endpoint.
- **`ot-builder`** orchestrates across all three; see `build-issues.md` for the issue backlog and dependency DAG.

## Domain Model Quick Reference

- **Asset**: Site → Line → Equipment hierarchy. Computed `hierarchy` field.
- **Tag**: Core entity — name, description, unit, datatype, sampling frequency, criticality, status (draft/active/retired). Belongs to an Asset.
- **Source**: Where data originates — PLC/SCADA/Historian with connector type and topic/path.
- **L1Rule**: Physical range checks on a Tag — min, max, spike threshold, missing-data policy.
- **L2Rule**: Operational state profiles — maps states (Running/Idle/Stop) to expected value ranges based on condition logic.
