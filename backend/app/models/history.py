from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
import uuid

class SourceModel(BaseModel):
    id: str
    title: str
    type: str
    snippet: str
    relevance: int
    url: Optional[str] = None

class ChatMessageModel(BaseModel):
    id: str
    role: str
    content: str
    timestamp: str
    fileAttachment: Optional[str] = None
    sources: Optional[List[SourceModel]] = None
    confidence: Optional[str] = None

class ChatThreadModel(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # the user's sub claim
    title: str
    created_at: str
    updated_at: str
    messages: List[ChatMessageModel] = []
    
    # Required by CosmosDB typically
    partition_key: str = Field(default="")

    def __init__(self, **data):
        super().__init__(**data)
        if not self.partition_key:
            self.partition_key = self.user_id
