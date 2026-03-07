@description('Name of the Azure Container Registry (must be globally unique and alphanumeric)')
param acrName string = 'cmplncacr${uniqueString(resourceGroup().id)}'

@description('Name of the Container Apps Environment')
param environmentName string = 'cmplnc-env-${uniqueString(resourceGroup().id)}'

@description('Name of the Log Analytics Workspace (required for Container Apps)')
param logAnalyticsName string = 'cmplnc-log-${uniqueString(resourceGroup().id)}'

@description('Deployment location, inheriting from the East US 2 resource group')
param location string = resourceGroup().location

// 1. Log Analytics Workspace (Required to host a Container Apps Environment)
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
  }
}

// 2. Azure Container Apps Environment (Consumption Tier)
// This is the underlying free-tier eligible orchestrator
resource containerAppEnvironment 'Microsoft.App/managedEnvironments@2022-10-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logAnalytics.properties.customerId
        sharedKey: logAnalytics.listKeys().primarySharedKey
      }
    }
  }
}

// 3. Azure Container Registry (Basic Tier)
// This is where we will securely push our built Docker image
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2022-12-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic' // Most cost-effective tier for an MVP
  }
  properties: {
    adminUserEnabled: true // Required for the Container App to pull the image easily
  }
}

output acrLoginServer string = containerRegistry.properties.loginServer
output acrName string = containerRegistry.name
output environmentId string = containerAppEnvironment.id
