import os
import asyncio
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

load_dotenv()

async def test_conn():
    connection_string = os.getenv("PROJECT_CONNECTION_STRING")
    async with AIProjectClient(
        endpoint="https://israe-mlz80ufc-eastus2.services.ai.azure.com/api/projects/israe-mlz80ufc-eastus2_project",
        credential=DefaultAzureCredential()
    ) as client:
        # Get connections to see if Bing is available
        connections_iter = client.connections.list()
        connections = []
        async for c in connections_iter:
            connections.append(c)
        print(f"Connections found: {len(connections)}")
        for c in connections:
            print(f"- {c.name} ({c.connection_type})")

asyncio.run(test_conn())
