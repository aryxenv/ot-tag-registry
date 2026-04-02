#!/usr/bin/env bash
# setup.sh — One-command dev environment setup for OT Tag Registry.
# Usage: ./setup.sh [--start both|server|client]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
CYAN="\033[0;36m"
RESET="\033[0m"

info()  { echo -e "${GREEN}[✓]${RESET} $*"; }
warn()  { echo -e "${YELLOW}[!]${RESET} $*"; }
err()   { echo -e "${RED}[✗]${RESET} $*" >&2; }
step()  { echo -e "\n${BOLD}${CYAN}=== $* ===${RESET}"; }

# ---------------------------------------------------------------------------
# Parse args
# ---------------------------------------------------------------------------
START_MODE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --start)
            START_MODE="${2:-}"
            if [[ -z "$START_MODE" || ! "$START_MODE" =~ ^(both|server|client)$ ]]; then
                err "Invalid --start value. Use: --start both|server|client"
                exit 1
            fi
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./setup.sh [--start both|server|client]"
            echo ""
            echo "Sets up the OT Tag Registry dev environment:"
            echo "  1. Checks prerequisites (uv, node, az, azd)"
            echo "  2. Installs backend dependencies"
            echo "  3. Installs frontend dependencies"
            echo "  4. Provisions Azure resources via azd up (if needed)"
            echo ""
            echo "Options:"
            echo "  --start both    Start backend + frontend after setup"
            echo "  --start server  Start backend only after setup"
            echo "  --start client  Start frontend only after setup"
            echo "  -h, --help      Show this help"
            exit 0
            ;;
        *)
            err "Unknown option: $1. Use --help for usage."
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# 1. Prerequisites
# ---------------------------------------------------------------------------
step "Checking prerequisites"

missing=()
for tool in uv node az azd; do
    if ! command -v "$tool" &>/dev/null; then
        missing+=("$tool")
    else
        info "$tool found"
    fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
    err "Missing required tools: ${missing[*]}"
    err "Install them before running setup."
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Backend dependencies
# ---------------------------------------------------------------------------
step "Installing backend dependencies"

cd "$REPO_ROOT/server"

if [[ ! -d .venv ]]; then
    uv venv --quiet
    info "Created Python virtual environment"
else
    info "Python virtual environment already exists"
fi

uv pip install -r requirements.txt --quiet
info "Backend dependencies installed"

# ---------------------------------------------------------------------------
# 3. Frontend dependencies
# ---------------------------------------------------------------------------
step "Installing frontend dependencies"

cd "$REPO_ROOT/client"
npm install --silent 2>&1 | tail -1
info "Frontend dependencies installed"

# ---------------------------------------------------------------------------
# 4. Azure provisioning (azd up)
# ---------------------------------------------------------------------------
step "Checking Azure provisioning"

needs_provision=true
env_file="$REPO_ROOT/server/.env"

if [[ -f "$env_file" ]]; then
    cosmos_val=$(grep -oP '^COSMOS_ENDPOINT=\K.+' "$env_file" 2>/dev/null || true)
    if [[ -n "$cosmos_val" ]]; then
        needs_provision=false
    fi
fi

if $needs_provision; then
    warn "Azure resources not yet provisioned (no COSMOS_ENDPOINT in server/.env)"
    info "Running azd up — this provisions Cosmos DB, AI Search, AI Foundry and seeds data..."
    info "You will be prompted to select a subscription and region if this is the first run."
    echo ""
    cd "$REPO_ROOT"
    azd up
    info "Azure provisioning complete"
else
    info "Azure resources already provisioned (server/.env has COSMOS_ENDPOINT)"
    info "To re-provision, run: azd up"
fi

# ---------------------------------------------------------------------------
# 5. Done — print manual start commands
# ---------------------------------------------------------------------------
step "Setup complete"

echo ""
echo -e "Start services manually:"
echo -e "  ${BOLD}Server:${RESET}  cd server && uv run uvicorn src.main:app --reload"
echo -e "  ${BOLD}Client:${RESET}  cd client && npm run dev"
echo ""

# ---------------------------------------------------------------------------
# 6. Optional --start
# ---------------------------------------------------------------------------
if [[ -z "$START_MODE" ]]; then
    exit 0
fi

step "Starting services (--start $START_MODE)"

cleanup() {
    echo ""
    info "Shutting down..."
    [[ -n "${SERVER_PID:-}" ]] && kill "$SERVER_PID" 2>/dev/null && info "Stopped server"
    [[ -n "${CLIENT_PID:-}" ]] && kill "$CLIENT_PID" 2>/dev/null && info "Stopped client"
    wait 2>/dev/null
}
trap cleanup EXIT INT TERM

start_server() {
    cd "$REPO_ROOT/server"
    uv run uvicorn src.main:app --reload --port 8000 &
    SERVER_PID=$!
    info "Server started on http://localhost:8000 (PID $SERVER_PID)"
}

start_client() {
    cd "$REPO_ROOT/client"
    npm run dev &
    CLIENT_PID=$!
    info "Client started on http://localhost:5173 (PID $CLIENT_PID)"
}

case "$START_MODE" in
    server)
        start_server
        wait "$SERVER_PID"
        ;;
    client)
        start_client
        wait "$CLIENT_PID"
        ;;
    both)
        start_server
        start_client
        wait
        ;;
esac
