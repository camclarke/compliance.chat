# Azure Free Services for `compliance.chat`

To keep operational costs at essentially zero dollars while maintaining an Enterprise Architecture, our project takes advantage of Microsoft's **Free Tier** offerings. 

Below is a curated list of relevant Azure services that offer perpetual (Always Free) or 12-month free tiers, directly matched to our project's architecture:

## 1. AI & Machine Learning Services
*   **Azure Document Intelligence:** Microsoft's premium PDF and forms extractor.
    *   *Free Tier:* 500 pages per month (F0 or S0 12-month tier depending on region availability).
*   **Azure AI Search (Optional add-on):** Cloud search service.
    *   *Free Tier:* 50 MB storage for 10,000 hosted documents and 3 indexes per service (Always Free).
*   **Azure OpenAI (Embeddings & Chat):** While there is no strict "Free" tier for GPT-4o, the cost of `text-embedding-3-small` is fractions of a cent per 1,000 tokens. Using it exclusively for local ingestion is functionally free.

## 2. Global Vector Storage & Databases
*   **Azure Cosmos DB:** Our chosen global vector database.
    *   *Always Free Option:* 1,000 Request Units (RU/s) provisioned throughput with 25 GB of storage. 
    *   *Note:* Ensure you select the "Apply Free Tier Discount" toggle when creating the Cosmos DB account.
*   **Azure Cosmos DB for MongoDB (vCore):** Alternative vector deployment.
    *   *Always Free Option:* A dedicated MongoDB cluster with 32 GB storage.

## 3. Compute & Backend Hosting
When we deploy the FastAPI backend from our local PC to the cloud, we will use these free compute options:
*   **Azure App Service:** Fully managed platform for web apps and APIs.
    *   *Always Free Option:* Up to 10 web/API apps with 1 GB storage and 1 hour of compute per day (F1 Tier).
*   **Azure Container Apps:** Serverless containers for microservices.
    *   *Always Free Option:* 180,000 vCPU seconds, 360,000 GiB seconds, and 2 million requests per month.
*   **Azure Functions:** Serverless code architecture (great for triggering the Document Intelligence pipeline in the cloud later).
    *   *Always Free Option:* 1 million executions per month.

## 4. Frontend & Application Hosting
*   **Azure Static Web Apps:** Perfect for hosting our React/Vite Single Page Application frontend.
    *   *Always Free Option:* 100 GB bandwidth per subscription, 2 custom domains, and 0.5 GB storage per app.

*Source:* [Azure Free Services Page](https://azure.microsoft.com/en-us/pricing/free-services/)
