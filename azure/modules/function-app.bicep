@description('Azure region for the Function App')
param location string

@description('Name prefix for Function App resources')
param namePrefix string

@description('Tags to apply to resources (must include azd-env-name and azd-service-name)')
param tags object = {}

@description('Cosmos DB endpoint for the assets container')
param cosmosEndpoint string

@description('Cosmos DB database name')
param cosmosDatabaseName string

// ---------------------------------------------------------------------------
// Storage Account (required by Function App runtime — managed identity only)
// ---------------------------------------------------------------------------

var storageAccountName = replace('st${namePrefix}', '-', '')
var deploymentContainerName = 'app-package-func-${namePrefix}'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
    allowSharedKeyAccess: false
    allowBlobPublicAccess: false
    publicNetworkAccess: 'Enabled'
  }

  // Deployment blob container
  resource blobServices 'blobServices' = {
    name: 'default'
    resource deployContainer 'containers' = {
      name: deploymentContainerName
    }
  }
}

// ---------------------------------------------------------------------------
// Storage role assignments — Function App MI needs blob + queue + table access
// ---------------------------------------------------------------------------

// Storage Blob Data Owner — for deployment artifacts + AzureWebJobsStorage blobs
resource storageBlobRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, functionApp.id, 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')
  properties: {
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b')
  }
}

// Storage Queue Data Contributor — required for AzureWebJobsStorage
resource storageQueueRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, functionApp.id, '974c5e8b-45b9-4653-ba55-5f855dd0fb88')
  properties: {
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '974c5e8b-45b9-4653-ba55-5f855dd0fb88')
  }
}

// Storage Table Data Contributor — for AzureWebJobsStorage tables
resource storageTableRole 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: storageAccount
  name: guid(storageAccount.id, functionApp.id, '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3')
  properties: {
    principalId: functionApp.identity.principalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3')
  }
}

// ---------------------------------------------------------------------------
// App Service Plan (Flex Consumption)
// ---------------------------------------------------------------------------

resource appServicePlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: 'plan-${namePrefix}'
  location: location
  sku: {
    name: 'FC1'
    tier: 'FlexConsumption'
  }
  properties: {
    reserved: true // Linux
  }
}

// ---------------------------------------------------------------------------
// Function App (Flex Consumption — managed identity storage)
// ---------------------------------------------------------------------------

resource functionApp 'Microsoft.Web/sites@2024-04-01' = {
  name: 'func-${namePrefix}'
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned'
  }
  tags: tags
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    functionAppConfig: {
      deployment: {
        storage: {
          type: 'blobContainer'
          value: '${storageAccount.properties.primaryEndpoints.blob}${deploymentContainerName}'
          authentication: {
            type: 'SystemAssignedIdentity'
          }
        }
      }
      scaleAndConcurrency: {
        maximumInstanceCount: 100
        instanceMemoryMB: 2048
      }
      runtime: {
        name: 'python'
        version: '3.11'
      }
    }
    siteConfig: {
      appSettings: [
        { name: 'AzureWebJobsStorage__credential', value: 'managedidentity' }
        { name: 'AzureWebJobsStorage__blobServiceUri', value: storageAccount.properties.primaryEndpoints.blob }
        { name: 'AzureWebJobsStorage__queueServiceUri', value: storageAccount.properties.primaryEndpoints.queue }
        { name: 'AzureWebJobsStorage__tableServiceUri', value: storageAccount.properties.primaryEndpoints.table }
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'COSMOS_ENDPOINT', value: cosmosEndpoint }
        { name: 'COSMOS_DATABASE', value: cosmosDatabaseName }
      ]
    }
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

output functionAppUrl string = 'https://${functionApp.properties.defaultHostName}'
output functionAppName string = functionApp.name
output principalId string = functionApp.identity.principalId
output storageAccountName string = storageAccount.name
