#!/usr/bin/env bash
# preprovision — ensure prerequisites, capture user identity, create .env files.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"

# ---------------------------------------------------------------------------
# 1. Prerequisite checks
# ---------------------------------------------------------------------------
missing=()
for tool in az azd uv node; do
    if ! command -v "$tool" &>/dev/null; then
        missing+=("$tool")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo "ERROR: Missing required tools: ${missing[*]}. Please install them before running azd up." >&2
    exit 1
fi

echo "All prerequisites found (az, azd, uv, node)"

# ---------------------------------------------------------------------------
# 2. Capture signed-in user principal ID for RBAC assignments
# ---------------------------------------------------------------------------
principal_id="$(azd env get-value AZURE_PRINCIPAL_ID 2>/dev/null || true)"

if [ -z "$principal_id" ]; then
    echo "Retrieving signed-in user principal ID..."
    principal_id="$(az ad signed-in-user show --query id --output tsv 2>/dev/null || true)"

    if [ -n "$principal_id" ]; then
        azd env set AZURE_PRINCIPAL_ID "$principal_id"
        echo "Set AZURE_PRINCIPAL_ID = $principal_id"
    else
        echo "WARNING: Could not retrieve signed-in user principal ID — RBAC role assignments may fail" >&2
    fi
else
    echo "AZURE_PRINCIPAL_ID already set: $principal_id"
fi

# ---------------------------------------------------------------------------
# 3. Ensure .env files exist in server/ and services/
# ---------------------------------------------------------------------------
for dir in server services; do
    env_file="$REPO_ROOT/$dir/.env"
    example_file="$REPO_ROOT/$dir/.env.example"

    if [ ! -f "$env_file" ]; then
        if [ -f "$example_file" ]; then
            cp "$example_file" "$env_file"
            echo "Created $dir/.env from .env.example"
        else
            echo "WARNING: $dir/.env.example not found — skipping" >&2
        fi
    else
        echo "$dir/.env already exists"
    fi
done
