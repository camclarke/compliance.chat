import sys
import os
sys.path.append(os.path.abspath("."))
from app.services.history_service import history_service

thread_id = "28c64fe3-3be3-4118-8b3c-d02a25ccc469"
user_id = "gFoUFrG-0o3eviGk_ndG9UaNmIosDWApscquiHupKds"

thread = history_service.get_thread(thread_id, user_id)
print(f"Result: {thread}")
