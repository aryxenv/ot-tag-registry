using './main.bicep'

param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'ot-tag-registry')
param location = readEnvironmentVariable('AZURE_LOCATION', 'eastus2')
