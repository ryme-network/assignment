import json
import os
import argparse
from datetime import datetime
from typing import Dict, List, Optional

from embeddings.metadata_store import MetadataStore
from embeddings.mongodb_filters import MongoDBFilters
from embeddings.llm_scorer import LLMScorer
# DISABLED: Direct field scorer - kept for reference but not used
# from embeddings.direct_field_scorer import DirectFieldScorer
from embeddings.hybrid_scorer import HybridScorer
from embeddings.match_explainer import MatchExplainer
from pipeline import IngestionPipeline


def load_data():
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    creators_path = os.path.join(script_dir, "creators.json")
    brands_path = os.path.join(script_dir, "brands.json")
    
    with open(creators_path, encoding="utf-8") as f:
        creators = json.load(f)

    with open(brands_path, encoding="utf-8") as f:
        brands = json.load(f)

    return creators, brands


def find_brand_by_name(brands_data: List[Dict], brand_name: str) -> Optional[Dict]:
    brand_name_lower = brand_name.lower()
    for brand in brands_data:
        if brand.get("brand_name", "").lower() == brand_name_lower:
            return brand
    return None


def recommend_creators_for_brand(
    brand_name: str,
    top_k: int = 10,
    output_file: Optional[str] = None,
    skip_ingestion: bool = False
) -> Dict:
    # Load data
    creators_data, brands_data = load_data()
    
    # Find brand
    brand = find_brand_by_name(brands_data["brands"], brand_name)
    if not brand:
        raise ValueError(f"Brand '{brand_name}' not found in brands data")
    
    print(f"Analyzing brand: {brand.get('brand_name')}")
    
    # Initialize pipeline and ingest data if needed
    pipeline = IngestionPipeline()
    
    if not skip_ingestion:
        print("Ingesting data into MongoDB...")
        pipeline.ingest_creators(creators_data["creators"])
        pipeline.ingest_brands(brands_data["brands"])
        print("Data ingestion complete.")
    
    metadata_store = pipeline.metadata_store
    filters = MongoDBFilters(metadata_store)
    llm_scorer = LLMScorer()
    # DISABLED: Direct field scorer - kept for reference but not used
    # direct_field_scorer = DirectFieldScorer()
    hybrid_scorer = HybridScorer()
    explainer = MatchExplainer()
    
    # Get transformed brand from MongoDB
    brand_id = brand.get("brand_id")
    transformed_brand = metadata_store.get_brand(brand_id) if brand_id else brand
    if not transformed_brand:
        transformed_brand = brand
    
    # Apply hard filters to get candidate creators
    print(f"\nApplying hard filters for brand: {transformed_brand.get('brand_name', 'N/A')}...")
    candidate_ids = filters.apply_hard_filters(transformed_brand)
    print(f"Found {len(candidate_ids)} candidates after filtering")
    
    if not candidate_ids:
        print("No candidates found matching the criteria!")
        pipeline.close()
        return {
            "brand_name": brand.get("brand_name"),
            "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
            "total_creators_analyzed": 0,
            "recommended_creators": []
        }
    
    # Fetch candidate creators
    candidates = metadata_store.get_creators_by_ids(candidate_ids)
    print(f"Fetched {len(candidates)} candidate profiles")
    
    # DISABLED: Direct field scoring (gender, age) - now using LLM-only approach
    # The direct_field_scorer is kept in code but not used in calculations
    # direct_field_scorer = DirectFieldScorer()  # Still imported but unused
    # print("\nCalculating direct field scores (gender, age)...")
    # direct_field_scores = {}
    # for candidate in candidates:
    #     scores = direct_field_scorer.calculate_direct_field_scores(candidate, transformed_brand)
    #     direct_field_scores[candidate["creator_id"]] = scores
    
    # Score candidates using LLM (now includes all explanations)
    print("\nScoring candidates with LLM (this may take a while)...")
    llm_scored_results = llm_scorer.score_batch(candidates, transformed_brand)
    print(f"Scored {len(llm_scored_results)} candidates")
    
    # Calculate comprehensive hybrid scores
    print("\nCalculating comprehensive hybrid scores...")
    comprehensive_results = []
    
    for llm_result in llm_scored_results:
        creator_id = llm_result["creator_id"]
        creator = next((c for c in candidates if c["creator_id"] == creator_id), None)
        
        if not creator:
            continue
        
        # DISABLED: Direct field scores - now using LLM-only approach
        # direct_scores = direct_field_scores.get(creator_id, {})
        
        # Calculate comprehensive scores (using LLM scores only, no direct field scores)
        comprehensive_scores = hybrid_scorer.calculate_comprehensive_scores(
            creator=creator,
            brand=transformed_brand,
            llm_scores={
                "content_score": llm_result.get("content_score", 0.5),
                "values_score": llm_result.get("values_score", 0.5),
                "audience_score": llm_result.get("audience_score", 0.5)
            },
            direct_field_scores=None  # Not used anymore
        )
        
        # Get LLM-generated explanations (all explanations now come from LLM)
        explanation = explainer.explain_match(
            creator=creator,
            brand=transformed_brand,
            scores=comprehensive_scores,
            llm_reasoning=llm_result.get("reasoning", ""),
            llm_strengths=llm_result.get("strengths", []),
            llm_concerns=llm_result.get("concerns", []),
            llm_campaign_fit=llm_result.get("campaign_fit", "")
        )
        
        # Build result (gender_score and age_score removed from score_breakdown)
        result = {
            "creator_id": creator_id,
            "creator_name": creator.get("name", "N/A"),
            "overall_match_score": comprehensive_scores["overall_match_score"],
            "score_breakdown": {
                "audience_alignment": comprehensive_scores["audience_alignment"],
                "content_relevance": comprehensive_scores["content_relevance"],
                "value_alignment": comprehensive_scores["value_alignment"],
                "engagement_quality": comprehensive_scores["engagement_quality"]
                # NOTE: gender_score and age_score removed - now using LLM-only approach
            },
            "reasoning": explanation["reasoning"],
            "strengths": explanation["strengths"],
            "concerns": explanation["concerns"],
            "campaign_fit": explanation["campaign_fit"]
        }
        
        comprehensive_results.append(result)
    
    comprehensive_results.sort(key=lambda x: x["overall_match_score"], reverse=True)
    
    top_recommendations = comprehensive_results[:top_k]
    
    output = {
        "brand_name": transformed_brand.get("brand_name"),
        "analysis_timestamp": datetime.utcnow().isoformat() + "Z",
        "total_creators_analyzed": len(candidates),
        "recommended_creators": top_recommendations
    }
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to {output_file}")
    
    # Close connections
    pipeline.close()
    
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Recommend creators for a brand using AI-powered matching"
    )
    parser.add_argument(
        "--brand",
        type=str,
        required=True,
        help="Name of the brand to analyze (e.g., 'Happi Planet' or 'Upside Health')"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of top recommendations to return (default: 10)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Output JSON file path (optional)"
    )
    parser.add_argument(
        "--skip-ingestion",
        default=True,
        action="store_true",
        help="Skip data ingestion (assumes data already in MongoDB)"
    )
    
    args = parser.parse_args()
    
    try:
        result = recommend_creators_for_brand(
            brand_name=args.brand,
            top_k=args.top_k,
            output_file=args.output,
            skip_ingestion=args.skip_ingestion
        )
        
        # Print results
        print("\n" + "="*80)
        print("RECOMMENDATION RESULTS")
        print("="*80)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
