@description('Name of the Azure Container Registry (must be globally unique and alphanumeric)')
param acrName string = 'cmplncacr${uniqueString(resourceGroup().id)}'

@description('Name of the Container Apps Environment')
param environmentName string = 'cmplnc-env-${uniqueString(resourceGroup().id)}'

@description('Name of the Log Analytics Workspace (required for Container Apps)')
param logAnalyticsName string = 'cmplnc-log-${uniqueString(resourceGroup().id)}'

@description('Name of the Container App')
param containerAppName string = 'compliance-api'

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
resource containerRegistry 'Microsoft.ContainerRegistry/registries@2022-12-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

// 4. Azure Container App (The FastAPI Backend)
resource containerApp 'Microsoft.App/containerApps@2022-10-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: containerAppEnvironment.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest' // Placeholder until ACR push
          resources: {
            cpu: json('1.0')       // Enforced constraint: 1.0 vCPU
            memory: '2.0Gi'        // Enforced constraint: 2.0 GiB RAM
          }
        }
      ]
      scale: {
        minReplicas: 0             // Enforced constraint: Scale-to-Zero
        maxReplicas: 5
      }
    }
  }
}

output acrLoginServer string = containerRegistry.properties.loginServer
output acrName string = containerRegistry.name
output environmentId string = containerAppEnvironment.id
output containerAppFqdn string = containerApp.properties.configuration.ingress.fqdn
