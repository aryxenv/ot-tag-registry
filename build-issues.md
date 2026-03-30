# Build Issues — OT Tag Registry

> Technical issue backlog split into **(A) Pre-built foundations** (must be done before the demo) and **(B) Live demo build** (built on-stage with GitHub Copilot agent).

---

## A) Pre-Built Foundations

These issues must be completed and stable before the live demo session. They represent the "boring but working" baseline the audience sees at the start.

---

### Issue #0 — Bootstrap Python/FastAPI server project

**Labels:** `infrastructure`, `pre-built`, `priority: critical`

**Description**

Scaffold the Python backend project from scratch. The `server/` directory is currently empty. This is a **hard prerequisite** for all backend issues (#1–#5, #10). Also install Fluent UI React on the client as the UI component library.

**Requirements**

- [ ] Create `server/requirements.txt` with core dependencies:
  - `fastapi`
  - `uvicorn[standard]`
  - `azure-cosmos`
  - `python-dotenv`
  - `pydantic`
- [ ] Create Python package structure:
  ```
  server/
  ├── requirements.txt
  ├── .env.example
  └── src/
      ├── __init__.py
      ├── main.py              # FastAPI app, CORS, root router
      ├── config/
      │   └── __init__.py
      ├── models/
      │   └── __init__.py
      ├── routes/
      │   └── __init__.py
      ├── repositories/
      │   └── __init__.py
      ├── validators/
      │   └── __init__.py
      └── scripts/
          └── __init__.py
  ```
- [ ] `server/src/main.py`:
  - FastAPI app instance
  - CORS middleware allowing `http://localhost:5173`
  - Health endpoint: `GET /` → `{ "status": "ok" }`
  - Test endpoint: `GET /api/test` → `{ "message": "hello world" }`
- [ ] `.env.example` with placeholder variables:
  - `COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`
  - `SEARCH_ENDPOINT`, `SEARCH_API_KEY`, `SEARCH_INDEX_NAME`
  - `OPENAI_ENDPOINT`, `OPENAI_API_KEY`, `OPENAI_EMBEDDING_DEPLOYMENT`
- [ ] Configure `client/vite.config.ts` with dev proxy: `/api` → `http://localhost:8000`
- [ ] Install Fluent UI React on the client:
  - `cd client && npm install @fluentui/react-components @fluentui/react-icons`
  - Wrap the app root in `<FluentProvider theme={webLightTheme}>` in `main.tsx`
- [ ] Verify end-to-end: `uv venv && uv run pip install -r requirements.txt && uv run uvicorn src.main:app --reload` serves both endpoints

**Acceptance criteria**
- `uv run uvicorn src.main:app --reload` starts the server on port 8000
- `GET /` and `GET /api/test` return expected JSON responses
- CORS headers allow requests from `http://localhost:5173`
- All subdirectory packages are importable (no missing `__init__.py`)
- Frontend dev server can proxy API calls to the backend
- Fluent UI React is installed and `FluentProvider` wraps the app root

---

### Issue #1 — Define data models for Asset, Tag, Source, and Rules

**Labels:** `data-model`, `pre-built`, `priority: critical`

**Description**

Implement Python data models (Pydantic or dataclasses) and Cosmos DB document schemas for all core domain entities described in the use case.

**Requirements**

- [ ] **Asset** model
  - `id` (string, auto-generated)
  - `site` (string, required) — e.g., "Plant-Munich"
  - `line` (string, required) — e.g., "Line-2"
  - `equipment` (string, required) — e.g., "Pump-001"
  - `hierarchy` (string, computed) — `site.line.equipment`
  - `description` (string, optional)
  - `createdAt`, `updatedAt` (timestamps)

- [ ] **Tag** model
  - `id` (string, auto-generated)
  - `name` (string, required) — the canonical tag name
  - `description` (string, required) — free-text description of what this tag measures
  - `unit` (string, required) — e.g., "bar", "°C", "RPM"
  - `datatype` (enum: `float`, `int`, `bool`, `string`)
  - `samplingFrequency` (number, seconds)
  - `criticality` (enum: `low`, `medium`, `high`, `critical`)
  - `status` (enum: `active`, `retired`, `draft`)
  - `assetId` (string, FK to Asset)
  - `sourceId` (string, FK to Source, optional)
  - `createdAt`, `updatedAt` (timestamps)

- [ ] **Source** model
  - `id` (string, auto-generated)
  - `systemType` (enum: `PLC`, `SCADA`, `Historian`, `Other`)
  - `connectorType` (string) — e.g., "OPC-UA", "MQTT", "Modbus"
  - `topicOrPath` (string) — the address/topic for this data source
  - `description` (string, optional)
  - `createdAt`, `updatedAt` (timestamps)

- [ ] **L1 Rule (Range)** model
  - `id` (string, auto-generated)
  - `tagId` (string, FK to Tag)
  - `min` (number, nullable) — lower bound
  - `max` (number, nullable) — upper bound
  - `missingDataPolicy` (enum: `ignore`, `alert`, `interpolate`, `last-known`)
  - `spikeThreshold` (number, nullable) — max allowed delta between consecutive readings
  - `createdAt`, `updatedAt` (timestamps)

- [ ] **L2 Rule (State Profile)** model
  - `id` (string, auto-generated)
  - `tagId` (string, FK to Tag)
  - `stateMapping` (array of objects):
    - `state` (enum: `Running`, `Idle`, `Stop`)
    - `conditionField` (string) — which tag/signal determines this state
    - `conditionOperator` (enum: `>`, `>=`, `<`, `<=`, `==`, `!=`, `between`)
    - `conditionValue` (number | [number, number])
    - `rangeMin` (number, nullable) — expected range while in this state
    - `rangeMax` (number, nullable)
  - `createdAt`, `updatedAt` (timestamps)

**Acceptance criteria**

- All models are defined as Pydantic models in a shared `server/src/models/` package
- Cosmos DB container configuration (partition keys, indexing policy) is defined
- Seed script can create containers and insert sample documents

---

### Issue #2 — Set up Azure Cosmos DB integration

**Labels:** `database`, `pre-built`, `priority: critical`

**Description**

Wire up Azure Cosmos DB as the persistence layer using the `azure-cosmos` Python SDK.

**Requirements**

- [ ] Create `server/src/config/cosmos_client.py` — initialise Cosmos client from env vars (`COSMOS_ENDPOINT`, `COSMOS_KEY`, `COSMOS_DATABASE`)
- [ ] Create database initialisation logic (create DB + containers if not exist)
- [ ] Containers to create:
  - `assets` (partition key: `/site`)
  - `tags` (partition key: `/assetId`)
  - `sources` (partition key: `/systemType`)
  - `l1Rules` (partition key: `/tagId`)
  - `l2Rules` (partition key: `/tagId`)
- [ ] Create a generic CRUD repository helper (`server/src/repositories/cosmos_repository.py`) to reduce boilerplate
- [ ] Add `.env.example` with all required environment variables
- [ ] Seed script (`server/src/scripts/seed.py`) that populates realistic sample data (10+ assets, 30+ tags, sources, rules)

**Acceptance criteria**

- `uv run python -m src.scripts.seed` (or equivalent CLI command) creates all containers and inserts sample data
- Repository helper supports: `create`, `get_by_id`, `get_all`, `query`, `update`, `delete`
- Connection errors produce clear log messages

---

### Issue #3 — Build Tag lifecycle API endpoints

**Labels:** `api`, `pre-built`, `priority: critical`

**Description**

Implement the core CRUD + lifecycle endpoints for Tags.

**Endpoints**

| Method  | Route                  | Description                                                               |
| ------- | ---------------------- | ------------------------------------------------------------------------- |
| `GET`   | `/api/tags`            | List all tags (supports `?status=`, `?assetId=`, `?search=` query params) |
| `GET`   | `/api/tags/:id`        | Get a single tag by ID                                                    |
| `POST`  | `/api/tags`            | Create a new tag (status defaults to `draft`)                             |
| `PUT`   | `/api/tags/:id`        | Update a tag                                                              |
| `PATCH` | `/api/tags/:id/retire` | Retire a tag (sets `status` to `retired`, soft-delete)                    |
| `GET`   | `/api/assets`          | List all assets                                                           |
| `POST`  | `/api/assets`          | Create an asset                                                           |
| `GET`   | `/api/sources`         | List all sources                                                          |
| `POST`  | `/api/sources`         | Create a source                                                           |

**Requirements**

- [ ] Input validation on all POST/PUT endpoints (required fields, enum values, types)
- [ ] Return proper HTTP status codes (201 on create, 404 on not found, 400 on validation error)
- [ ] Include `updatedAt` timestamp on every mutation
- [ ] Retirement is a soft-delete — retired tags remain queryable but are excluded from default list views
- [ ] Wire routes in the FastAPI app entry point

**Acceptance criteria**

- All endpoints return correct status codes and response shapes
- [ ] Invalid payloads return structured error responses `{ "error": str, "details": list[str] | None }`
- [ ] Tags can be created, read, updated, and retired via curl/Postman

---

### Issue #4 — Build Rules configuration API endpoints

**Labels:** `api`, `pre-built`, `priority: high`

**Description**

Implement endpoints for configuring L1 (Range) and L2 (State Profile) rules per tag.

**Endpoints**

| Method   | Route                       | Description               |
| -------- | --------------------------- | ------------------------- |
| `GET`    | `/api/tags/:tagId/rules/l1` | Get L1 rule for a tag     |
| `POST`   | `/api/tags/:tagId/rules/l1` | Create or replace L1 rule |
| `PUT`    | `/api/tags/:tagId/rules/l1` | Update L1 rule            |
| `DELETE` | `/api/tags/:tagId/rules/l1` | Remove L1 rule            |
| `GET`    | `/api/tags/:tagId/rules/l2` | Get L2 rule for a tag     |
| `POST`   | `/api/tags/:tagId/rules/l2` | Create or replace L2 rule |
| `PUT`    | `/api/tags/:tagId/rules/l2` | Update L2 rule            |
| `DELETE` | `/api/tags/:tagId/rules/l2` | Remove L2 rule            |

**Requirements**

- [ ] Validate that the referenced `tagId` exists before creating rules
- [ ] L1: at least one of `min`, `max`, `spikeThreshold` must be set
- [ ] L2: `stateMapping` must have at least one entry; validate enum values for `state` and `conditionOperator`
- [ ] One L1 rule per tag, one L2 rule per tag (upsert semantics on POST)

**Acceptance criteria**

- Rules are correctly persisted and retrievable per tag
- Validation errors return clear messages
- Deleting a rule returns 204; deleting a non-existent rule returns 404

---

### Issue #5 — Build deterministic tag naming validator

**Labels:** `validation`, `pre-built`, `priority: critical`

**Description**

Implement a rule-based naming validator that enforces a configurable naming schema. This is the **governance backbone** — it runs independently of any AI suggestion.

**Naming schema (configurable)**

Default: `<site>.<line>.<equipment>.<measurementType>.<qualifier>`

Example valid name: `Munich.Line2.Pump001.Pressure.Discharge`

**Requirements**

- [ ] Create `server/src/validators/naming_validator.py`
- [ ] Configurable schema definition:

  ```python
  @dataclass
  class SegmentRule:
      name: str                          # e.g., "site", "line", "equipment"
      required: bool
      pattern: re.Pattern | None = None  # e.g., re.compile(r'^[A-Z][a-zA-Z0-9]+$')
      allowed_values: list[str] | None = None  # e.g., known site codes

  @dataclass
  class NamingSchema:
      separator: str                     # default: "."
      segments: list[SegmentRule]        # ordered list of required/optional segments
  ```

- [ ] Validation checks:
  - Correct number of segments
  - Required segments present and non-empty
  - Each segment matches its `pattern` (if defined)
  - Each segment value is in `allowed_values` (if defined)
  - No special characters outside allowed set
  - No consecutive separators or leading/trailing separators
- [ ] Return structured error list:

  ```python
  @dataclass
  class ValidationError:
      segment: str
      message: str
      received: str
      expected: str | None = None

  @dataclass
  class ValidationResult:
      valid: bool
      errors: list[ValidationError]
  ```

- [ ] Expose as `POST /api/tags/validate-name` endpoint accepting `{ name: string }`
- [ ] Integrate into tag creation flow — `POST /api/tags` should auto-validate and reject invalid names

**Acceptance criteria**

- Valid names pass; invalid names return a clear, human-readable error list
- Schema is loaded from config (not hardcoded)
- At least 10 unit test cases (pytest) covering edge cases (missing segments, bad characters, empty segments, too many segments)

---

### Issue #6 — Build minimal frontend — Tag list and search

**Labels:** `frontend`, `pre-built`, `priority: critical`

**Description**

Replace the Vite template UI with a functional Tag Registry interface. Start with the tag listing and search page.

**Requirements**

- [ ] Set up React Router with a basic layout (sidebar/topbar + content area)
- [ ] **Tag List page** (`/tags`):
  - Table/list view showing: tag name, description, asset (site/line/equipment), status, criticality
  - Status badge colours (active = green, draft = yellow, retired = grey)
  - Criticality indicator
  - Sortable columns (name, status, criticality)
  - Pagination or virtual scroll for 100+ tags
- [ ] **Search & filter bar**:
  - Text search (filters by name and description)
  - Status filter dropdown (All / Active / Draft / Retired)
  - Asset filter (site dropdown → line dropdown → equipment dropdown, cascading)
- [ ] API integration: fetch from `GET /api/tags` with query params
- [ ] Loading states and empty states
- [ ] Clicking a tag row navigates to the tag detail/edit page

**Acceptance criteria**

- Page loads and displays seeded tags
- Search filters results in real time (or on submit)
- Status and asset filters work correctly
- Responsive enough for a demo screen (doesn't need to be mobile-perfect)

---

### Issue #7 — Build minimal frontend — Tag create/edit form

**Labels:** `frontend`, `pre-built`, `priority: critical`

**Description**

Implement the tag creation and editing form with all required fields.

**Requirements**

- [ ] **Tag create page** (`/tags/new`):
  - Form fields for all Tag model properties:
    - Name (text input + validation indicator)
    - Description (textarea)
    - Unit (text input or common-units dropdown)
    - Datatype (dropdown: float, int, bool, string)
    - Sampling frequency (number input, seconds)
    - Criticality (dropdown: low, medium, high, critical)
    - Asset selection (cascading dropdowns: site → line → equipment)
    - Source selection (dropdown, optional)
  - Real-time naming validation (calls `POST /api/tags/validate-name` on blur/change of name field)
  - Validation error display inline under the name field
  - Submit → `POST /api/tags` → redirect to tag list on success
  - Cancel button

- [ ] **Tag edit page** (`/tags/:id/edit`):
  - Same form, pre-populated with existing tag data
  - Submit → `PUT /api/tags/:id`
  - **Retire button** (with confirmation dialog) → `PATCH /api/tags/:id/retire`

- [ ] **Placeholder area for "Suggest a Name" button** — visible but disabled/stubbed with tooltip "Coming soon". This is where the live demo feature will be wired in.

**Acceptance criteria**

- Can create a new tag with valid data and see it in the list
- Can edit an existing tag
- Can retire a tag
- Naming validation errors display inline and block submission
- "Suggest a Name" placeholder is visible on the form

---

### Issue #8 — Build minimal frontend — Rules configuration section

**Labels:** `frontend`, `pre-built`, `priority: high`

**Description**

Add L1 and L2 rule configuration to the tag detail/edit view.

**Requirements**

- [ ] **L1 Range Rules section** (on tag edit page, collapsible panel):
  - Min value (number input, optional)
  - Max value (number input, optional)
  - Missing data policy (dropdown: ignore, alert, interpolate, last-known)
  - Spike threshold (number input, optional)
  - Save → `POST /api/tags/:tagId/rules/l1`
  - Delete rule option
  - Show current rule values if one exists

- [ ] **L2 State Profile section** (on tag edit page, collapsible panel):
  - Dynamic list of state mappings (add/remove rows)
  - Per row:
    - State (dropdown: Running, Idle, Stop)
    - Condition field (text — which signal determines state)
    - Condition operator (dropdown: >, >=, <, <=, ==, !=, between)
    - Condition value (number input; two inputs if "between")
    - Range min / Range max for this state (number inputs)
  - Save → `POST /api/tags/:tagId/rules/l2`
  - Delete rule option

**Acceptance criteria**

- Can create, view, update, and delete L1 rules for a tag
- Can create, view, update, and delete L2 rules with multiple state mappings
- Validation prevents saving empty/invalid rules
- Rules section loads existing data on tag edit

---

### Issue #9 — Set up and seed Azure AI Search vector index

**Labels:** `azure`, `search`, `pre-built`, `priority: critical`

**Description**

Create and populate an Azure AI Search index with approved/golden tags to power the "Suggest a Name" feature. This is the **core AI infrastructure** for the demo.

**Index schema**

Index name: `golden-tags`

| Field               | Type                     | Purpose                               | Searchable | Filterable | Retrievable |
| ------------------- | ------------------------ | ------------------------------------- | ---------- | ---------- | ----------- |
| `id`                | `Edm.String`             | Document key                          | —          | —          | ✅          |
| `tagName`           | `Edm.String`             | Canonical tag name to suggest         | ✅         | —          | ✅          |
| `site`              | `Edm.String`             | Site code                             | —          | ✅         | ✅          |
| `line`              | `Edm.String`             | Line identifier                       | —          | ✅         | ✅          |
| `equipment`         | `Edm.String`             | Equipment identifier                  | —          | ✅         | ✅          |
| `unit`              | `Edm.String`             | Measurement unit                      | —          | ✅         | ✅          |
| `datatype`          | `Edm.String`             | Data type                             | —          | ✅         | ✅          |
| `description`       | `Edm.String`             | Human-readable description            | ✅         | —          | ✅          |
| `measurementTokens` | `Edm.String`             | Normalised measurement keywords       | ✅         | —          | ✅          |
| `synonyms`          | `Edm.String`             | Alternative wordings                  | ✅         | —          | ✅          |
| `semanticText`      | `Edm.String`             | Combined semantic field for embedding | —          | —          | —           |
| `semanticVector`    | `Collection(Edm.Single)` | Vector embedding of `semanticText`    | Vector     | —          | —           |

**Requirements**

- [ ] Create index definition script (`services/search/create_index.py`)
- [ ] Configure vector search profile:
  - Algorithm: HNSW
  - Dimensions: match chosen embedding model (e.g., 1536 for `text-embedding-ada-002`)
  - Metric: cosine
- [ ] Create seed/indexing script (`services/search/seed_index.py`):
  - Reads approved tags from Cosmos DB (or a local JSON golden set)
  - For each tag, builds `semanticText` = `{description} {measurementTokens} {synonyms} {unit}`
  - Generates embedding via Azure OpenAI embedding endpoint
  - Uploads documents to index
- [ ] Golden dataset: prepare at least **50 realistic golden tags** across 3+ sites, multiple lines and equipment types, covering common OT measurements (pressure, temperature, flow, vibration, speed, level, etc.)
- [ ] Add `.env` variables: `SEARCH_ENDPOINT`, `SEARCH_API_KEY`, `SEARCH_INDEX_NAME`, `OPENAI_ENDPOINT`, `OPENAI_API_KEY`, `OPENAI_EMBEDDING_DEPLOYMENT`

**Acceptance criteria**

- Index is created with correct schema including vector field
- 50+ golden tags are indexed with embeddings
- A manual vector query (via REST or SDK) returns semantically relevant results
- Hard filters (site, line) correctly restrict result sets

---

### Issue #10 — Implement governance approval stub

**Labels:** `api`, `pre-built`, `priority: low`

**Description**

Add a minimal "request approval" mechanism so the demo can reference governance workflows.

**Requirements**

- [ ] Add `approvalStatus` field to Tag model (enum: `none`, `pending`, `approved`, `rejected`)
- [ ] `POST /api/tags/:id/request-approval` — sets `approvalStatus` to `pending`
- [ ] `POST /api/tags/:id/approve` — sets `approvalStatus` to `approved`, sets tag `status` to `active`
- [ ] `POST /api/tags/:id/reject` — sets `approvalStatus` to `rejected` with optional `rejectionReason`
- [ ] Frontend: show approval status badge on tag detail, "Request Approval" button when tag is in `draft`

**Acceptance criteria**

- Approval lifecycle works end-to-end (request → approve/reject)
- Status badge updates in the UI
- This is intentionally minimal — no email notifications, no role-based access

---

### Issue #11 — Create realistic seed data and demo scenario

**Labels:** `data`, `pre-built`, `priority: high`

**Description**

Prepare a coherent seed dataset that tells a believable story during the demo.

**Requirements**

- [ ] **3 sites**: e.g., Munich, Austin, Shanghai
- [ ] **2–3 lines per site**: e.g., Line-1 (Assembly), Line-2 (Packaging)
- [ ] **3–5 equipment per line**: Pumps, Compressors, Conveyors, Heat Exchangers, Motors
- [ ] **30+ tags** distributed across sites/lines with:
  - Realistic names following the naming schema
  - Realistic descriptions (some in slightly different wording styles to show semantic matching value)
  - Mix of statuses: mostly active, a few draft, a couple retired
  - Associated L1 and L2 rules
- [ ] **Sources**: 3–5 different source configs (OPC-UA, MQTT, Modbus)
- [ ] A few tags intentionally named **inconsistently** (to demonstrate the problem during the demo)
- [ ] Script: `uv run python -m src.scripts.seed` from server directory seeds both Cosmos DB and Azure AI Search index

**Acceptance criteria**

- Seed completes without errors
- UI shows a realistic-looking tag registry
- Inconsistent tags are visible and can be used to motivate the "Suggest a Name" feature

---

### Issue #14 — Wire vector search query logic in search service

**Labels:** `azure`, `search`, `pre-built`, `priority: critical`

**Dependencies:** Depends on Issue #9 (AI Search index must exist). Must be completed before Issue #12.

**Description**

Implement the search service module that encapsulates the Azure AI Search query logic used by the suggest-name endpoint.

**Requirements**

- [ ] Create `services/search/suggest_name.py` (or integrate into existing search service)
- [ ] Function signature:
  ```python
  async def suggest_tag_name(
      site: str,
      line: str,
      description: str,
      equipment: str | None = None,
      unit: str | None = None,
      datatype: str | None = None,
      top_k: int = 5,
  ) -> SuggestionResult:
      ...
  ```
- [ ] Build OData filter string from hard filter params
- [ ] Generate embedding for semantic query text via Azure OpenAI
- [ ] Execute hybrid query (vector + filters) against Azure AI Search
- [ ] Map search results to `SuggestionResult` type
- [ ] Handle: no results, API errors, timeout

**Acceptance criteria**

- Function correctly combines hard filters with vector search
- Returns ranked results with scores
- Gracefully handles missing optional parameters
- Error handling doesn't crash the server

---

### Issue #12 — Build "Suggest a Name" backend endpoint

**Labels:** `api`, `ai`, `pre-built`, `priority: critical`

**Dependencies:** Depends on Issue #14 (search service). Must be completed before demo Issue #13.

**Description**

Implement the backend endpoint that queries Azure AI Search using the **hard-filter + semantic search** pattern to return tag name suggestions.

**Endpoint**

`POST /api/tags/suggest-name`

**Request body**

```json
{
  "site": "Munich",
  "line": "Line-2",
  "equipment": "Pump-001",
  "description": "outlet pressure sensor on main pump",
  "unit": "bar",
  "datatype": "float"
}
```

**Implementation steps (what the Copilot agent should build)**

1. **Build hard filter set** from request:
   - Always: `site eq '{site}'`
   - Always: `line eq '{line}'`
   - Optional: `equipment eq '{equipment}'` (include if provided)

2. **Build semantic query text**:
   - Combine: `{description} {unit}` (and optionally measurement hint)
   - Generate embedding via Azure OpenAI embedding endpoint

3. **Execute vector search** against Azure AI Search:
   - Apply OData filter (hard filters)
   - Vector query on `semanticVector` field with the generated embedding
   - Top K = 5 candidates

4. **Post-process results**:
   - Rank by similarity score
   - Extract top suggestion + 2–3 alternatives
   - Build "why" explanation from matched fields

**Response body**

```json
{
  "suggestedName": "Munich.Line2.Pump001.Pressure.Discharge",
  "alternatives": [
    "Munich.Line2.Pump001.Pressure.Outlet",
    "Munich.Line2.Pump002.Pressure.Discharge",
    "Munich.Line1.Pump001.Pressure.Discharge"
  ],
  "evidence": "Similar to tag 'Munich.Line2.Pump001.Pressure.Discharge' — same site/line, description match on 'outlet pressure' ↔ 'discharge pressure' (0.94 similarity)",
  "matches": [
    {
      "tagName": "Munich.Line2.Pump001.Pressure.Discharge",
      "description": "Discharge pressure of main centrifugal pump",
      "score": 0.94
    },
    {
      "tagName": "Munich.Line2.Pump001.Pressure.Outlet",
      "description": "Outlet pressure measurement on pump",
      "score": 0.89
    }
  ]
}
```

**Acceptance criteria**

- Endpoint returns suggestions filtered to the correct site/line context
- Semantic similarity matches descriptions even with different wording
- Response includes scored matches with explanations
- Handles edge cases: no matches found, missing optional fields

---

## B) Live Demo Build (Built on stage with GitHub Copilot Agent)

These issues are built **live during the demo** using GitHub Copilot agent. The backend API (`POST /api/tags/suggest-name`) and vector search wiring are already pre-built and working — the live demo focuses on building the **frontend integration** that calls that API and the **language normalisation** enhancement.

---

### Issue #13 — Build "Suggest a Name" frontend button and suggestion panel

**Labels:** `frontend`, `ai`, `live-demo`, `priority: critical`

**Dependencies:** Depends on pre-built Issue #12 (backend endpoint must be available at `POST /api/tags/suggest-name`).

**Description**

Replace the stub placeholder on the tag create/edit form with a working "Suggest a Name" button and results panel.

**UI behaviour**

1. **Button**: "Suggest a Name" (enabled when site, line, and description are filled in)
2. **On click**:
   - Show loading spinner
   - Call `POST /api/tags/suggest-name` with current form values
3. **Suggestion panel** (appears below or beside the name field):
   - **Top suggestion** displayed prominently with the tag name
   - **"Use this suggestion"** button → populates the name field and triggers validation
   - **Alternatives section**: 2–3 alternative names, each clickable to select
   - **Evidence/why section**: short explanation of why this name was suggested (e.g., "Similar to existing tag X — matched on description 'discharge pressure'")
   - **Close/dismiss** button
4. **After selecting a suggestion**:
   - Name field is populated
   - Deterministic validator runs automatically
   - If valid → green checkmark
   - If invalid → show validation errors (user can still edit)

**Requirements**

- [ ] Button disabled state: requires at least `site`, `line`, and `description` to be non-empty
- [ ] Loading state with spinner/skeleton
- [ ] Error state if API call fails (show friendly message, don't block form)
- [ ] Panel is dismissible
- [ ] Selecting a suggestion does NOT auto-submit — user must explicitly save
- [ ] Style consistent with existing form UI

**Acceptance criteria**

- Button enables when required fields are filled
- Clicking "Suggest a Name" shows suggestions from the vector index
- "Use this suggestion" populates name and triggers validation
- Alternatives are selectable
- Evidence text is visible and understandable
- Feature is assistive only — never auto-applies or bypasses validation

---

### Issue #15 — Add language normalisation step

**Labels:** `azure`, `ai`, `live-demo`, `priority: low`, `optional`

**Description**

Add a language detection + normalisation step before the semantic query, so descriptions in German/Chinese/etc. still produce correct suggestions.

**Requirements**

- [ ] Detect input language of `description` (Azure AI Language or simple heuristic)
- [ ] If non-English, translate to English before generating the embedding
- [ ] Pass normalised text to the vector search
- [ ] Keep this non-blocking: if translation fails, proceed with original text
- [ ] Create `services/language/normalise.py`

**Acceptance criteria**

- A German description like "Auslassdruck der Hauptpumpe" produces the same suggestion as "outlet pressure of main pump"
- Failure in translation does not break the suggestion flow
