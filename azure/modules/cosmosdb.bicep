@description('Azure region for the Cosmos DB account')
param location string

@description('Cosmos DB account name')
param accountName string

@description('Database name')
param databaseName string

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
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

output endpoint string = cosmosAccount.properties.documentEndpoint
output databaseName string = databaseName
output accountName string = cosmosAccount.name
