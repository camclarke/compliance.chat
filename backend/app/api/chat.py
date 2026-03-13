from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File, Request
from fastapi.responses import JSONResponse
from app.services.agent_orchestrator import process_chat_message
from app.core.auth import get_current_user
from datetime import datetime, timezone
import uuid
from app.models.history import ChatThreadModel, ChatMessageModel
from app.services.history_service import history_service
from app.core.usage import usage_tracker

router = APIRouter()

# Dependency: return the shared AIProjectClient initialised at app startup.
async def get_kernel(request: Request):
    return getattr(request.app.state, "ai_client", None)

@router.get("/history")
async def get_history(user: dict = Depends(get_current_user)):
    """Fetch all chat threads for the logged in user."""
    user_sub = user.get("sub", "")
    threads = history_service.get_user_threads(user_sub)
    return {"threads": threads}

@router.get("/history/{thread_id}")
async def get_thread_history(thread_id: str, user: dict = Depends(get_current_user)):
    """Fetch specific chat thread history."""
    user_sub = user.get("sub", "")
    thread = history_service.get_thread(thread_id, user_sub)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread.model_dump()

@router.post("/chat")
async def chat_endpoint(
    message: str = Form(...),
    thread_id: str = Form(None),
    file: UploadFile = File(None),
    client = Depends(get_kernel),
    user: dict = Depends(get_current_user)
):
    """
    Receives a chat message (and optional file) from the frontend and returns the AI's response.
    Enforces token-based daily quotas per user and saves to Cosmos DB history.
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

    if not client:
        raise HTTPException(
            status_code=500, 
            detail="Azure AI Project Connection String not configured properly in .env."
        )

    try:
        # Read the file content if provided
        file_content = await file.read() if file else None
        file_name = file.filename if file else None
        file_content_type = file.content_type if file else None

        # Try to load existing thread
        thread = None
        if thread_id:
            thread = history_service.get_thread(thread_id, user_sub)
            
        if not thread:
            # Create a new thread
            safe_message = str(message)
            thread_title = safe_message[:30] + "..." if len(safe_message) > 30 else safe_message
            thread = ChatThreadModel(
                user_id=user_sub,
                title=thread_title,
                created_at=datetime.now(timezone.utc).isoformat(),
                updated_at=datetime.now(timezone.utc).isoformat(),
                messages=[]
            )

        # Build user message model
        user_msg = ChatMessageModel(
            id=str(uuid.uuid4()),
            role="user",
            content=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            fileAttachment=file_name
        )
        thread.messages.append(user_msg)

        # Build conversation history from prior thread messages (exclude the message just appended)
        history = [
            {"role": m.role, "content": m.content}
            for m in thread.messages[:-1]
            if m.role in ("user", "assistant")
        ]

        result = await process_chat_message(
            client, message, file_content, file_name, file_content_type, history=history
        )
        if not result:
             raise Exception("Empty response from AI")

        # ── Record actual token usage ─────────────────────────
        tokens_consumed = 0
        model_name = "gpt-4o" # default fallback
        
        if hasattr(result, 'metadata') and result.metadata:
            usage_meta = result.metadata.get("usage")
            model_name = result.metadata.get("model", "gpt-4o")
            if usage_meta:
                tokens_consumed = getattr(usage_meta, "total_tokens", 0)
                if not tokens_consumed:
                    prompt_tokens = getattr(usage_meta, "prompt_tokens", 0)
                    completion_tokens = getattr(usage_meta, "completion_tokens", 0)
                    tokens_consumed = prompt_tokens + completion_tokens

        # Fallback estimate if metadata unavailable
        reply_text = str(result)
        if tokens_consumed == 0:
            tokens_consumed = max(100, len(message) // 2 + len(reply_text) // 2)

        new_remaining = usage_tracker.record_usage(user_sub, tokens_consumed)

        # Build assistant message model
        ai_msg = ChatMessageModel(
            id=str(uuid.uuid4()),
            role="assistant",
            content=reply_text,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        thread.messages.append(ai_msg)
        thread.updated_at = datetime.now(timezone.utc).isoformat()
        
        # Save to Cosmos DB
        saved_thread = history_service.save_thread(thread)

        sources = getattr(result, "sources", []) or []

        response = JSONResponse(
            content={
                "reply": reply_text,
                "sources": sources,
                "thread_id": saved_thread.id,
                "model": model_name
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
