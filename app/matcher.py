import json
import os

from embeddings.metadata_store import MetadataStore
from embeddings.mongodb_filters import MongoDBFilters
from embeddings.llm_scorer import LLMScorer
from pipeline import IngestionPipeline
from embeddings.explain import explain_match

def load_data():
    """Load data from JSON files."""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    creators_path = os.path.join(script_dir, "creators.json")
    brands_path = os.path.join(script_dir, "brands.json")
    
    with open(creators_path, encoding="utf-8") as f:
        creators = json.load(f)

    with open(brands_path, encoding="utf-8") as f:
        brands = json.load(f)

    return creators, brands

def main():
    # Load data
    creators_data, brands_data = load_data()
    brand = brands_data["brands"][0]        #TODO: Add from CLI
    creators = creators_data["creators"]
    
    print("Initializing ingestion pipeline...")
    pipeline = IngestionPipeline()
    
    print("Ingesting creators into MongoDB...")
    creator_stats = pipeline.ingest_creators(creators)
    print(f"  Ingested {creator_stats['mongodb_creators']} creators")
    
    print("Ingesting brands into MongoDB...")
    brand_stats = pipeline.ingest_brands(brands_data["brands"])
    print(f"  Ingested {brand_stats['mongodb_brands']} brands")
    
    metadata_store = pipeline.metadata_store
    filters = MongoDBFilters(metadata_store)
    scorer = LLMScorer()
    
    print(f"\nApplying hard filters for brand: {brand.get('brand_name', 'N/A')}...")
    candidate_ids = filters.apply_hard_filters(brand)
    print(f"Found {len(candidate_ids)} candidates after filtering")
    
    if not candidate_ids:
        print("No candidates found matching the criteria!")
        pipeline.close()
        return
    
    # Fetch candidate creators from MongoDB
    candidates = metadata_store.get_creators_by_ids(candidate_ids)
    print(f"Fetched {len(candidates)} candidate profiles from MongoDB")
    
    # Score candidates using LLM
    print("\nScoring candidates with LLM (this may take a while)...")
    scored_results = scorer.score_batch(candidates, brand)
    print(f"Scored {len(scored_results)} candidates")
    
    # Sort by final score
    scored_results.sort(key=lambda x: x["final_score"], reverse=True)
    
    # Get top results
    top_k = 10
    top_results = scored_results[:top_k]
    
    # Fetch full creator data for explanations
    final_results = []
    for result in top_results:
        creator = metadata_store.get_creator(result["creator_id"])
        if creator:
            result["explanation"] = explain_match(result, creator, brand)
            result["creator_name"] = creator.get("name", "N/A")
            final_results.append(result)
    
    # Output results
    print("\n" + "="*80)
    print("Top Matched Creators:\n")
    for r in final_results[:5]:
        print("=" * 80)
        print(f"Creator ID      : {r['creator_id']}")
        print(f"Creator Name    : {r.get('creator_name', 'N/A')}")
        print(f"Final Score     : {r['final_score']}")
        print(f"Content Score   : {r['content_score']}")
        print(f"Values Score    : {r['values_score']}")
        print(f"Audience Score  : {r['audience_score']}")
        if r.get('reasoning'):
            print(f"LLM Reasoning   : {r['reasoning']}")
        print(f"\n{r.get('explanation', '')}")
        print()
    
    # Close connections
    pipeline.close()
    print("\nPipeline closed successfully.")


if __name__ == "__main__":
    main()
