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

@description('SKU for the AI Search service')
@allowed(['basic', 'standard', 'standard2', 'standard3'])
param searchSku string = 'basic'

@description('Principal ID of the signed-in user (set by preprovision hook)')
param principalId string

var resourceGroupName = 'rg-${environmentName}'

resource rg 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
}

// ---------------------------------------------------------------------------
// Modules
// ---------------------------------------------------------------------------

module cosmosDb 'modules/cosmosdb.bicep' = {
  scope: rg
  name: 'cosmosdb'
  params: {
    location: location
    accountName: 'cosmos-${environmentName}'
    databaseName: cosmosDatabaseName
    principalId: principalId
  }
}

module aiSearch 'modules/ai-search.bicep' = {
  scope: rg
  name: 'ai-search'
  params: {
    location: location
    serviceName: 'search-${environmentName}'
    sku: searchSku
  }
}

module aiFoundry 'modules/ai-foundry.bicep' = {
  scope: rg
  name: 'ai-foundry'
  params: {
    location: location
    accountName: 'ai-${environmentName}'
    projectName: 'ai-${environmentName}-proj'
  }
}

module functionApp 'modules/function-app.bicep' = {
  scope: rg
  name: 'function-app'
  params: {
    location: location
    namePrefix: environmentName
    tags: {
      'azd-env-name': environmentName
      'azd-service-name': 'functions'
    }
    cosmosEndpoint: cosmosDb.outputs.endpoint
    cosmosDatabaseName: cosmosDatabaseName
  }
}

// ---------------------------------------------------------------------------
// Role assignments — signed-in user
// ---------------------------------------------------------------------------

// Cognitive Services OpenAI User — for embedding generation via AI Services
module userCogServicesRole 'modules/role-assignment.bicep' = {
  scope: rg
  name: 'user-cog-services-role'
  params: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd' // Cognitive Services OpenAI User
  }
}

// Search Index Data Contributor — for querying + writing index data
module userSearchDataRole 'modules/role-assignment.bicep' = {
  scope: rg
  name: 'user-search-data-role'
  params: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7' // Search Index Data Contributor
  }
}

// Search Service Contributor — for managing index schemas
module userSearchServiceRole 'modules/role-assignment.bicep' = {
  scope: rg
  name: 'user-search-service-role'
  params: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0' // Search Service Contributor
  }
}

// Azure AI Developer — for AIProjectClient access to AI Foundry
module userAiDevRole 'modules/role-assignment.bicep' = {
  scope: rg
  name: 'user-ai-developer-role'
  params: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: '64702f94-c441-49e6-a78b-ef80e0188fee' // Azure AI Developer
  }
}

// Cosmos DB Built-in Data Reader — for Function App to query assets (data plane role)
module funcCosmosReaderRole 'modules/cosmos-role.bicep' = {
  scope: rg
  name: 'func-cosmos-reader-role'
  params: {
    cosmosAccountName: cosmosDb.outputs.accountName
    principalId: functionApp.outputs.principalId
    roleDefinitionId: '00000000-0000-0000-0000-000000000001' // Built-in Data Reader
  }
}

// Storage Blob Data Owner — for signed-in user to deploy to Function App blob container
module userFuncStorageBlobRole 'modules/role-assignment.bicep' = {
  scope: rg
  name: 'user-func-storage-blob-role'
  params: {
    principalId: principalId
    principalType: 'User'
    roleDefinitionId: 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b' // Storage Blob Data Owner
  }
}

// ---------------------------------------------------------------------------
// Outputs (automatically stored in azd env)
// ---------------------------------------------------------------------------

output COSMOS_ENDPOINT string = cosmosDb.outputs.endpoint
output COSMOS_DATABASE string = cosmosDb.outputs.databaseName
output COSMOS_ACCOUNT_NAME string = cosmosDb.outputs.accountName
output SEARCH_ENDPOINT string = aiSearch.outputs.endpoint
output SEARCH_SERVICE_NAME string = aiSearch.outputs.name
output SEARCH_INDEX_NAME string = 'golden-tags'
output PROJECT_ENDPOINT string = aiFoundry.outputs.projectEndpoint
output AI_SERVICES_ENDPOINT string = aiFoundry.outputs.endpoint
output PROJECT_NAME string = aiFoundry.outputs.projectName
output PROJECT_EMBEDDING_DEPLOYMENT string = aiFoundry.outputs.embeddingDeploymentName
output PROJECT_CHAT_DEPLOYMENT string = aiFoundry.outputs.chatDeploymentName
output AI_SERVICES_ACCOUNT_NAME string = aiFoundry.outputs.accountName
output FUNCTION_APP_URL string = functionApp.outputs.functionAppUrl
output AZURE_RESOURCE_GROUP string = rg.name
