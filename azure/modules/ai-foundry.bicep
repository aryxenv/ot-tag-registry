@description('Azure region for the AI Foundry resource')
param location string

@description('Name of the AI Foundry resource (AI Services account)')
param accountName string

@description('Name of the AI Project')
param projectName string

@description('Name of the embedding model deployment')
param embeddingDeploymentName string = 'text-embedding-3-large'

@description('Embedding model name')
param embeddingModelName string = 'text-embedding-3-large'

@description('Embedding model version')
param embeddingModelVersion string = '1'

@description('Deployment capacity in thousands of tokens per minute')
param embeddingCapacity int = 120

@description('Name of the chat model deployment')
param chatDeploymentName string = 'gpt-4.1-mini'

@description('Chat model name')
param chatModelName string = 'gpt-4.1-mini'

@description('Chat model version')
param chatModelVersion string = '2025-04-14'

@description('Chat deployment capacity (thousands of tokens per minute)')
param chatCapacity int = 10

// ---------------------------------------------------------------------------
// AI Foundry resource (CognitiveServices/accounts, kind: AIServices)
// Replaces the old Hub + separate Azure OpenAI pattern.
// ---------------------------------------------------------------------------

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  kind: 'AIServices'
  sku: {
    name: 'S0'
  }
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: false
    publicNetworkAccess: 'Enabled'
  }
}

// ---------------------------------------------------------------------------
// AI Project — groups developer resources for a single use case
// ---------------------------------------------------------------------------

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-06-01' = {
  parent: aiFoundry
  name: projectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

// ---------------------------------------------------------------------------
// Embedding model deployment
// ---------------------------------------------------------------------------

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: aiFoundry
  name: embeddingDeploymentName
  sku: {
    name: 'Standard'
    capacity: embeddingCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: embeddingModelName
      version: embeddingModelVersion
    }
  }
}

// ---------------------------------------------------------------------------
// Chat model deployment (Mistral-Large-3)
// ---------------------------------------------------------------------------

resource chatDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = {
  parent: aiFoundry
  name: chatDeploymentName
  dependsOn: [embeddingDeployment]
  sku: {
    name: 'GlobalStandard'
    capacity: chatCapacity
  }
  properties: {
    model: {
      format: 'OpenAI'
      name: chatModelName
      version: chatModelVersion
    }
  }
}

// ---------------------------------------------------------------------------
// Outputs
// ---------------------------------------------------------------------------

output endpoint string = aiFoundry.properties.endpoint
output accountName string = aiFoundry.name
output projectName string = aiProject.name
output embeddingDeploymentName string = embeddingDeployment.name
output chatDeploymentName string = chatDeployment.name
output principalId string = aiFoundry.identity.principalId
