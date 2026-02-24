from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File
import semantic_kernel as sk
from app.models.chat_schemas import ChatResponse
from app.services.agent_orchestrator import create_kernel, process_chat_message
from app.core.auth import get_current_user

router = APIRouter()

# Dependency to get the kernel instance
def get_kernel() -> sk.Kernel:
    return create_kernel()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    message: str = Form(...),
    file: UploadFile = File(None),
    kernel: sk.Kernel = Depends(get_kernel),
    user: dict = Depends(get_current_user)
):
    """
    Receives a chat message (and optional file) from the frontend and returns the AI's response.
    """
    # Simple check to ensure keys are loaded
    if not kernel.get_service("chat"):
        raise HTTPException(
            status_code=500, 
            detail="Azure OpenAI credentials not configured properly in .env."
        )

    try:
        # Read the file content if provided
        file_content = await file.read() if file else None
        file_name = file.filename if file else None
        file_content_type = file.content_type if file else None

        reply = await process_chat_message(kernel, message, file_content, file_name, file_content_type)
        return ChatResponse(
            reply=reply,
            sources=["Multimodal Swarm Response"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
