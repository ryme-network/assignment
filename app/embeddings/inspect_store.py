import json
from embeddings.chroma_store import ChromaVectorStore


def print_collection_info(store: ChromaVectorStore, collection_type: str = "creators"):
    info = store.get_collection_info()
    print(f"\n{'='*80}")
    print(f"Collection: {info['name']}")
    print(f"Total embeddings: {info['count']}")
    print(f"Type: {collection_type}")
    print(f"{'='*80}\n")


def print_sample_data(store: ChromaVectorStore, limit: int = 5, embedding_type: str = None):
    where_clause = {"embedding_type": embedding_type} if embedding_type else None
    data = store.peek(limit=limit, where=where_clause)
    
    print(f"\nSample data (showing {data['count']} of {store.get_count()} total):")
    print("-" * 80)
    
    for i, (id_val, metadata, document) in enumerate(zip(
        data.get("ids", []),
        data.get("metadatas", []),
        data.get("documents", [])
    )):
        print(f"\n[{i+1}] ID: {id_val}")
        print(f"    Metadata: {json.dumps(metadata, indent=6)}")
        print(f"    Document: {document[:150]}..." if len(document) > 150 else f"    Document: {document}")
        print()


def print_entity_summary(store: ChromaVectorStore, entity_type: str = "creator"):
    entity_ids = store.list_all_entity_ids(entity_type=entity_type)
    
    print(f"\n{'='*80}")
    print(f"{entity_type.title()} Summary")
    print(f"{'='*80}")
    print(f"Total unique {entity_type}s: {len(entity_ids)}")
    print(f"IDs: {', '.join(entity_ids[:20])}" + ("..." if len(entity_ids) > 20 else ""))
    print()
    
    # Count embeddings per entity type
    for embedding_type in ["content", "values", "audience"]:
        where_clause = {"embedding_type": f"{entity_type}_{embedding_type}"}
        count = len(store.peek(limit=1000, where=where_clause).get("ids", []))
        print(f"  - {embedding_type.title()}: {count} embeddings")


def print_embedding_types(store: ChromaVectorStore):
    print(f"\n{'='*80}")
    print("Embedding Type Breakdown")
    print(f"{'='*80}")
    
    embedding_types = [
        "creator_content",
        "creator_values", 
        "creator_audience",
        "brand_content",
        "brand_values",
        "brand_audience"
    ]
    
    for etype in embedding_types:
        where_clause = {"embedding_type": etype}
        data = store.peek(limit=1000, where=where_clause)
        count = data.get("count", 0)
        if count > 0:
            print(f"  {etype}: {count} embeddings")


def inspect_creator(store: ChromaVectorStore, creator_id: str):
    print(f"\n{'='*80}")
    print(f"Inspecting Creator: {creator_id}")
    print(f"{'='*80}\n")
    
    for embedding_type in ["creator_content", "creator_values", "creator_audience"]:
        where_clause = {
            "embedding_type": embedding_type,
            "creator_id": creator_id
        }
        data = store.peek(limit=1, where=where_clause)
        
        if data.get("count", 0) > 0:
            print(f"Type: {embedding_type}")
            print(f"Document: {data['documents'][0]}")
            print(f"Metadata: {json.dumps(data['metadatas'][0], indent=2)}")
            print()


def inspect_brand(store: ChromaVectorStore, brand_id: str):
    print(f"\n{'='*80}")
    print(f"Inspecting Brand: {brand_id}")
    print(f"{'='*80}\n")
    
    for embedding_type in ["brand_content", "brand_values", "brand_audience"]:
        where_clause = {
            "embedding_type": embedding_type,
            "brand_id": brand_id
        }
        data = store.peek(limit=1, where=where_clause)
        
        if data.get("count", 0) > 0:
            print(f"Type: {embedding_type}")
            print(f"Document: {data['documents'][0]}")
            print(f"Metadata: {json.dumps(data['metadatas'][0], indent=2)}")
            print()


def main():
    import sys
    
    # Default to creators collection
    collection_name = sys.argv[1] if len(sys.argv) > 1 else "creators"
    entity_type = "brand" if "brand" in collection_name.lower() else "creator"
    
    store = ChromaVectorStore(collection_name=collection_name)
    
    print("\n" + "="*80)
    print("ChromaDB Collection Inspector")
    print("="*80)
    
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
        if entity_type == "creator":
            inspect_creator(store, entity_id)
        else:
            inspect_brand(store, entity_id)


if __name__ == "__main__":
    main()

