import os
import sys

sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.services.history_service import history_service

def drop_container():
    if not history_service.is_configured():
        print("Cosmos DB is not configured.")
        return

    try:
        history_service.database.delete_container(history_service.container_name)
        print(f"Successfully deleted container {history_service.container_name}. It will be recreated on next app startup.")
    except Exception as e:
        print(f"Failed to delete container: {e}")

if __name__ == "__main__":
    drop_container()
