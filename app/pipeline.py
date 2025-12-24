from typing import List, Dict, Optional
from embeddings.data_transformer import DataTransformer
from embeddings.metadata_store import MetadataStore

class IngestionPipeline:
    """Orchestrates data ingestion into MongoDB only."""

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        mongodb_uri: Optional[str] = None,
        mongodb_db: Optional[str] = None
    ):
        self.transformer = DataTransformer(gemini_api_key=gemini_api_key)
        self.metadata_store = MetadataStore(
            connection_uri=mongodb_uri,
            database_name=mongodb_db
        )
        # ChromaDB store removed - not needed for new architecture
        # self.vector_store = ChromaVectorStore(...)

    def ingest_creators(self, creators: List[Dict]) -> Dict[str, int]:
        """
        Ingest creators into MongoDB only (metadata + derived fields).
        """
        # Transform creators (adds derived fields)
        transformed_creators = [
            self.transformer.transform_creator(creator)
            for creator in creators
        ]

        # Store in MongoDB
        mongo_count = self.metadata_store.insert_creators_batch(transformed_creators)

        return {
            "mongodb_creators": mongo_count,
            "chromadb_embeddings": 0  # Not used anymore
        }

    def ingest_brands(self, brands: List[Dict]) -> Dict[str, int]:
        """
        Ingest brands into MongoDB (metadata + derived fields).
        """
        # Transform brands (adds derived fields)
        transformed_brands = [
            self.transformer.transform_brand(brand)
            for brand in brands
        ]

        # Store in MongoDB
        mongo_count = self.metadata_store.insert_brands_batch(transformed_brands)

        return {
            "mongodb_brands": mongo_count
        }

    def refresh_data(
        self,
        creators: List[Dict],
        brands: List[Dict],
        clear_existing: bool = True
    ) -> Dict[str, int]:

        if clear_existing:
            print("Clearing existing data from MongoDB...")
            deleted = self.metadata_store.clear_all()
            print(f"  Deleted {deleted['creators_deleted']} creators and {deleted['brands_deleted']} brands")
        
        print("Re-ingesting creators...")
        creator_stats = self.ingest_creators(creators)
        
        print("Re-ingesting brands...")
        brand_stats = self.ingest_brands(brands)
        
        return {
            "mongodb_creators": creator_stats["mongodb_creators"],
            "mongodb_brands": brand_stats["mongodb_brands"]
        }

    def close(self):
        """Close all connections."""
        self.metadata_store.close()

