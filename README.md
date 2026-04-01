# OT Tag Registry

**One place to create, govern, and standardise every sensor tag across your industrial sites.**

## The Problem

In most industrial operations, tag definitions — the names, rules, and metadata that describe every sensor, actuator, and data point — live in **Excel sheets, email threads, and tribal knowledge**. This leads to:

- **Inconsistent naming** — the same measurement is called different things at different sites, breaking analytics and cross-site benchmarking.
- **Unclear ownership** — nobody knows whether OT, IT, or the system integrator is responsible for a given tag definition.
- **Slow onboarding** — adding a new sensor or production line means weeks of rework aligning naming conventions, validation rules, and data contracts.

## What This App Does

The OT Tag Registry gives **Site OT engineers** a single, governed application to:

| Capability                                       | Business Value                                                                                                                                                              |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Create / update / retire tags**                | Every tag has a single source of truth with full lifecycle tracking                                                                                                         |
| **Define physical-truth rules as configuration** | L1 range checks (min/max, spike, missing-data) and L2 state profiles (Running/Idle/Stop) are set by engineers — no code changes needed                                      |
| **Enforce consistent naming automatically**      | A deterministic validator ensures every tag follows the site naming schema — no more "creative" tag names                                                                   |
| **Get AI-powered name suggestions**              | When creating a tag, the system suggests canonical names based on what already exists for that site/line/equipment — aligning new tags with established standards instantly |
| **Request validation & approval**                | Governance workflows ensure changes are reviewed before going live                                                                                                          |

## How AI Adds Value (Without Replacing Governance)

The **"Suggest a Name"** feature uses **Azure AI Search** to recommend tag names based on semantic similarity to approved tags — filtered by the correct site, line, and equipment context. This means:

- A new engineer typing _"outlet pressure sensor on main pump"_ instantly sees the canonical name used across the organisation.
- Descriptions in different languages or wordings still map to the right standard name.
- **AI assists; rules enforce.** Suggestions are always optional — the deterministic naming validator remains the final gate.

> **Rules for correctness. AI for speed and consistency.**

## Key Data Objects

| Object                       | Purpose                                                                              |
| ---------------------------- | ------------------------------------------------------------------------------------ |
| **Asset**                    | Organisational hierarchy — site → line → equipment                                   |
| **Tag**                      | The core entity — name, description, unit, datatype, sampling frequency, criticality |
| **Source**                   | Where the data comes from — PLC, SCADA, Historian, connector, topic/path             |
| **L1 Rules (Range)**         | Physical boundary checks — min/max, missing-data policy, spike threshold             |
| **L2 Rules (State Profile)** | Operational state mapping — Running/Idle/Stop with state-dependent ranges            |

## Architecture

```mermaid
graph TD
    FE["<b>React Frontend</b><br/>Tag management · Rules config · AI panel"]
    BE["<b>Python Backend (FastAPI)</b><br/>Tag CRUD · Rules engine · Naming validator<br/>Suggestion orchestrator"]
    COSMOS[("<b>Azure Cosmos DB</b><br/>Tags, Assets,<br/>Rules, Sources")]
    SEARCH[("<b>Azure AI Search</b><br/>Vector index of approved/golden tags<br/>Structured filters + semantic embeddings")]

    FE -- "REST API" --> BE
    BE --> COSMOS
    BE --> SEARCH
```

- **Frontend + Backend run locally** for fast iteration and demo reliability.
- **Azure managed services** provide enterprise-grade persistence and AI search capabilities.

## Getting Started

### Prerequisites

- **Python 3.12+** with [`uv`](https://docs.astral.sh/uv/) package manager
- **Node.js 20+** with npm
- **Azure Cosmos DB** account — the backend persists all data to a real Cosmos DB instance in your Azure subscription
- **Azure AI Search** service — powers the "Suggest a Name" vector search feature
- **Azure AI Foundry** project — provides `text-embedding-3-large` embeddings for semantic search

### Environment Setup

Copy the example env file and fill in your Cosmos DB credentials:

```bash
cp server/.env.example server/.env
```

Required variables:

| Variable                       | Description                                                                    |
| ------------------------------ | ------------------------------------------------------------------------------ |
| `COSMOS_ENDPOINT`              | Your Cosmos DB account URI (e.g. `https://<account>.documents.azure.com:443/`) |
| `COSMOS_DATABASE`              | Database name (defaults to `ot-tag-registry`)                                  |
| `SEARCH_ENDPOINT`              | Azure AI Search service URI (e.g. `https://<service>.search.windows.net`)      |
| `SEARCH_INDEX_NAME`            | Index name (defaults to `golden-tags`)                                         |
| `PROJECT_ENDPOINT`             | Azure AI Foundry project endpoint                                              |
| `PROJECT_EMBEDDING_DEPLOYMENT` | Embedding model deployment name (e.g. `text-embedding-3-large`)                |

> **Authentication:** All services use `DefaultAzureCredential` (managed identity in Azure, Azure CLI / VS Code locally). No API keys are needed.

The **services** layer needs its own env file with the same variables for setup scripts:

```bash
cp services/.env.example services/.env
```

### Install & Run

```bash
# Install dependencies
cd server && uv venv && uv pip install -r requirements.txt
cd ../services && uv venv && uv pip install -r requirements.txt
cd ../client && npm install

# Start backend (port 8000)
cd server && uv run uvicorn src.main:app --reload

# Start frontend (port 5173)
cd client && npm run dev
```

### Seed Sample Data

The seed script populates your Cosmos DB with realistic sample data for development and demo purposes:

```bash
cd services && uv run python -m database.seed
```

This will:

1. **Create the database and 5 containers** (`assets`, `tags`, `sources`, `l1Rules`, `l2Rules`) if they don't already exist
2. **Upsert sample documents** — ~20 assets across 3 sites (Luxembourg, Brussels, Amsterdam), 6 data sources, ~35 tags, 27 L1 rules, and 5 L2 rules

> [!WARNING]
> This writes to your live Azure Cosmos DB instance. The script uses upsert operations, so it's safe to re-run — it will overwrite existing seed documents rather than create duplicates. Make sure your `server/.env` has valid credentials before running.

### Seed Azure AI Search Index

The AI Search index powers the "Suggest a Name" feature. Two scripts set up and populate the `golden-tags` vector index:

```bash
# 1. Create the index schema (run once)
cd services && uv run python -m search.create_index

# 2. Generate embeddings and upload golden tags
cd services && uv run python -m search.seed_index
```

This will:

1. **Create the `golden-tags` index** with HNSW vector search (3072 dimensions, cosine metric) configured for `text-embedding-3-large`
2. **Seed 68 golden tags** across 3 sites (Luxembourg, Belgium, France), 8 equipment types, and 29 measurement types — each with a vector embedding generated via Azure AI Foundry

> **Requires** `SEARCH_ENDPOINT`, `PROJECT_ENDPOINT`, and `PROJECT_EMBEDDING_DEPLOYMENT` to be set in `services/.env`.

## API Reference

All endpoints are prefixed with `/api`.

### Tags

| Method  | Path                              | Description                                             |
| ------- | --------------------------------- | ------------------------------------------------------- |
| `GET`   | `/api/tags`                       | List tags (query params: `status`, `assetId`, `search`) |
| `GET`   | `/api/tags/{id}`                  | Get a single tag                                        |
| `POST`  | `/api/tags`                       | Create a new tag (defaults to `draft` status)           |
| `PUT`   | `/api/tags/{id}`                  | Partial update — only provided fields change            |
| `PATCH` | `/api/tags/{id}/retire`           | Soft-delete (sets status to `retired`)                  |
| `POST`  | `/api/tags/validate-name`         | Validate a name against the naming schema               |
| `POST`  | `/api/tags/suggest-name`          | AI-powered name suggestions via hybrid vector search    |
| `POST`  | `/api/tags/{id}/request-approval` | Submit tag for governance approval                      |
| `POST`  | `/api/tags/{id}/approve`          | Approve a pending tag                                   |
| `POST`  | `/api/tags/{id}/reject`           | Reject a pending tag (optional reason)                  |

### Assets

| Method | Path          | Description        |
| ------ | ------------- | ------------------ |
| `GET`  | `/api/assets` | List all assets    |
| `POST` | `/api/assets` | Create a new asset |

### Sources

| Method | Path           | Description         |
| ------ | -------------- | ------------------- |
| `GET`  | `/api/sources` | List all sources    |
| `POST` | `/api/sources` | Create a new source |

### Rules

| Method   | Path                      | Description                 |
| -------- | ------------------------- | --------------------------- |
| `GET`    | `/api/tags/{id}/rules/l1` | Get L1 (range) rule         |
| `POST`   | `/api/tags/{id}/rules/l1` | Create or replace L1 rule   |
| `PUT`    | `/api/tags/{id}/rules/l1` | Partial update L1 rule      |
| `DELETE` | `/api/tags/{id}/rules/l1` | Delete L1 rule              |
| `GET`    | `/api/tags/{id}/rules/l2` | Get L2 (state profile) rule |
| `POST`   | `/api/tags/{id}/rules/l2` | Create or replace L2 rule   |
| `PUT`    | `/api/tags/{id}/rules/l2` | Partial update L2 rule      |
| `DELETE` | `/api/tags/{id}/rules/l2` | Delete L2 rule              |

## Testing & Linting

```bash
# Backend tests (pytest)
cd server && uv run pytest tests/ -v

# Frontend lint
cd client && npm run lint

# Frontend type-check + build
cd client && npm run build
```

## Deployment

The project includes Azure Developer CLI (`azd`) configuration for deploying to Azure:

```bash
azd up        # Provision infrastructure + deploy app
azd deploy    # Deploy code changes only (infra already exists)
```

Infrastructure is defined as **Bicep** templates in `azure/`. See `azure.yaml` for the full configuration.

## Project Structure

```
ot-tag-registry/
├── azure/           # Bicep infrastructure-as-code templates
├── client/          # React + Vite + TypeScript frontend
├── server/          # Python (FastAPI) backend API (standalone deployable)
│   ├── src/
│   │   ├── routes/      # API endpoints (tags, assets, sources, rules, suggest-name)
│   │   ├── models/      # Pydantic data models
│   │   ├── utils/       # Cosmos DB client (db.py) + AI Search client (search.py)
│   │   └── validators/  # Naming schema validator
│   └── tests/           # Pytest suite with mocked Cosmos repos
├── services/        # Local-only setup tools (not deployed)
│   ├── database/    # Cosmos DB container creation + data seeding
│   ├── search/      # Azure AI Search index creation + golden tag seeding
│   └── language/    # Language normalisation
├── skills/          # Copilot agent skill definitions
└── excalidraw/      # Architecture diagrams
```

## Disclaimer

> [!WARNING]
> This repository is provided for **demo, educational, and experimental purposes only**.
> It is **not production‑ready** and **must not be used in production deployments**.
> The author takes **no responsibility or liability** for any damage, data loss, costs,
> or issues arising from the use of this code.
> Use at your own risk.
