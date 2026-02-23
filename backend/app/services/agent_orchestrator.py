import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def create_kernel() -> sk.Kernel:
    """
    Initializes Semantic Kernel with the configured Azure OpenAI services.
    """
    kernel = sk.Kernel()

    if settings.AZURE_OPENAI_API_KEY and settings.AZURE_OPENAI_ENDPOINT:
        try:
            kernel.add_service(
                sk.services.AzureChatCompletion(
                    service_id="chat",
                    deployment_name=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                    endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                )
            )
            logger.info("Successfully added AzureChatCompletion to Semantic Kernel.")
        except Exception as e:
            logger.error(f"Failed to add Azure OpenAI service: {e}")
    else:
        logger.warning("Azure OpenAI credentials are not fully configured.")

    return kernel

async def process_chat_message(kernel: sk.Kernel, message: str) -> str:
    """
    Processes a user's chat message using the Semantic Kernel.
    Currently acts as a pass-through to the LLM. 
    Future iterations will include the Multi-Agent Swarm logic.
    """
    prompt = f"""
    You are the compliance.chat expert AI agent. 
    You specialize in product compliance, importation laws, FCC, CE, ANATEL, etc.
    Answer the user's question accurately. If you don't know, say you don't know.
    
    User: {message}
    """
    
    # Phase 1: Simple invoke. We will upgrade this to use Plugins and Planners for Multi-Agent logic.
    result = await kernel.invoke_prompt(prompt)
    return str(result)
