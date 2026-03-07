@description('Cosmos DB account name, max length 44 characters, lowercase')
param accountName string = 'cmplnc-cosmos-${uniqueString(resourceGroup().id)}'

@description('Location for the Cosmos DB account.')
param location string = resourceGroup().location

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: accountName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    databaseAccountOfferType: 'Standard'
    
    // ==========================================================
    // CRITICAL BILLING SAFEGUARD
    // This absolutely guarantees the "Apply Free Tier Discount" 
    // is checked and enforced at the Azure Resource Manager level.
    // If the subscription already has a free tier account, this
    // deployment will fail rather than charge you money.
    enableFreeTier: true 
    // ==========================================================

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

// Create the Database (Sharing the 1000 RU/s free throughput)
resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2023-04-15' = {
  parent: cosmosDbAccount
  name: 'ComplianceDB'
  properties: {
    resource: {
      id: 'ComplianceDB'
    }
    options: {
      throughput: 1000 // Free Tier limit
    }
  }
}

// Container: All Documents (Single-Storage Approach)
resource documentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2023-04-15' = {
  parent: database
  name: 'documents'
  properties: {
    resource: {
      id: 'documents'
      partitionKey: {
        paths: [
          '/id'
        ]
        kind: 'Hash'
      }
    }
  }
}

output endpoint string = cosmosDbAccount.properties.documentEndpoint
output id string = cosmosDbAccount.id
output name string = cosmosDbAccount.name
