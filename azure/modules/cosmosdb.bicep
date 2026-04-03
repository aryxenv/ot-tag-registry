@description('Azure region for the Cosmos DB account')
param location string

@description('Cosmos DB account name')
param accountName string

@description('Database name')
param databaseName string

@description('Principal ID to assign Cosmos DB data plane access')
param principalId string

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    publicNetworkAccess: 'Enabled'
    isVirtualNetworkFilterEnabled: false
    ipRules: []
    capabilities: [
      { name: 'EnableServerless' }
    ]
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
  }
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2024-05-15' = {
  parent: cosmosAccount
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

var containers = [
  { name: 'assets', partitionKey: '/site' }
  { name: 'tags', partitionKey: '/assetId' }
  { name: 'sources', partitionKey: '/systemType' }
  { name: 'l1Rules', partitionKey: '/tagId' }
  { name: 'l2Rules', partitionKey: '/tagId' }
]

resource sqlContainers 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2024-05-15' = [
  for container in containers: {
    parent: database
    name: container.name
    properties: {
      resource: {
        id: container.name
        partitionKey: {
          paths: [container.partitionKey]
          kind: 'Hash'
        }
      }
    }
  }
]

// Cosmos DB Built-in Data Contributor — data plane access via DefaultAzureCredential
resource cosmosDataContributor 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, principalId, '00000000-0000-0000-0000-000000000002')
  properties: {
    principalId: principalId
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/00000000-0000-0000-0000-000000000002'
    scope: cosmosAccount.id
  }
}

output endpoint string = cosmosAccount.properties.documentEndpoint
output databaseName string = databaseName
output accountName string = cosmosAccount.name
