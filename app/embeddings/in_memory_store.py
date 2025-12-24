import numpy as np
from typing import Dict, List, Optional, Set


class InMemoryVectorStore:              #TODO: Set up a proper Vector DB

    def __init__(self):
        self.embeddings = None          # np.ndarray (N, D)
        self.metadatas: List[Dict] = []
        self.documents: List[str] = []

        # inverted index: field -> value -> set(indices)
        self.metadata_index: Dict[str, Dict[str, Set[int]]] = {}

    def _index_metadata(self, meta: Dict, idx: int):
        for key, value in meta.items():
            self.metadata_index.setdefault(key, {})
            self.metadata_index[key].setdefault(str(value), set())
            self.metadata_index[key][str(value)].add(idx)

    def add(
        self,
        embeddings: np.ndarray,
        metadatas: List[Dict],
        documents: List[str],
    ):
        start_idx = 0 if self.embeddings is None else len(self.metadatas)

        if self.embeddings is None:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])

        self.documents.extend(documents)

        for i, meta in enumerate(metadatas):
            idx = start_idx + i
            self.metadatas.append(meta)
            self._index_metadata(meta, idx)

    def _filter_indices(self, where: Dict) -> List[int]:
        sets = []
        for key, value in where.items():
            value = str(value)
            if (
                key not in self.metadata_index
                or value not in self.metadata_index[key]
            ):
                return []
            sets.append(self.metadata_index[key][value])

        return list(set.intersection(*sets)) if sets else list(
            range(len(self.metadatas))
        )

    def query(
        self,
        embedding: np.ndarray,
        n_results: int = 5,
        where: Optional[Dict] = None,
    ):
        if self.embeddings is None:
            return {"metadatas": [[]], "distances": [[]]}

        indices = (
            self._filter_indices(where)
            if where else list(range(len(self.metadatas)))
        )

        if not indices:
            return {"metadatas": [[]], "distances": [[]]}

        vectors = self.embeddings[indices]

        # cosine similarity
        q = embedding / np.linalg.norm(embedding)
        v = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)

        sims = np.dot(v, q)
        distances = 1.0 - sims

        top = np.argsort(distances)[:n_results]
        result_indices = [indices[i] for i in top]

        return {
            "metadatas": [[self.metadatas[i] for i in result_indices]],
            "distances": [[distances[i] for i in top]],
        }
