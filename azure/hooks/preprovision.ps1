#!/usr/bin/env pwsh
# preprovision — ensure prerequisites, capture user identity, create .env files.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel

# ---------------------------------------------------------------------------
# 1. Prerequisite checks
# ---------------------------------------------------------------------------
$missing = @()
foreach ($tool in @("az", "azd", "uv", "node")) {
    if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) {
        $missing += $tool
    }
}

if ($missing.Count -gt 0) {
    Write-Error "Missing required tools: $($missing -join ', '). Please install them before running azd up."
    exit 1
}

Write-Host "All prerequisites found (az, azd, uv, node)"

# ---------------------------------------------------------------------------
# 2. Capture signed-in user principal ID for RBAC assignments
# ---------------------------------------------------------------------------
$principalId = azd env get-value AZURE_PRINCIPAL_ID 2>$null

if (-not $principalId) {
    Write-Host "Retrieving signed-in user principal ID..."
    $principalId = az ad signed-in-user show --query id --output tsv 2>$null

    if ($principalId) {
        azd env set AZURE_PRINCIPAL_ID $principalId
        Write-Host "Set AZURE_PRINCIPAL_ID = $principalId"
    } else {
        Write-Warning "Could not retrieve signed-in user principal ID — RBAC role assignments may fail"
    }
}
else {
    Write-Host "AZURE_PRINCIPAL_ID already set: $principalId"
}

# ---------------------------------------------------------------------------
# 3. Ensure .env files exist in server/ and services/
# ---------------------------------------------------------------------------
$envPairs = @(
    @{ Dir = "server";   Example = "server/.env.example" }
    @{ Dir = "services"; Example = "services/.env.example" }
)

foreach ($pair in $envPairs) {
    $envFile = Join-Path $repoRoot $pair.Dir ".env"
    $exampleFile = Join-Path $repoRoot $pair.Example

    if (-not (Test-Path $envFile)) {
        if (Test-Path $exampleFile) {
            Copy-Item $exampleFile $envFile
            Write-Host "Created $($pair.Dir)/.env from .env.example"
        } else {
            Write-Warning "$($pair.Example) not found — skipping"
        }
    } else {
        Write-Host "$($pair.Dir)/.env already exists"
    }
}
