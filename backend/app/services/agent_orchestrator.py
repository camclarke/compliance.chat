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

async def process_chat_message(
    kernel: sk.Kernel, 
    message: str, 
    file_content: bytes = None, 
    file_name: str = None, 
    file_content_type: str = None
) -> str:
    """
    Processes a user's chat message using Semantic Kernel.
    Equips the agent with tools (like the RAG Database) to find answers automatically.
    Also handles Multimodal processing (Images and PDFs).
    """
    try:
        from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
        from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import AzureChatPromptExecutionSettings
        from semantic_kernel.contents import ChatHistory, TextContent, ImageContent

        # Tell the LLM it is allowed to call the plugin functions automatically
        execution_settings = AzureChatPromptExecutionSettings(
            tool_choice="auto",
            temperature=0.0
        )
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        chat_history = ChatHistory()
        
        # System prompt ensuring the agent acts strictly as a compliance expert
        system_instruction = """
        You are an expert, multilingual Global Product Compliance Agent acting on behalf of compliance.chat.
        Your goal is to answer manufacturers' questions about importing electronics, medical devices, and other goods.
        
        CRITICAL: If the user asks about specific safety standards, rules, NOMs, FCC regulations, or technical requirements, 
        YOU MUST use the `ComplianceDatabase-search_compliance_rules` tool to search the database first before answering.
        Do not hallucinate limits or rules. Quote the exact rules you find in the database.
        If the user uploaded a product image or PDF datasheet, strictly evaluate the product specifications shown in the file against the retrieved safety rules to determine a Pass/Fail outcome.
        """
        chat_history.add_system_message(system_instruction)

        # Build User Message Contents
        user_contents = []
        user_contents.append(TextContent(text=f"User Question: {message}"))

        if file_content:
            if file_content_type and file_content_type.startswith('image/'):
                import base64
                base64_img = base64.b64encode(file_content).decode('utf-8')
                data_uri = f"data:{file_content_type};base64,{base64_img}"
                logger.info("Injecting Multimodal Image directly into semantic context window.")
                user_contents.append(ImageContent(uri=data_uri))
            
            elif file_content_type == 'application/pdf':
                try:
                    import io
                    from pypdf import PdfReader
                    pdf = PdfReader(io.BytesIO(file_content))
                    text_extracted = ""
                    for page in pdf.pages:
                        extracted = page.extract_text()
                        if extracted:
                            text_extracted += extracted + "\n"
                    
                    # Limit PDF text to roughly 5000 characters to prevent context window blowouts
                    limited_text = text_extracted[:5000]
                    logger.info(f"Extracted {len(limited_text)} chars from PDF spec sheet.")
                    
                    user_contents.append(TextContent(text=f"\n[Attached PDF Datasheet Name: {file_name}]\n{limited_text}"))
                except Exception as ex:
                    logger.error(f"Failed to extract text from PDF: {ex}")
                    user_contents.append(TextContent(text=f"\n[Note: User attempted to upload PDF {file_name}, but data extraction failed.]"))

        # Add the compound user message to the history
        chat_history.add_user_message(user_contents)

        # Get Chat Service and Invoke
        chat_service = kernel.get_service("chat")
        
        # We must explicitly pass the kernel to allow auto tool-calling!
        result = await chat_service.get_chat_message_content(
            chat_history=chat_history,
            settings=execution_settings,
            kernel=kernel
        )
        
        return str(result)
        
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        import traceback
        traceback.print_exc()
        return "I apologize, but I encountered an internal error while trying to process your request."
