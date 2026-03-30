#!/usr/bin/env pwsh
# postprovision — write provisioned Cosmos DB values into .env files.

$repoRoot = git rev-parse --show-toplevel

$cosmosEndpoint = azd env get-value COSMOS_ENDPOINT
$cosmosDatabase = azd env get-value COSMOS_DATABASE
$cosmosAccountName = azd env get-value COSMOS_ACCOUNT_NAME
$resourceGroup = azd env get-value AZURE_RESOURCE_GROUP

if (-not $cosmosEndpoint) {
    Write-Warning "COSMOS_ENDPOINT not found in azd env — skipping .env update"
    exit 0
}

# Fetch the primary key via Azure CLI
$cosmosKey = ""
if ($cosmosAccountName -and $resourceGroup) {
    $cosmosKey = az cosmosdb keys list `
        --name $cosmosAccountName `
        --resource-group $resourceGroup `
        --query primaryMasterKey `
        --output tsv
    if ($cosmosKey) {
        Write-Host "Retrieved Cosmos DB primary key"
    } else {
        Write-Warning "Could not retrieve Cosmos DB key — COSMOS_KEY will be left empty"
    }
}

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

$envFiles = @(
    (Join-Path $repoRoot "server" ".env"),
    (Join-Path $repoRoot "services" ".env")
)

foreach ($envFile in $envFiles) {
    Set-EnvValue -FilePath $envFile -Key "COSMOS_ENDPOINT" -Value $cosmosEndpoint
    Set-EnvValue -FilePath $envFile -Key "COSMOS_DATABASE" -Value $cosmosDatabase
    if ($cosmosKey) {
        Set-EnvValue -FilePath $envFile -Key "COSMOS_KEY" -Value $cosmosKey
    }

    $relative = [System.IO.Path]::GetRelativePath($repoRoot, $envFile)
    Write-Host "Updated $relative with Cosmos DB connection details"
}
