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
$cosmosAccountName   = azd env get-value COSMOS_ACCOUNT_NAME
$resourceGroup       = azd env get-value AZURE_RESOURCE_GROUP
$searchEndpoint      = azd env get-value SEARCH_ENDPOINT
$searchServiceName   = azd env get-value SEARCH_SERVICE_NAME
$searchIndexName     = azd env get-value SEARCH_INDEX_NAME
$projectEndpoint     = azd env get-value PROJECT_ENDPOINT
$embeddingDeployment = azd env get-value PROJECT_EMBEDDING_DEPLOYMENT

# ---------------------------------------------------------------------------
# 2. Retrieve API keys (fallback auth alongside DefaultAzureCredential)
# ---------------------------------------------------------------------------

# Cosmos DB primary key
$cosmosKey = ""
if ($cosmosAccountName -and $resourceGroup) {
    $cosmosKey = az cosmosdb keys list `
        --name $cosmosAccountName `
        --resource-group $resourceGroup `
        --query primaryMasterKey `
        --output tsv 2>$null
    if ($cosmosKey) {
        Write-Host "Retrieved Cosmos DB primary key"
    } else {
        Write-Warning "Could not retrieve Cosmos DB key — COSMOS_KEY will be left empty"
    }
}

# AI Search admin key
$searchApiKey = ""
if ($searchServiceName -and $resourceGroup) {
    $searchApiKey = az search admin-key show `
        --service-name $searchServiceName `
        --resource-group $resourceGroup `
        --query primaryKey `
        --output tsv 2>$null
    if ($searchApiKey) {
        Write-Host "Retrieved AI Search admin key"
    } else {
        Write-Warning "Could not retrieve AI Search key — SEARCH_API_KEY will be left empty (RBAC will be used)"
    }
}

# ---------------------------------------------------------------------------
# 3. Populate .env files
# ---------------------------------------------------------------------------
$envFiles = @(
    (Join-Path $repoRoot "server" ".env"),
    (Join-Path $repoRoot "services" ".env")
)

foreach ($envFile in $envFiles) {
    # Cosmos DB
    Set-EnvValue -FilePath $envFile -Key "COSMOS_ENDPOINT" -Value $cosmosEndpoint
    Set-EnvValue -FilePath $envFile -Key "COSMOS_DATABASE" -Value $cosmosDatabase
    if ($cosmosKey) {
        Set-EnvValue -FilePath $envFile -Key "COSMOS_KEY" -Value $cosmosKey
    }

    # AI Search
    Set-EnvValue -FilePath $envFile -Key "SEARCH_ENDPOINT" -Value $searchEndpoint
    Set-EnvValue -FilePath $envFile -Key "SEARCH_INDEX_NAME" -Value $searchIndexName
    if ($searchApiKey) {
        Set-EnvValue -FilePath $envFile -Key "SEARCH_API_KEY" -Value $searchApiKey
    }

    # AI Foundry
    Set-EnvValue -FilePath $envFile -Key "PROJECT_ENDPOINT" -Value $projectEndpoint
    Set-EnvValue -FilePath $envFile -Key "PROJECT_EMBEDDING_DEPLOYMENT" -Value $embeddingDeployment

    $relative = [System.IO.Path]::GetRelativePath($repoRoot, $envFile)
    Write-Host "Updated $relative with all connection details"
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
