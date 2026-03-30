targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment (used to generate resource names)')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@description('Cosmos DB database name')
param cosmosDatabaseName string = 'ot-tag-registry'

var resourceGroupName = 'rg-${environmentName}'

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
}

module cosmosDb 'modules/cosmosdb.bicep' = {
  scope: rg
  name: 'cosmosdb'
  params: {
    location: location
    accountName: 'cosmos-${environmentName}'
    databaseName: cosmosDatabaseName
  }
}

output COSMOS_ENDPOINT string = cosmosDb.outputs.endpoint
output COSMOS_DATABASE string = cosmosDb.outputs.databaseName
output COSMOS_ACCOUNT_NAME string = cosmosDb.outputs.accountName
output AZURE_RESOURCE_GROUP string = rg.name
