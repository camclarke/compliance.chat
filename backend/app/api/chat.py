from fastapi import APIRouter, HTTPException, Depends
import semantic_kernel as sk
from app.models.chat_schemas import ChatRequest, ChatResponse
from app.services.agent_orchestrator import create_kernel, process_chat_message

router = APIRouter()

# Dependency to get the kernel instance
def get_kernel() -> sk.Kernel:
    return create_kernel()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, kernel: sk.Kernel = Depends(get_kernel)):
    """
    Receives a chat message from the frontend and returns the AI's response.
    """
    # Simple check to ensure keys are loaded
    if not kernel.get_service("chat"):
        raise HTTPException(
            status_code=500, 
            detail="Azure OpenAI credentials not configured properly in .env."
        )

    try:
        reply = await process_chat_message(kernel, request.message)
        return ChatResponse(
            reply=reply,
            sources=["Azure AI Model Router Placeholder"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
