#!/usr/bin/env pwsh
# preprovision — ensure .env files exist in server/ and services/ before provisioning.

$repoRoot = git rev-parse --show-toplevel

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
