from pymongo import MongoClient
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()


class MetadataStore:

    def __init__(
        self,
        connection_uri: Optional[str] = None,
        database_name: Optional[str] = None
    ):
        self.connection_uri = connection_uri or os.getenv(
            "MONGODB_URI",
            "mongodb://localhost:27017/"
        )
        self.database_name = database_name or os.getenv(
            "MONGODB_DATABASE",
            "creator_brand_db"
        )

        # Connect to MongoDB
        self.client = MongoClient(self.connection_uri)
        self.db = self.client[self.database_name]

        # Collections
        self.creators_collection = self.db["creators"]
        self.brands_collection = self.db["brands"]

        # Create indexes for better query performance
        self._create_indexes()

    def _create_indexes(self):
        """Create indexes on commonly queried fields."""
        try:
            # Creator indexes
            self.creators_collection.create_index("creator_id", unique=True)
            self.creators_collection.create_index("platform")
            self.creators_collection.create_index("tier_numeric")
            self.creators_collection.create_index("followers")
            self.creators_collection.create_index("audience_demographics.top_locations")

            # Brand indexes
            self.brands_collection.create_index("brand_id", unique=True)
            self.brands_collection.create_index("locations_expanded")
            self.brands_collection.create_index("follower_range_min")
            self.brands_collection.create_index("follower_range_max")
            self.brands_collection.create_index("primary_gender_extracted")
            self.brands_collection.create_index("income_level_category")
            self.brands_collection.create_index("languages")
        except Exception as e:
            print(f"Warning: Error creating indexes (may already exist): {e}")

    def insert_creator(self, creator_data: Dict) -> str:
        creator_id = creator_data["creator_id"]
        result = self.creators_collection.update_one(
            {"creator_id": creator_id},
            {"$set": creator_data},
            upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else creator_id

    def insert_creators_batch(self, creators_data: List[Dict]) -> int:
        from pymongo import UpdateOne

        # Use bulk operations for efficiency
        operations = []
        for creator in creators_data:
            operations.append(
                UpdateOne(
                    {"creator_id": creator["creator_id"]},
                    {"$set": creator},
                    upsert=True
                )
            )

        if operations:
            result = self.creators_collection.bulk_write(operations)
            return result.modified_count + result.upserted_count
        return 0

    def insert_brand(self, brand_data: Dict) -> str:
        """Insert or update a brand document."""
        brand_id = brand_data["brand_id"]
        result = self.brands_collection.update_one(
            {"brand_id": brand_id},
            {"$set": brand_data},
            upsert=True
        )
        return str(result.upserted_id) if result.upserted_id else brand_id

    def insert_brands_batch(self, brands_data: List[Dict]) -> int:
        """Insert multiple brands in batch."""
        from pymongo import UpdateOne

        operations = []
        for brand in brands_data:
            operations.append(
                UpdateOne(
                    {"brand_id": brand["brand_id"]},
                    {"$set": brand},
                    upsert=True
                )
            )

        if operations:
            result = self.brands_collection.bulk_write(operations)
            return result.modified_count + result.upserted_count
        return 0

    def get_creator(self, creator_id: str) -> Optional[Dict]:
        """Retrieve a creator by ID."""
        result = self.creators_collection.find_one({"creator_id": creator_id})
        if result:
            result.pop("_id", None)  # Remove MongoDB's _id field
        return result

    def get_brand(self, brand_id: str) -> Optional[Dict]:
        """Retrieve a brand by ID."""
        result = self.brands_collection.find_one({"brand_id": brand_id})
        if result:
            result.pop("_id", None)  # Remove MongoDB's _id field
        return result

    def get_creators_by_ids(self, creator_ids: List[str]) -> List[Dict]:
        """Retrieve multiple creators by IDs."""
        results = list(self.creators_collection.find({"creator_id": {"$in": creator_ids}}))
        for result in results:
            result.pop("_id", None)  # Remove MongoDB's _id field
        return results

    def find_creators_by_location_overlap(self, target_locations: List[str]) -> List[Dict]:
        """
        Find creators whose top_locations overlap with target locations.
        """
        results = list(self.creators_collection.find({
            "audience_demographics.top_locations": {"$in": target_locations}
        }))
        for result in results:
            result.pop("_id", None)
        return results

    def find_creators_by_age_group(self, age_ranges: List[str], min_overlap: float = 0.0) -> List[Dict]:
        query = {"$or": []}
        for age_range in age_ranges:
            query["$or"].append({
                f"age_groups.{age_range}": {"$gte": min_overlap}
            })

        results = list(self.creators_collection.find(query))
        for result in results:
            result.pop("_id", None)
        return results

    def find_brands_by_location_overlap(self, target_locations: List[str]) -> List[Dict]:
        """Find brands with location overlap."""
        results = list(self.brands_collection.find({
            "locations_expanded": {"$in": target_locations}
        }))
        for result in results:
            result.pop("_id", None)
        return results

    def clear_creators(self) -> int:
        """Delete all creators from the collection. Returns count of deleted documents."""
        result = self.creators_collection.delete_many({})
        return result.deleted_count

    def clear_brands(self) -> int:
        """Delete all brands from the collection. Returns count of deleted documents."""
        result = self.brands_collection.delete_many({})
        return result.deleted_count

    def clear_all(self) -> Dict[str, int]:
        """Clear both creators and brands collections. Returns count of deleted documents."""
        creators_deleted = self.clear_creators()
        brands_deleted = self.clear_brands()
        return {
            "creators_deleted": creators_deleted,
            "brands_deleted": brands_deleted
        }

    def close(self):
        """Close MongoDB connection."""
        self.client.close()

