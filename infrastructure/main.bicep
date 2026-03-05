@description('Name of the Form Recognizer (Document Intelligence) resource.')
param accountName string = 'compliancedocintel-${uniqueString(resourceGroup().id)}'

@description('Location for all resources.')
param location string = resourceGroup().location

@description('Pricing tier of the Document Intelligence resource. F0 is free (if available), S0 is standard.')
@allowed([
  'F0'
  'S0'
])
param sku string = 'S0'

resource documentIntelligence 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: accountName
  location: location
  sku: {
    name: sku
  }
  kind: 'FormRecognizer' // FormRecognizer is the underlying kind for Document Intelligence
  properties: {
    publicNetworkAccess: 'Enabled'
    customSubDomainName: accountName
  }
}

output endpoint string = documentIntelligence.properties.endpoint
output accountId string = documentIntelligence.id
output name string = documentIntelligence.name
