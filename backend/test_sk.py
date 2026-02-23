import asyncio
from app.services.agent_orchestrator import create_kernel, process_chat_message
import sys

async def main():
    kernel = create_kernel()
    try:
        reply = await process_chat_message(kernel, "What does FCC stand for?")
        print("REPLY:", reply)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
