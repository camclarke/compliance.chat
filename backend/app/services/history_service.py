import os
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from app.core.config import settings
from app.models.history import ChatThreadModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class HistoryService:
    def __init__(self):
        self.endpoint = settings.AZURE_COSMOS_ENDPOINT
        self.key = settings.AZURE_COSMOS_KEY
        self.database_name = settings.AZURE_COSMOS_DATABASE
        self.container_name = settings.AZURE_COSMOS_CONTAINER
        self.client = None
        self.database = None
        self.container = None
        
        # Initialize only if credentials exist (fail gracefully otherwise for local testing)
        if self.endpoint and self.key:
            try:
                self.client = CosmosClient(self.endpoint, credential=self.key)
                self.database = self.client.create_database_if_not_exists(id=self.database_name)
                self.container = self.database.create_container_if_not_exists(
                    id=self.container_name, 
                    partition_key=PartitionKey(path="/partition_key"),
                    offer_throughput=400
                )
            except Exception as e:
                logger.error(f"Failed to initialize Azure Cosmos DB: {e}")

    def is_configured(self) -> bool:
        return self.container is not None

    def get_user_threads(self, user_id: str) -> List[dict]:
        """Fetch all threads for a specific user."""
        if not self.is_configured():
            return []
            
        query = "SELECT c.id, c.title, c.created_at, c.updated_at FROM c WHERE c.partition_key = @user_id ORDER BY c.updated_at DESC"
        parameters = [{"name": "@user_id", "value": user_id}]
        
        items = list(self.container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=False
        ))
        return items

    def get_thread(self, thread_id: str, user_id: str) -> Optional[ChatThreadModel]:
        """Fetch a specific thread with its full message history."""
        if not self.is_configured():
            return None
            
        try:
            item = self.container.read_item(item=thread_id, partition_key=user_id)
            return ChatThreadModel(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None

    def save_thread(self, thread: ChatThreadModel) -> ChatThreadModel:
        """Upsert a thread to Cosmos DB."""
        if not self.is_configured():
            return thread
            
        self.container.upsert_item(thread.model_dump())
        return thread

history_service = HistoryService()
