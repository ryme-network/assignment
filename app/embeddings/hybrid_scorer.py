from typing import Dict, Optional
from embeddings.direct_field_scorer import DirectFieldScorer


class HybridScorer:
    def __init__(
        self,
        audience_weights: Optional[Dict[str, float]] = None,
        overall_weights: Optional[Dict[str, float]] = None
    ):
        self.direct_field_scorer = DirectFieldScorer()
        
        # Weights for combining audience alignment components
        self.audience_weights = audience_weights or {
            "gender": 0.35,      # Gender matching importance
            "age": 0.35,         # Age matching importance
            "llm_audience": 0.30  # LLM semantic audience matching
        }
        
        # Weights for overall match score
        self.overall_weights = overall_weights or {
            "audience_alignment": 0.30,   # Most important - demographic fit
            "content_relevance": 0.30,    # Content niche alignment
            "value_alignment": 0.25,      # Brand values compatibility
            "engagement_quality": 0.15     # Engagement metrics
        }

    def calculate_engagement_quality_score(self, creator: Dict) -> float:
        engagement_rate = creator.get("engagement_rate", 0.0)
        content_quality = creator.get("content_quality_score", 0.0)
        followers = creator.get("followers", 1)  # Avoid division by zero
        avg_engagement = creator.get("avg_engagement_per_post", 0)
        
        # Normalize engagement rate (typical range: 0.01-0.10, with 0.05 being good)
        # Score: 0.0 for 0.01, 1.0 for 0.10+
        normalized_engagement_rate = min(1.0, max(0.0, (engagement_rate - 0.01) / 0.09))
        
        # Normalize avg engagement per post by followers (engagement rate proxy)
        # If avg_engagement is high relative to followers, that's good
        engagement_per_follower = avg_engagement / followers if followers > 0 else 0
        normalized_avg_engagement = min(1.0, max(0.0, engagement_per_follower * 10))  # Scale factor
        
        # Combine metrics (content quality is already 0-1)
        engagement_score = (
            0.40 * normalized_engagement_rate +
            0.35 * content_quality +
            0.25 * normalized_avg_engagement
        )
        
        return round(min(1.0, max(0.0, engagement_score)), 4)

    def calculate_audience_alignment(
        self,
        gender_score: float,
        age_score: float,
        llm_audience_score: float
    ) -> float:
        
        audience_alignment = (
            self.audience_weights["gender"] * gender_score +
            self.audience_weights["age"] * age_score +
            self.audience_weights["llm_audience"] * llm_audience_score
        )
        
        return round(min(1.0, max(0.0, audience_alignment)), 4)

    def calculate_comprehensive_scores(
        self,
        creator: Dict,
        brand: Dict,
        llm_scores: Dict[str, float],
        direct_field_scores: Dict[str, float]
    ) -> Dict[str, float]:
        
        # Extract scores
        gender_score = direct_field_scores.get("gender_score", 0.5)
        age_score = direct_field_scores.get("age_score", 0.5)
        llm_content = llm_scores.get("content_score", 0.5)
        llm_values = llm_scores.get("values_score", 0.5)
        llm_audience = llm_scores.get("audience_score", 0.5)
        
        # Calculate component scores
        audience_alignment = self.calculate_audience_alignment(
            gender_score, age_score, llm_audience
        )
        content_relevance = round(llm_content, 4)
        value_alignment = round(llm_values, 4)
        engagement_quality = self.calculate_engagement_quality_score(creator)
        
        # Calculate overall match score
        overall_match_score = (
            self.overall_weights["audience_alignment"] * audience_alignment +
            self.overall_weights["content_relevance"] * content_relevance +
            self.overall_weights["value_alignment"] * value_alignment +
            self.overall_weights["engagement_quality"] * engagement_quality
        )
        
        return {
            "audience_alignment": audience_alignment,
            "content_relevance": content_relevance,
            "value_alignment": value_alignment,
            "engagement_quality": engagement_quality,
            "overall_match_score": round(overall_match_score, 4),
            # Keep individual scores for reference
            "gender_score": gender_score,
            "age_score": age_score,
            "llm_content_score": llm_content,
            "llm_values_score": llm_values,
            "llm_audience_score": llm_audience
        }

