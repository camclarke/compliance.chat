import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    PROJECT_NAME = "Compliance.chat API"
    VERSION = "1.0.0"
    
    # Azure OpenAI Settings
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    # Azure Model Router: single endpoint for dynamic LLM selection
    AZURE_OPENAI_CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "model-router")
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")

    # Azure Cosmos DB (Chat History)
    AZURE_COSMOS_ENDPOINT = os.getenv("AZURE_COSMOS_ENDPOINT", "")
    AZURE_COSMOS_KEY = os.getenv("AZURE_COSMOS_KEY", "")
    AZURE_COSMOS_DATABASE = os.getenv("AZURE_COSMOS_DATABASE", "ComplianceDB")
    AZURE_COSMOS_CONTAINER = os.getenv("AZURE_COSMOS_CONTAINER", "ChatHistory")

    # Billing / Dodo Payments
    DODO_PAYMENTS_API_KEY = os.getenv("DODO_PAYMENTS_API_KEY", "")
    DODO_WEBHOOK_SECRET = os.getenv("DODO_WEBHOOK_SECRET", "")
    DODO_ENVIRONMENT = os.getenv("DODO_ENVIRONMENT", "test_mode")
    DODO_PRODUCT_PRO = os.getenv("DODO_PRODUCT_PRO", "placeholder_pro_product_id")
    DODO_PRODUCT_MAX = os.getenv("DODO_PRODUCT_MAX", "placeholder_max_product_id")
    DODO_PRODUCT_ELITE = os.getenv("DODO_PRODUCT_ELITE", "placeholder_elite_product_id")

settings = Settings()
