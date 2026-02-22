from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Compliance.chat API", version="1.0.0")

# Allow frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Semantic Kernel
kernel = sk.Kernel()

# We need the deployment name, endpoint, and key from the .env
deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4o-mini")
api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")

# Only add the AI service if keys are present (prevents crash on startup without keys)
if api_key and endpoint:
    kernel.add_service(
        sk.services.AzureChatCompletion(
            service_id="chat",
            deployment_name=deployment,
            endpoint=endpoint,
            api_key=api_key,
        )
    )

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    sources: list[str] = []

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "compliance.chat AI backend"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not api_key or not endpoint:
        raise HTTPException(status_code=500, detail="Azure OpenAI credentials not configured.")
        
    try:
        # Phase 1: Direct pass-through to LLM (No RAG yet)
        # We will add Vector DB Retrieval here later!
        
        prompt = f"""
        You are the Compliance.chat expert AI agent. 
        You specialize in product compliance, importation laws, FCC, CE, ANATEL, etc.
        Answer the user's question accurately. If you don't know, say you don't know.
        
        User: {request.message}
        """
        
        # Invoke Semantic Kernel
        result = await kernel.invoke_prompt(prompt)
        
        return ChatResponse(
            reply=str(result),
            sources=["Direct LLM Knowledge (RAG Integration Pending)"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
