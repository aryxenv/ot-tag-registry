@description('Name of the Cosmos DB account')
param cosmosAccountName string

@description('Principal ID to assign the role to')
param principalId string

@description('Cosmos DB built-in role definition ID (GUID only)')
@allowed([
  '00000000-0000-0000-0000-000000000001' // Built-in Data Reader
  '00000000-0000-0000-0000-000000000002' // Built-in Data Contributor
])
param roleDefinitionId string

resource cosmosAccount 'Microsoft.DocumentDB/databaseAccounts@2024-05-15' existing = {
  name: cosmosAccountName
}

resource sqlRoleAssignment 'Microsoft.DocumentDB/databaseAccounts/sqlRoleAssignments@2024-05-15' = {
  parent: cosmosAccount
  name: guid(cosmosAccount.id, principalId, roleDefinitionId)
  properties: {
    principalId: principalId
    roleDefinitionId: '${cosmosAccount.id}/sqlRoleDefinitions/${roleDefinitionId}'
    scope: cosmosAccount.id
  }
}
