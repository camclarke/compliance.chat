import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__))))

from app.services.history_service import history_service

def wipe_history():
    if not history_service.is_configured():
        print("Cosmos DB is not configured.")
        return

    container = history_service.container
    query = "SELECT * FROM c"
    items = list(container.query_items(query=query, enable_cross_partition_query=True))
    
    print(f"Found {len(items)} items to delete.")
    
    deleted_count = 0
    for item in items:
        # Check all possible partition key fields
        pkey = item.get('partition_key')
        if not pkey:
            pkey = item.get('user_id')
        
        print(f"Attempting to delete {item['id']} with partition key '{pkey}'")
        try:
            container.delete_item(item=item['id'], partition_key=pkey)
            deleted_count += 1
            print(f" -> Success")
        except Exception as e:
            print(f" -> Failed: {e}")
            
    print(f"Successfully deleted {deleted_count} records.")

if __name__ == "__main__":
    wipe_history()
