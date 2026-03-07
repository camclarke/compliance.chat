@description('The name of the Azure Function App')
param appName string = 'cmplnc-func-${uniqueString(resourceGroup().id)}'

@description('Deployment location, inheriting from the East US 2 resource group')
param location string = resourceGroup().location

var functionWorkerRuntime = 'python'
var hostingPlanName = '${appName}-plan'
var storageAccountName = 'fnstore${uniqueString(resourceGroup().id)}'

// The Function App needs its own internal storage account for managing state/locks
resource storageAccount 'Microsoft.Storage/storageAccounts@2022-09-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS' // Free Tier eligible
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    allowSharedKeyAccess: true
  }
}

// The Consumption Plan gives you 1,000,000 Free Executions per month 
resource hostingPlan 'Microsoft.Web/serverfarms@2022-03-01' = {
  name: hostingPlanName
  location: location
  sku: {
    name: 'Y1' // "Y1" stands for Dynamic Serverless Consumption
    tier: 'Dynamic'
  }
  properties: {
    reserved: true // Required for deploying a Linux-based Python function
  }
}

// The actual Azure Function Python environment
resource functionApp 'Microsoft.Web/sites@2022-03-01' = {
  name: appName
  location: location
  kind: 'functionapp,linux'
  identity: {
    type: 'SystemAssigned' // Managed Identity for security
  }
  properties: {
    serverFarmId: hostingPlan.id
    siteConfig: {
      linuxFxVersion: 'python|3.11' // Python 3.11 Environment
      appSettings: [
        {
          name: 'AzureWebJobsStorage'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'WEBSITE_CONTENTAZUREFILECONNECTIONSTRING'
          value: 'DefaultEndpointsProtocol=https;AccountName=${storageAccountName};EndpointSuffix=${environment().suffixes.storage};AccountKey=${storageAccount.listKeys().keys[0].value}'
        }
        {
          name: 'WEBSITE_CONTENTSHARE'
          value: toLower(appName)
        }
        {
          name: 'FUNCTIONS_EXTENSION_VERSION'
          value: '~4'
        }
        {
          name: 'FUNCTIONS_WORKER_RUNTIME'
          value: functionWorkerRuntime
        }
      ]
    }
    httpsOnly: true
  }
}

output functionAppName string = functionApp.name
