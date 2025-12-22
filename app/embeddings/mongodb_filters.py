from typing import List, Dict, Optional
from embeddings.metadata_store import MetadataStore
import re


class MongoDBFilters:
    """MongoDB-based filtering system for creators."""

    def __init__(self, metadata_store: MetadataStore):
        self.store = metadata_store

    def apply_hard_filters(self, brand: Dict) -> List[str]:
        """
        Apply hard filters using MongoDB queries.
        Returns list of creator_ids that pass all filters.
        
        Args:
            brand: Brand dictionary (can be raw JSON or MongoDB document)
        """
        # Get brand from MongoDB to use transformed data (with expanded locations, etc.)
        brand_id = brand.get("brand_id")
        if brand_id:
            brand_doc = self.store.get_brand(brand_id)
            if brand_doc:
                brand = brand_doc  # Use transformed brand from MongoDB
        
        prefs = brand.get("creator_preferences", {})

        # Extract filter criteria from brand
        allowed_platforms = prefs.get("platforms", [])

        # Parse follower range - use derived fields if available, otherwise parse
        min_followers = brand.get("follower_range_min")
        max_followers = brand.get("follower_range_max")
        
        if not min_followers or not max_followers:
            follower_range_str = prefs.get("follower_range", "")
            parsed_min, parsed_max, _ = self._parse_follower_range(follower_range_str)
            min_followers = parsed_min or 10000  # Default
            max_followers = parsed_max or 1000000  # Default

        # Language preferences
        language_pref = prefs.get("language_preference", "")
        preferred_langs = self._extract_languages(language_pref)

        # Build MongoDB query
        query = {
            "platform": {"$in": allowed_platforms},
            "followers": {"$gte": min_followers, "$lte": max_followers},
            "language": {"$in": preferred_langs}
        }

        # Query MongoDB
        filtered_creators = list(self.store.creators_collection.find(
            query,
            {"creator_id": 1, "_id": 0}
        ))

        creator_ids = [c["creator_id"] for c in filtered_creators]

        # Apply location overlap filter if brand has location preferences
        # Use expanded locations if available (from transformed brand)
        brand_locations = brand.get("locations_expanded")
        if not brand_locations:
            brand_locations = brand.get("target_audience", {}).get("locations", [])
        
        if brand_locations:
            location_filtered = self._filter_by_location_overlap(creator_ids, brand_locations)
            creator_ids = location_filtered

        # Apply must-avoid filter
        must_avoid = prefs.get("must_avoid", [])
        if must_avoid:
            creator_ids = self._filter_must_avoid(creator_ids, must_avoid)

        return creator_ids

    def _parse_follower_range(self, follower_range_str: str) -> tuple:
        """Parse follower range string to min/max."""
        if not follower_range_str:
            return None, None, None

        pattern = r'(\d+\.?\d*)\s*([KMkm])?\s*-\s*(\d+\.?\d*)\s*([KMkm])?'
        match = re.search(pattern, follower_range_str)

        if match:
            min_val = float(match.group(1))
            min_suffix = (match.group(2) or "").upper()
            max_val = float(match.group(3))
            max_suffix = (match.group(4) or "").upper()

            min_followers = int(min_val * (1000 if min_suffix == "K" else (1000000 if min_suffix == "M" else 1)))
            max_followers = int(max_val * (1000 if max_suffix == "K" else (1000000 if max_suffix == "M" else 1)))

            return min_followers, max_followers, None

        return None, None, None

    def _extract_languages(self, language_pref: str) -> List[str]:
        """Extract language codes from preference string."""
        langs = []
        if "hindi" in language_pref.lower():
            langs.append("Hindi")
        if "english" in language_pref.lower():
            langs.append("English")
        # Add more languages as needed
        return langs if langs else ["Hindi", "English"]  # Default

    def _filter_by_location_overlap(
        self,
        creator_ids: List[str],
        brand_locations: List[str]
    ) -> List[str]:
        """Filter creators by location overlap."""
        filtered_ids = []
        brand_locations_lower = [loc.lower() for loc in brand_locations]

        for creator_id in creator_ids:
            creator = self.store.get_creator(creator_id)
            if not creator:
                continue

            creator_locations = creator.get("audience_demographics", {}).get("top_locations", [])
            creator_locations_lower = [loc.lower() for loc in creator_locations]

            # Check for any overlap
            if any(loc in brand_locations_lower for loc in creator_locations_lower):
                filtered_ids.append(creator_id)
                continue

            # Also check expanded locations if available
            if creator.get("locations_expanded"):
                creator_expanded = [loc.lower() for loc in creator.get("locations_expanded", [])]
                if any(loc in brand_locations_lower for loc in creator_expanded):
                    filtered_ids.append(creator_id)

        return filtered_ids

    def _filter_must_avoid(
        self,
        creator_ids: List[str],
        must_avoid: List[str]
    ) -> List[str]:
        """Filter out creators that violate must-avoid rules."""
        filtered_ids = []

        for creator_id in creator_ids:
            creator = self.store.get_creator(creator_id)
            if not creator:
                continue

            # Check content themes and past collaborations
            creator_text = (
                " ".join(creator.get("content_themes", [])) + " " +
                " ".join(creator.get("past_brand_collaborations", [])) + " " +
                (creator.get("primary_niche", "") or "")
            ).lower()

            # Check if any must-avoid keyword appears
            should_avoid = False
            for avoid_term in must_avoid:
                if avoid_term.lower() in creator_text:
                    should_avoid = True
                    break

            if not should_avoid:
                filtered_ids.append(creator_id)

        return filtered_ids

