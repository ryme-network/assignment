"""
Utility script to refresh MongoDB collections with updated data transformations.
Use this when you've added new fields to the data transformer and need to re-ingest.
"""
import json
import os
from pipeline import IngestionPipeline


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
    print("=" * 80)
    print("MongoDB Data Refresh Utility")
    print("=" * 80)
    print()
    
    # Load data
    print("Loading data from JSON files...")
    creators_data, brands_data = load_data()
    creators = creators_data["creators"]
    brands = brands_data["brands"]
    print(f"  Loaded {len(creators)} creators and {len(brands)} brands")
    print()
    
    # Initialize pipeline
    print("Initializing ingestion pipeline...")
    pipeline = IngestionPipeline()
    print()
    
    # Refresh data (clears and re-ingests)
    print("Refreshing MongoDB collections...")
    stats = pipeline.refresh_data(creators, brands, clear_existing=True)
    print()
    
    print("=" * 80)
    print("Refresh Complete!")
    print("=" * 80)
    print(f"  Ingested {stats['mongodb_creators']} creators")
    print(f"  Ingested {stats['mongodb_brands']} brands")
    print()
    print("All data has been refreshed with latest transformations.")
    print("New fields (languages, gender percentages, etc.) are now available.")
    
    # Close connections
    pipeline.close()
    print("\nPipeline closed successfully.")


if __name__ == "__main__":
    main()

