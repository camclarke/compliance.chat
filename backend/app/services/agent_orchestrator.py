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
                AzureChatCompletion(
                    service_id="chat",
                    deployment_name=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                    endpoint=settings.AZURE_OPENAI_ENDPOINT,
                    api_key=settings.AZURE_OPENAI_API_KEY,
                )
            )
            logger.info("Successfully added AzureChatCompletion to Semantic Kernel.")
        except Exception as e:
            logger.error(f"Failed to add Azure OpenAI service: {e}")
            
        # Add the custom RAG Plugin so the AI can search the local database
        from app.plugins.compliance_retrieval import ComplianceRetrievalPlugin
        kernel.add_plugin(ComplianceRetrievalPlugin(), plugin_name="ComplianceDatabase")
        logger.info("Successfully loaded ComplianceDatabase plugin.")

        # Add the Live Web Scraper Plugin
        from app.plugins.web_scraper import WebScraperPlugin
        kernel.add_plugin(WebScraperPlugin(), plugin_name="WebScraper")
        logger.info("Successfully loaded WebScraper plugin.")

    return kernel

async def process_chat_message(kernel: sk.Kernel, message: str) -> str:
    """
    Processes a user's chat message using Semantic Kernel.
    Equips the agent with tools (like the RAG Database) to find answers automatically.
    """
    try:
        from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
        from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import AzureChatPromptExecutionSettings

        # Tell the LLM it is allowed to call the plugin functions automatically
        execution_settings = AzureChatPromptExecutionSettings(
            tool_choice="auto",
            temperature=0.0
        )
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        # System prompt ensuring the agent acts strictly as a compliance expert
        prompt = f"""
        You are an expert, multilingual Global Product Compliance Agent acting on behalf of compliance.chat.
        Your goal is to answer manufacturers' questions about importing electronics, medical devices, and other goods.
        
        CRITICAL: If the user asks about specific safety standards, rules, NOMs, FCC regulations, or technical requirements, 
        YOU MUST use the `ComplianceDatabase-search_compliance_rules` tool to search the database first before answering.
        Do not hallucinate limits or rules. Quote the exact rules you find in the database.

        User Question: {message}
        """

        result = await kernel.invoke_prompt(
            prompt,
            settings=execution_settings
        )
        return str(result)
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        return "I apologize, but I encountered an internal error while trying to process your request."
