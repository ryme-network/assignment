from typing import Dict, List, Optional
import numpy as np


class MultiScoreRanker:
    def __init__(
        self,
        store,
        embedder,
        weights: Optional[Dict[str, float]] = None,
    ):
        self.store = store
        self.embedder = embedder
        self.weights = weights or {
            "content": 0.45,
            "values": 0.35,
            "audience": 0.20,
        }

    def _query(
        self,
        query_text: str,
        embedding_type: str,
        top_k: int = 20,
    ):
        embedding = self.embedder.encode([query_text])[0]

        results = self.store.query(
            embedding,
            n_results=top_k,
            where={"embedding_type": embedding_type},
        )

        scores = {}
        for i, meta in enumerate(results["metadatas"][0]):
            creator_id = meta["creator_id"]
            similarity = 1 - results["distances"][0][i]
            scores[creator_id] = similarity

        return scores

    def rank_creators(
        self,
        brand_texts: Dict[str, str],
        top_k: int = 10,
    ) -> List[Dict]:
        """
        brand_texts = {
            "content": "...",
            "values": "...",
            "audience": "..."
        }
        """

        content_scores = self._query(
            brand_texts["content"], "creator_content"
        )
        values_scores = self._query(
            brand_texts["values"], "creator_values"
        )
        audience_scores = self._query(
            brand_texts["audience"], "creator_audience"
        )

        all_creator_ids = (
            set(content_scores)
            | set(values_scores)
            | set(audience_scores)
        )

        ranked = []
        for cid in all_creator_ids:
            final_score = (
                self.weights["content"] * content_scores.get(cid, 0.0)
                + self.weights["values"] * values_scores.get(cid, 0.0)
                + self.weights["audience"] * audience_scores.get(cid, 0.0)
            )

            ranked.append({
                "creator_id": cid,
                "final_score": round(final_score, 4),
                "content_score": round(content_scores.get(cid, 0.0), 4),
                "values_score": round(values_scores.get(cid, 0.0), 4),
                "audience_score": round(audience_scores.get(cid, 0.0), 4),
            })

        ranked.sort(key=lambda x: x["final_score"], reverse=True)
        return ranked[:top_k]

    @staticmethod
    def is_cold_start_creator(creator: dict) -> bool:
        return (
            creator.get("avg_engagement_per_post", 0) == 0
            or not creator.get("past_brand_collaborations")
        )

    @staticmethod
    def is_cold_start_brand(brand: dict) -> bool:
        return not brand.get("past_successful_partnerships")
