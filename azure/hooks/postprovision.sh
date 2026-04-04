#!/usr/bin/env bash
# postprovision — populate .env files with provisioned values, then seed data.

set -euo pipefail

# Force Python to use UTF-8 on Windows (avoids cp1252 encoding errors)
export PYTHONUTF8=1

REPO_ROOT="$(git rev-parse --show-toplevel)"

# ---------------------------------------------------------------------------
# Helper: set a key=value in an .env file (upsert, cross-platform)
# ---------------------------------------------------------------------------
set_env_value() {
    local file="$1" key="$2" value="$3"

    if [ ! -f "$file" ]; then
        echo "WARNING: $file not found — skipping" >&2
        return
    fi

    local tmp="${file}.tmp"
    if grep -q "^${key}=" "$file" 2>/dev/null; then
        sed "s|^${key}=.*|${key}=${value}|" "$file" > "$tmp" && mv "$tmp" "$file"
    else
        printf '%s\n' "${key}=${value}" >> "$file"
    fi
}

# ---------------------------------------------------------------------------
# 1. Read all outputs from azd env
# ---------------------------------------------------------------------------
cosmos_endpoint="$(azd env get-value COSMOS_ENDPOINT)"
cosmos_database="$(azd env get-value COSMOS_DATABASE)"
search_endpoint="$(azd env get-value SEARCH_ENDPOINT)"
search_index_name="$(azd env get-value SEARCH_INDEX_NAME)"
project_endpoint="$(azd env get-value PROJECT_ENDPOINT)"
project_name="$(azd env get-value PROJECT_NAME)"
ai_services_endpoint="$(azd env get-value AI_SERVICES_ENDPOINT)"
embedding_deployment="$(azd env get-value PROJECT_EMBEDDING_DEPLOYMENT)"
chat_deployment="$(azd env get-value PROJECT_CHAT_DEPLOYMENT)"
# ---------------------------------------------------------------------------
# 2. Populate .env files (RBAC-only — no API keys)
# ---------------------------------------------------------------------------
for env_file in "$REPO_ROOT/server/.env" "$REPO_ROOT/services/.env"; do
    # Cosmos DB
    set_env_value "$env_file" "COSMOS_ENDPOINT" "$cosmos_endpoint"
    set_env_value "$env_file" "COSMOS_DATABASE" "$cosmos_database"

    # AI Search
    set_env_value "$env_file" "SEARCH_ENDPOINT" "$search_endpoint"
    set_env_value "$env_file" "SEARCH_INDEX_NAME" "$search_index_name"

    # AI Foundry
    set_env_value "$env_file" "PROJECT_ENDPOINT" "$project_endpoint"
    set_env_value "$env_file" "PROJECT_NAME" "$project_name"
    set_env_value "$env_file" "AI_SERVICES_ENDPOINT" "$ai_services_endpoint"
    set_env_value "$env_file" "PROJECT_EMBEDDING_DEPLOYMENT" "$embedding_deployment"
    set_env_value "$env_file" "PROJECT_CHAT_DEPLOYMENT" "$chat_deployment"

    relative="${env_file#"$REPO_ROOT/"}"
    echo "Updated $relative with connection details (RBAC auth — no API keys)"
done

# ---------------------------------------------------------------------------
# 3. Install service dependencies and seed data
# ---------------------------------------------------------------------------
echo ""
echo "=== Setting up services ==="

services_dir="$REPO_ROOT/services"
cd "$services_dir"

cleanup() { cd "$REPO_ROOT"; }
trap cleanup EXIT

# Create venv if it doesn't exist
if [ ! -d "$services_dir/.venv" ]; then
    echo "Creating services virtual environment..."
    uv venv
fi

echo "Installing services dependencies..."
uv pip install -r requirements.txt --quiet

# Create AI Search index
echo "Creating AI Search index (golden-tags)..."
uv run python -m search.create_index

# Seed all data (Cosmos DB + AI Search)
echo "Seeding Cosmos DB and AI Search data..."
if uv run python -m seed_all; then
    echo ""
    echo "=== Setting up AI agent ==="
    echo "Creating auto-fill agent on AI Foundry..."
    # The AI Foundry project may take time to propagate after fresh creation.
    # Retry up to 3 times with a delay between attempts.
    agent_ok=false
    for attempt in 1 2 3; do
        if uv run python -m agent.setup_agent 2>&1; then
            agent_ok=true
            break
        fi
        echo "  ⚠ Agent setup attempt $attempt failed — retrying in 30s..."
        sleep 30
    done
    if [ "$agent_ok" = false ]; then
        echo "WARNING: Agent setup failed after 3 attempts." >&2
        echo "WARNING: Run manually later: cd services && uv run python -m agent.setup_agent" >&2
    fi

    echo ""
    echo "=== Post-provision complete ==="
    echo "All services configured and seeded. Ready to run:"
    echo "  cd server && uv run uvicorn src.main:app --reload"
    echo "  cd client && npm run dev"
else
    echo "WARNING: Seeding failed." >&2
    echo "WARNING: You can seed manually later: cd services && uv run python -m seed_all" >&2
fi
