import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from app.services.agent_orchestrator import create_kernel, process_chat_message

async def run_test():
    print("Initializing client...")
    client = await create_kernel()
    if not client:
        print("Failed to init client")
        return
        
    print("Sending message...")
    try:
        result = await process_chat_message(client, "What are the latest FCC rules in 2026? Be concise.")
        
        print("\n--- RESULT ---")
        if result:
            print(f"TEXT: {result.text}")
            if result.metadata and 'usage' in result.metadata:
                print(f"TOKENS: {result.metadata['usage'].total_tokens}")
        else:
            print("Result was None")
        
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(run_test())
