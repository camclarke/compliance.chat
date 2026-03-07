@description('Storage account name, max length 24 characters, lowercase, no dashes')
param accountName string = 'cmplncstore${uniqueString(resourceGroup().id)}'

@description('Location for the storage account.')
param location string = resourceGroup().location

// Deploy a Standard Storage Account with LRS 
// (Locally Redundant Storage - aligns with the 12-month free tier of 5GB)
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: accountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    supportsHttpsTrafficOnly: true
    allowSharedKeyAccess: true
  }
}

// Create the Blob Service within the Storage Account
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-01-01' = {
  parent: storageAccount
  name: 'default'
}

// Create the "inbox" container where PDFs will be dropped
resource inboxContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-01-01' = {
  parent: blobService
  name: 'inbox'
  properties: {
    publicAccess: 'None' // Keep it fiercely private/secure
  }
}

output storageAccountName string = storageAccount.name
output storageAccountId string = storageAccount.id
