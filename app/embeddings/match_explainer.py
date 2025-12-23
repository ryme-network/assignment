from typing import Dict, List
from datetime import datetime


class MatchExplainer:
    def __init__(self):
        pass

    def generate_strengths(
        self,
        creator: Dict,
        brand: Dict,
        scores: Dict[str, float]
    ) -> List[str]:
        strengths = []
        
        # Audience alignment strengths
        if scores.get("audience_alignment", 0) > 0.80:
            strengths.append("Excellent audience demographic alignment")
        elif scores.get("audience_alignment", 0) > 0.70:
            strengths.append("Strong audience demographic match")
        
        if scores.get("gender_score", 0) > 0.75:
            creator_gender = creator.get("audience_demographics", {}).get("gender", {})
            female_pct = creator_gender.get("female", 0) * 100
            strengths.append(f"Gender alignment: {female_pct:.0f}% female audience matches brand target")
        
        if scores.get("age_score", 0) > 0.75:
            strengths.append("Age range alignment: Creator's audience matches brand's target age group")
        
        # Content relevance strengths
        if scores.get("content_relevance", 0) > 0.80:
            primary_niche = creator.get("primary_niche", "")
            strengths.append(f"Perfect niche match: {primary_niche} aligns with brand needs")
        elif scores.get("content_relevance", 0) > 0.70:
            content_categories = creator.get("content_categories", [])
            if content_categories:
                strengths.append(f"Strong content alignment in {', '.join(content_categories[:2])}")
        
        # Value alignment strengths
        if scores.get("value_alignment", 0) > 0.80:
            strengths.append("Strong brand values alignment")
        elif scores.get("value_alignment", 0) > 0.70:
            past_collabs = creator.get("past_brand_collaborations", [])
            if past_collabs:
                strengths.append(f"Relevant past collaborations with similar brands")
        
        # Engagement strengths
        if scores.get("engagement_quality", 0) > 0.75:
            engagement_rate = creator.get("engagement_rate", 0) * 100
            strengths.append(f"High engagement rate: {engagement_rate:.1f}% indicates active community")
        
        content_quality = creator.get("content_quality_score", 0)
        if content_quality > 0.85:
            strengths.append("High content quality score indicates professional production")
        
        # Location strengths
        creator_locations = creator.get("audience_demographics", {}).get("top_locations", [])
        brand_locations = brand.get("target_audience", {}).get("locations", [])
        if creator_locations and brand_locations:
            overlap = set(loc.lower() for loc in creator_locations) & set(
                loc.lower() for loc in brand_locations
            )
            if overlap:
                strengths.append(f"Geographic overlap in {', '.join(list(overlap)[:2])}")
        
        return strengths if strengths else ["Good overall match with multiple alignment factors"]

    def generate_concerns(
        self,
        creator: Dict,
        brand: Dict,
        scores: Dict[str, float]
    ) -> List[str]:
        concerns = []
        
        # Audience concerns
        if scores.get("audience_alignment", 0) < 0.60:
            concerns.append("Limited audience demographic alignment - may not reach target market effectively")
        
        if scores.get("gender_score", 0) < 0.60:
            concerns.append("Gender distribution may not match brand's target audience")
        
        if scores.get("age_score", 0) < 0.60:
            concerns.append("Age range mismatch - creator's audience may be outside brand's target")
        
        # Content concerns
        if scores.get("content_relevance", 0) < 0.65:
            concerns.append("Content niche may not fully align with brand messaging needs")
        
        # Value concerns
        if scores.get("value_alignment", 0) < 0.65:
            concerns.append("Potential values misalignment - review past collaborations carefully")
        
        # Engagement concerns
        if scores.get("engagement_quality", 0) < 0.60:
            engagement_rate = creator.get("engagement_rate", 0) * 100
            if engagement_rate < 3.0:
                concerns.append(f"Low engagement rate ({engagement_rate:.1f}%) may indicate inactive audience")
        
        # Follower count concerns
        followers = creator.get("followers", 0)
        brand_min = brand.get("follower_range_min", 0)
        brand_max = brand.get("follower_range_max", 1000000)
        
        if followers < brand_min:
            concerns.append(f"Follower count ({followers:,}) below brand's preferred range")
        elif followers > brand_max * 1.5:
            concerns.append(f"Follower count ({followers:,}) significantly above brand's preferred range")
        
        # Content quality concerns
        content_quality = creator.get("content_quality_score", 0)
        if content_quality < 0.70:
            concerns.append("Content quality score below ideal - review content standards")
        
        return concerns if concerns else []

    def generate_campaign_fit(
        self,
        creator: Dict,
        brand: Dict,
        scores: Dict[str, float]
    ) -> str:
        overall_score = scores.get("overall_match_score", 0)
        
        if overall_score >= 0.85:
            campaign_type = brand.get("campaign_goals", {}).get("campaign_type", "marketing campaign")
            return f"Ideal for {campaign_type} - strong alignment across all dimensions"
        elif overall_score >= 0.75:
            primary_niche = creator.get("primary_niche", "")
            return f"Strong fit for brand campaign - excellent {primary_niche} alignment"
        elif overall_score >= 0.65:
            return "Good fit with some considerations - review specific alignment areas"
        else:
            return "Moderate fit - may require additional vetting and alignment discussions"

    def generate_reasoning(
        self,
        creator: Dict,
        brand: Dict,
        scores: Dict[str, float],
        llm_reasoning: str = ""
    ) -> str:
        reasoning_parts = []
        
        # Overall assessment
        overall_score = scores.get("overall_match_score", 0)
        if overall_score >= 0.80:
            reasoning_parts.append("This creator demonstrates strong alignment with the brand across multiple dimensions.")
        elif overall_score >= 0.70:
            reasoning_parts.append("This creator shows good alignment with the brand's requirements.")
        else:
            reasoning_parts.append("This creator has moderate alignment with some areas requiring attention.")
        
        # Key alignment points
        if scores.get("content_relevance", 0) > 0.75:
            primary_niche = creator.get("primary_niche", "")
            reasoning_parts.append(f"The creator's focus on {primary_niche} aligns well with the brand's needs.")
        
        if scores.get("audience_alignment", 0) > 0.75:
            reasoning_parts.append("The creator's audience demographics closely match the brand's target market.")
        
        if scores.get("value_alignment", 0) > 0.75:
            reasoning_parts.append("Shared values and brand alignment indicate authentic partnership potential.")
        
        # Add LLM reasoning if available
        if llm_reasoning:
            reasoning_parts.append(llm_reasoning)
        
        return " ".join(reasoning_parts) if reasoning_parts else "Moderate match with potential for collaboration."

    def explain_match(
        self,
        creator: Dict,
        brand: Dict,
        scores: Dict[str, float],
        llm_reasoning: str = ""
    ) -> Dict[str, any]:
        
        return {
            "reasoning": self.generate_reasoning(creator, brand, scores, llm_reasoning),
            "strengths": self.generate_strengths(creator, brand, scores),
            "concerns": self.generate_concerns(creator, brand, scores),
            "campaign_fit": self.generate_campaign_fit(creator, brand, scores)
        }

