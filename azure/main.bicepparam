using './main.bicep'

param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'ot-tag-registry')
param location = readEnvironmentVariable('AZURE_LOCATION', 'swedencentral')
param principalId = readEnvironmentVariable('AZURE_PRINCIPAL_ID', '')
