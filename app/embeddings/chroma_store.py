import numpy as np
from typing import Dict, List, Optional
import chromadb
from chromadb.config import Settings


class ChromaVectorStore:

    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "creators"):
        # Create a persistent client that stores data on disk
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"} 
        )
        
    def add(
        self,
        embeddings: np.ndarray,
        metadatas: List[Dict],
        documents: List[str],
    ):
        if len(embeddings) == 0:
            return
        
        # Convert numpy array to list of lists
        embeddings_list = embeddings.tolist()
        
        ids = []
        for i, meta in enumerate(metadatas):
            embedding_type = meta.get('embedding_type', 'unknown')
            # Support both creator_id and brand_id
            entity_id = meta.get('creator_id') or meta.get('brand_id') or f'unknown_{i}'
            ids.append(f"{embedding_type}_{entity_id}")
        
        # Add to ChromaDB
        self.collection.add(
            embeddings=embeddings_list,
            metadatas=metadatas,
            documents=documents,
            ids=ids
        )
    
    def query(
        self,
        embedding: np.ndarray,
        n_results: int = 5,
        where: Optional[Dict] = None,
    ) -> Dict:
        if embedding.ndim == 1:
            query_embeddings = [embedding.tolist()]
        else:
            query_embeddings = embedding.tolist()
        
        # Convert where clause to ChromaDB format if provided
        where_clause = None
        if where:
            where_clause = {}
            for key, value in where.items():
                where_clause[key] = value
        
        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=n_results,
            where=where_clause,
        )
        
        return {
            "metadatas": results.get("metadatas", [[]]),
            "distances": results.get("distances", [[]]),
        }
    
    def reset(self):
        try:
            self.client.delete_collection(name=self.collection.name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection.name,
                metadata={"hnsw:space": "cosine"}
            )
        except Exception as e:
            # Collection might not exist, that's fine
            pass
    
    def get_count(self) -> int:
        return self.collection.count()
    
    def peek(self, limit: int = 10, where: Optional[Dict] = None) -> Dict:
        where_clause = None
        if where:
            where_clause = {}
            for key, value in where.items():
                where_clause[key] = value
        
        results = self.collection.get(
            limit=limit,
            where=where_clause,
            include=["metadatas", "documents", "embeddings"]
        )
        
        return {
            "ids": results.get("ids", []),
            "metadatas": results.get("metadatas", []),
            "documents": results.get("documents", []),
            "count": len(results.get("ids", []))
        }
    
    def get_by_id(self, ids: List[str]) -> Dict:
        results = self.collection.get(
            ids=ids,
            include=["metadatas", "documents"]
        )
        
        return {
            "ids": results.get("ids", []),
            "metadatas": results.get("metadatas", []),
            "documents": results.get("documents", [])
        }
    
    def get_collection_info(self) -> Dict:
        return {
            "name": self.collection.name,
            "count": self.collection.count(),
            "metadata": self.collection.metadata
        }
    
    def list_all_entity_ids(self, entity_type: str = "creator") -> List[str]:
        entity_id_key = f"{entity_type}_id"
        all_data = self.collection.get(include=["metadatas"])
        
        entity_ids = set()
        for metadata in all_data.get("metadatas", []):
            if entity_id_key in metadata:
                entity_ids.add(metadata[entity_id_key])
        
        return sorted(list(entity_ids))

