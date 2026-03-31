# Custom Agents — OT Tag Registry

Agents that orchestrate the build of the OT Tag Registry application.

## Agents

| Agent | Type | Purpose | Issues |
|-------|------|---------|--------|
| `ot-builder` | Orchestrator | Coordinates the full build by delegating to subagents | All |
| `ob--backend-api` | Subagent | Python/FastAPI backend: models, Cosmos DB, API routes, validators | #0, #1–#5, #10, #12 |
| `ob--frontend` | Subagent | React/TypeScript/Fluent UI v9 frontend: pages, forms, components | #0 (partial), #6–#8, #13 |
| `ob--ai-search` | Subagent | Azure AI Search: index, embeddings, vector search, seed data | #9, #11, #14, #15 |

## Usage

Invoke the orchestrator to build any issue:

```
@ot-builder Build Issue #3 — Tag lifecycle API endpoints
```

```
@ot-builder Build Issues #6 and #7 — Tag list page and create/edit form
```

```
@ot-builder What's the current status? Which issues are complete?
```

## Architecture

```
ot-builder (orchestrator)
├── ob--backend-api   → server/
├── ob--frontend      → client/
└── ob--ai-search     → services/search/, services/language/
```
