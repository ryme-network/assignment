import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.embeddings.inspect_store import (
    print_collection_info,
    print_sample_data,
    print_entity_summary,
    print_embedding_types,
    inspect_creator,
    inspect_brand
)
from app.embeddings.chroma_store import ChromaVectorStore


def main():
    collection_name = sys.argv[1] if len(sys.argv) > 1 else "creators"
    entity_type = "brand" if "brand" in collection_name.lower() else "creator"
    
    store = ChromaVectorStore(collection_name=collection_name)
    
    print("\n" + "="*80)
    print("ChromaDB Collection Inspector")
    print("="*80)
    
    # Check if collection has data
    count = store.get_count()
    if count == 0:
        print(f"\n⚠️  Collection '{collection_name}' is empty or doesn't exist.")
        print(f"   Run matcher.py first to populate the creators collection.")
        return
    
    # Basic info
    print_collection_info(store, entity_type)
    
    # Entity summary
    print_entity_summary(store, entity_type)
    
    # Embedding type breakdown
    print_embedding_types(store)
    
    # Sample data
    print_sample_data(store, limit=3)
    
    # If specific entity ID provided
    if len(sys.argv) > 2:
        entity_id = sys.argv[2]
        print(f"\n{'='*80}")
        print(f"Detailed view for {entity_type}: {entity_id}")
        print(f"{'='*80}")
        if entity_type == "creator":
            inspect_creator(store, entity_id)
        else:
            inspect_brand(store, entity_id)
    else:
        print(f"\n💡 Tip: To inspect a specific {entity_type}, run:")
        print(f"   python app/inspect_collections.py {collection_name} <{entity_type}_id>")


if __name__ == "__main__":
    main()

