@description('Azure region for the AI Search service')
param location string

@description('Name of the AI Search service')
param serviceName string

@description('SKU for the AI Search service (basic supports 3072-dim vector search)')
@allowed(['basic', 'standard', 'standard2', 'standard3'])
param sku string = 'basic'

resource searchService 'Microsoft.Search/searchServices@2024-06-01-preview' = {
  name: serviceName
  location: location
  sku: {
    name: sku
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    replicaCount: 1
    partitionCount: 1
    hostingMode: 'default'
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
  }
}

output endpoint string = 'https://${searchService.name}.search.windows.net'
output name string = searchService.name
output id string = searchService.id
