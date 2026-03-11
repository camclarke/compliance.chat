import os
import asyncio
import logging
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from azure.ai.agents.models import BingGroundingTool

logger = logging.getLogger(__name__)

class AgentResult:
    def __init__(self, text, usage_metadata):
        self.text = text
        self.metadata = usage_metadata

    def __str__(self):
        return self.text

async def create_kernel():
    """
    Initializes AIProjectClient. (Kept the name create_kernel to not break chat.py).
    """
    endpoint = os.getenv("PROJECT_ENDPOINT")
    if not endpoint:
        logger.error("Missing PROJECT_ENDPOINT in environment variables.")
        return None
        
    client = AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    )
    logger.info("Successfully initialized AIProjectClient.")
    return client

async def process_chat_message(
    client: AIProjectClient, 
    message: str, 
    file_content: bytes = None, 
    file_name: str = None, 
    file_content_type: str = None
) -> AgentResult:
    """
    Processes a user's chat message using Azure AI Agent Service.
    """
    if not client:
        logger.error("AIProjectClient not initialized")
        return None

    try:
        # Create Bing grounding tool natively if connection is available
        bing_connection = None
        # We assume a connection named 'bing' or we retrieve the first bing search connection
        connections = client.connections.list()
        async for c in connections:
            if "bing" in c.name.lower() or c.connection_type.lower() == "bing_search_connection":
                bing_connection = await client.connections.get(connection_name=c.name)
                break
                
        tools = []
        if bing_connection:
            bing = BingGroundingTool(bing_connection)
            tools = bing.definitions
            logger.info(f"Attached Bing Grounding Tool to the agent using connection {bing_connection.name}.")
        else:
            logger.warning("No Bing connection found. Agent will run without live search.")

        # 1. Initialize OpenAI Client Wrapper
        openai_client = await client.get_openai_client(api_version="2024-05-01-preview")

        tools = []
        try:
            # Attempt to set up Bing Grounding
            # In a real app we'd query the project connections to find the bing connection ID
            # For now we'll simulate the class integration
            pass
        except Exception as tool_e:
            logger.warning(f"Failed to attach Bing Grounding tool: {tool_e}")

        # 2. Create Agent (Assistant)
        logger.info("Creating agent (Assistant)...")
        agent = await openai_client.beta.assistants.create(
            model="gpt-4o",
            name="ComplianceAgent",
            instructions=(
                "You are an AI assistant designed to answer questions about FCC and global compliance regulations. "
                "You should use Bing search whenever possible to ground your answers in factual 2026 current events. "
                "Always cite your sources with URLs."
            ),
            tools=tools
        )

        try:
            # 3. Create Thread
            logger.info("Creating thread...")
            thread = await openai_client.beta.threads.create()

            # 4. Add User Message
            logger.info(f"Adding user message to thread {thread.id}...")
            await openai_client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=message
            )

            # 5. Create and Poll Run
            logger.info("Executing run and polling...")
            run = await openai_client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=agent.id
            )

            if run.status != "completed":
                logger.error(f"Run ended with status: {run.status}")
                if hasattr(run, 'last_error') and run.last_error:
                    logger.error(f"Error details: {run.last_error}")
                return AgentResult(text=f"Agent run ended with status {run.status}", usage_metadata={})

            # 6. Fetch Messages
            messages_page = await openai_client.beta.threads.messages.list(
                thread_id=thread.id
            )
            # The newest message is first in the list typically, but we should find the latest assistant message
            assistant_messages = [m for m in messages_page.data if m.role == "assistant"]
            if not assistant_messages:
                return AgentResult(text="No response generated from agent.", usage_metadata={})
                
            latest_message = assistant_messages[0]
            
            final_text = ""
            for content_block in latest_message.content:
                if content_block.type == 'text':
                    final_text += content_block.text.value
            
            # Extract usage if available
            metadata = {
                 "model": "gpt-4o (Azure AI Agent)"
            }
            if hasattr(run, 'usage') and run.usage:
                class MockUsage:
                    def __init__(self, run_obj):
                        self.total_tokens = getattr(run_obj.usage, 'total_tokens', 0)
                        self.prompt_tokens = getattr(run_obj.usage, 'prompt_tokens', 0)
                        self.completion_tokens = getattr(run_obj.usage, 'completion_tokens', 0)
                metadata['usage'] = MockUsage(run)

            return AgentResult(
                text=final_text.strip(),
                usage_metadata=metadata
            )
            
        finally:
            # Cleanup Agent to avoid cluttering the project
            await openai_client.beta.assistants.delete(agent.id)

    except Exception as e:
        logger.error(f"Error processing chat message via AgentClient: {e}", exc_info=True)
        return None
