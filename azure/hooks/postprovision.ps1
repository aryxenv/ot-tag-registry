#!/usr/bin/env pwsh
# postprovision — populate .env files with provisioned values, then seed data.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = git rev-parse --show-toplevel

# ---------------------------------------------------------------------------
# Helper: set a key=value in an .env file (upsert)
# ---------------------------------------------------------------------------
function Set-EnvValue {
    param(
        [string]$FilePath,
        [string]$Key,
        [string]$Value
    )

    if (-not (Test-Path $FilePath)) {
        Write-Warning "$FilePath not found — skipping"
        return
    }

    $content = Get-Content $FilePath -Raw
    $pattern = "(?m)^${Key}=.*$"

    if ($content -match $pattern) {
        $content = $content -replace $pattern, "${Key}=${Value}"
    } else {
        $content = $content.TrimEnd() + "`n${Key}=${Value}`n"
    }

    Set-Content -Path $FilePath -Value $content -NoNewline
}

# ---------------------------------------------------------------------------
# 1. Read all outputs from azd env
# ---------------------------------------------------------------------------
$cosmosEndpoint      = azd env get-value COSMOS_ENDPOINT
$cosmosDatabase      = azd env get-value COSMOS_DATABASE
$searchEndpoint      = azd env get-value SEARCH_ENDPOINT
$searchIndexName     = azd env get-value SEARCH_INDEX_NAME
$projectEndpoint     = azd env get-value PROJECT_ENDPOINT
$embeddingDeployment = azd env get-value PROJECT_EMBEDDING_DEPLOYMENT

# ---------------------------------------------------------------------------
# 2. Populate .env files (RBAC-only — no API keys)
# ---------------------------------------------------------------------------
$envFiles = @(
    (Join-Path $repoRoot "server" ".env"),
    (Join-Path $repoRoot "services" ".env")
)

foreach ($envFile in $envFiles) {
    # Cosmos DB
    Set-EnvValue -FilePath $envFile -Key "COSMOS_ENDPOINT" -Value $cosmosEndpoint
    Set-EnvValue -FilePath $envFile -Key "COSMOS_DATABASE" -Value $cosmosDatabase

    # AI Search
    Set-EnvValue -FilePath $envFile -Key "SEARCH_ENDPOINT" -Value $searchEndpoint
    Set-EnvValue -FilePath $envFile -Key "SEARCH_INDEX_NAME" -Value $searchIndexName

    # AI Foundry
    Set-EnvValue -FilePath $envFile -Key "PROJECT_ENDPOINT" -Value $projectEndpoint
    Set-EnvValue -FilePath $envFile -Key "PROJECT_EMBEDDING_DEPLOYMENT" -Value $embeddingDeployment

    $relative = [System.IO.Path]::GetRelativePath($repoRoot, $envFile)
    Write-Host "Updated $relative with connection details (RBAC auth — no API keys)"
}

# ---------------------------------------------------------------------------
# 4. Install service dependencies and seed data
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Setting up services ==="

$servicesDir = Join-Path $repoRoot "services"
Push-Location $servicesDir

try {
    # Create venv if it doesn't exist
    if (-not (Test-Path (Join-Path $servicesDir ".venv"))) {
        Write-Host "Creating services virtual environment..."
        uv venv
    }

    Write-Host "Installing services dependencies..."
    uv pip install -r requirements.txt --quiet

    # Create AI Search index
    Write-Host "Creating AI Search index (golden-tags)..."
    uv run python -m search.create_index

    # Seed all data (Cosmos DB + AI Search)
    Write-Host "Seeding Cosmos DB and AI Search data..."
    uv run python -m seed_all

    Write-Host ""
    Write-Host "=== Post-provision complete ==="
    Write-Host "All services configured and seeded. Ready to run:"
    Write-Host "  cd server && uv run uvicorn src.main:app --reload"
    Write-Host "  cd client && npm run dev"
}
catch {
    Write-Warning "Seeding failed: $_"
    Write-Warning "You can seed manually later: cd services && uv run python -m seed_all"
}
finally {
    Pop-Location
}
