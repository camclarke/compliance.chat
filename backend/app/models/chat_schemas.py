from pydantic import BaseModel
from typing import List

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    sources: List[str] = []
