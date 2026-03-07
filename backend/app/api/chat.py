from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File
from fastapi.responses import JSONResponse
import semantic_kernel as sk
from app.models.chat_schemas import ChatResponse
from app.services.agent_orchestrator import create_kernel, process_chat_message
from app.core.auth import get_current_user
from app.core.usage import usage_tracker

router = APIRouter()

# Dependency to get the kernel instance
def get_kernel() -> sk.Kernel:
    return create_kernel()

@router.post("/chat")
async def chat_endpoint(
    message: str = Form(...),
    file: UploadFile = File(None),
    kernel: sk.Kernel = Depends(get_kernel),
    user: dict = Depends(get_current_user)
):
    """
    Receives a chat message (and optional file) from the frontend and returns the AI's response.
    Enforces token-based daily quotas per user.
    """
    user_sub = user.get("sub", "")
    user_name = user.get("name", "")
    user_email = user.get("email", "")

    # Ensure user exists in usage tracker
    usage_tracker.ensure_user(user_sub, name=user_name, email=user_email)

    # ── Pre-flight quota check ────────────────────────────────
    allowed, remaining, tier, daily_limit = usage_tracker.check_budget(user_sub)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "quota_exceeded",
                "tier": tier,
                "daily_limit": daily_limit,
                "tokens_used": daily_limit,  # They've used it all
            },
            headers={
                "X-Tokens-Remaining": "0",
                "X-Tokens-Limit": str(daily_limit) if daily_limit else "unlimited",
                "X-Tokens-Tier": tier,
            },
        )

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

        result = await process_chat_message(kernel, message, file_content, file_name, file_content_type)

        # ── Record actual token usage ─────────────────────────
        tokens_consumed = 0
        if hasattr(result, 'metadata') and result.metadata:
            usage_meta = result.metadata.get("usage")
            if usage_meta:
                tokens_consumed = getattr(usage_meta, "total_tokens", 0)
                if not tokens_consumed:
                    prompt_tokens = getattr(usage_meta, "prompt_tokens", 0)
                    completion_tokens = getattr(usage_meta, "completion_tokens", 0)
                    tokens_consumed = prompt_tokens + completion_tokens

        # Fallback estimate if metadata unavailable
        if tokens_consumed == 0:
            tokens_consumed = max(100, len(message) // 2 + len(str(result)) // 2)

        new_remaining = usage_tracker.record_usage(user_sub, tokens_consumed)

        reply_text = str(result)

        response = JSONResponse(
            content={
                "reply": reply_text,
                "sources": ["Multimodal Swarm Response"],
            },
            headers={
                "X-Tokens-Remaining": str(new_remaining),
                "X-Tokens-Limit": str(daily_limit) if daily_limit else "unlimited",
                "X-Tokens-Tier": tier,
                "X-Tokens-Used": str(tokens_consumed),
            },
        )
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")
