import re
from typing import Dict, List, Optional, Tuple
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()


class DataTransformer:
    # Tier mapping
    TIER_MAPPING = {
        "nano-influencer": 1,
        "nano influencer": 1,
        "micro-influencer": 2,
        "micro influencer": 2,
        "mid-tier influencer": 3,
        "mid tier influencer": 3,
        "macro-tier influencer": 4,
        "macro tier influencer": 4,
        "macro-influencer": 4,
        "mega-tier influencer": 5,
        "mega tier influencer": 5,
        "mega-influencer": 5,
    }

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            try:
                self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception:
                # Fallback to gemini-1.5-pro if flash is not available
                try:
                    self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                except Exception as e:
                    print(f"Warning: Could not initialize Gemini model for location expansion: {e}")
                    self.gemini_model = None
        else:
            self.gemini_model = None

    def parse_posting_frequency(self, posting_frequency: str) -> Optional[float]:
        if not posting_frequency:
            return None

        posting_frequency = posting_frequency.lower().strip()

        if "daily" in posting_frequency:
            return 7.0

        range_pattern = r'(\d+)\s*-\s*(\d+)'
        range_match = re.search(range_pattern, posting_frequency)
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            return (min_val + max_val) / 2.0

        single_pattern = r'(\d+)\s*(?:posts?|videos?)\s*per\s*week'
        single_match = re.search(single_pattern, posting_frequency)
        if single_match:
            return float(single_match.group(1))

        any_number = re.search(r'(\d+)', posting_frequency)
        if any_number:
            return float(any_number.group(1))

        return None

    def parse_tier_numeric(self, tier: str) -> Optional[int]:
        if not tier:
            return None

        tier_lower = tier.lower().strip()

        if tier_lower in self.TIER_MAPPING:
            return self.TIER_MAPPING[tier_lower]

        for key, value in self.TIER_MAPPING.items():
            if key in tier_lower:
                return value

        return None

    def expand_locations_with_gemini(self, locations: List[str]) -> List[str]:
        if not self.gemini_model:
            return locations

        expanded_locations = []

        # Location expansion mapping (fallback for common terms)
        location_expansions = {
            "tier 1 cities": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune"],
            "tier 1 city": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai", "Kolkata", "Pune"],
            "delhi ncr": ["Delhi", "Noida", "Gurgaon", "Faridabad", "Ghaziabad"],
            "mumbai metro": ["Mumbai", "Navi Mumbai", "Thane"],
        }

        for location in locations:
            location_lower = location.lower().strip()

            if location_lower in location_expansions:
                expanded_locations.extend(location_expansions[location_lower])
                continue

            if location_lower not in ["tier 1 cities", "tier 1 city", "tier 2 cities", "metro cities"]:
                expanded_locations.append(location)
                continue

            try:
                prompt = f"""List the major cities included in "{location}" in India context. 
Return only a comma-separated list of city names, no explanations. 
Example: If input is "Tier 1 cities", return: Mumbai, Delhi, Bangalore, Hyderabad, Chennai, Kolkata, Pune
Input: {location}
Output:"""

                response = self.gemini_model.generate_content(prompt)
                result = response.text.strip()

                # Parse comma-separated list
                cities = [city.strip() for city in result.split(",")]
                expanded_locations.extend(cities)

            except Exception as e:
                print(f"Warning: Gemini API error for location '{location}': {e}")
                # Fallback: keep original location
                expanded_locations.append(location)

        # Remove duplicates while preserving order
        seen = set()
        unique_locations = []
        for loc in expanded_locations:
            if loc.lower() not in seen:
                seen.add(loc.lower())
                unique_locations.append(loc)

        return unique_locations

    def parse_follower_range(self, follower_range_str: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        if not follower_range_str:
            return None, None, None

        # Extract numbers with K/M suffix
        pattern = r'(\d+\.?\d*)\s*([KMkm])?\s*-\s*(\d+\.?\d*)\s*([KMkm])?'
        match = re.search(pattern, follower_range_str)

        min_followers = None
        max_followers = None

        if match:
            min_val = float(match.group(1))
            min_suffix = (match.group(2) or "").upper()
            max_val = float(match.group(3))
            max_suffix = (match.group(4) or "").upper()

            # Convert to actual numbers
            if min_suffix == "K":
                min_followers = int(min_val * 1000)
            elif min_suffix == "M":
                min_followers = int(min_val * 1000000)
            else:
                min_followers = int(min_val)

            if max_suffix == "K":
                max_followers = int(max_val * 1000)
            elif max_suffix == "M":
                max_followers = int(max_val * 1000000)
            else:
                max_followers = int(max_val)

        # Extract influencer type category
        influencer_type = None
        if "micro" in follower_range_str.lower():
            influencer_type = "micro"
        elif "mid-tier" in follower_range_str.lower() or "mid tier" in follower_range_str.lower():
            influencer_type = "mid-tier"
        elif "macro" in follower_range_str.lower():
            influencer_type = "macro"
        elif "nano" in follower_range_str.lower():
            influencer_type = "nano"
        elif "mega" in follower_range_str.lower():
            influencer_type = "mega"

        return min_followers, max_followers, influencer_type

    def extract_metrics_from_string(self, metric_str: str) -> Dict[str, Optional[float]]:
        if not metric_str:
            return {"min": None, "max": None, "avg": None, "value": None}

        metric_str = metric_str.lower().strip()

        range_pattern = r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)\s*(million|thousand|k|m)?'
        range_match = re.search(range_pattern, metric_str)

        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            suffix = (range_match.group(3) or "").lower()

            multiplier = 1000000 if suffix in ["million", "m"] else (1000 if suffix in ["thousand", "k"] else 1)

            return {
                "min": min_val * multiplier,
                "max": max_val * multiplier,
                "avg": ((min_val + max_val) / 2) * multiplier,
                "value": None
            }

        single_pattern = r'(\d+[,\d]*\.?\d*)\s*(million|thousand|k|m)?'
        single_match = re.search(single_pattern, metric_str)

        if single_match:
            value = float(single_match.group(1).replace(",", ""))
            suffix = (single_match.group(2) or "").lower()
            multiplier = 1000000 if suffix in ["million", "m"] else (1000 if suffix in ["thousand", "k"] else 1)
            final_value = value * multiplier

            return {
                "min": None,
                "max": None,
                "avg": None,
                "value": final_value
            }

        return {"min": None, "max": None, "avg": None, "value": None}

    def transform_creator(self, creator: Dict) -> Dict:
        transformed = creator.copy()

        demographics = creator.get("audience_demographics", {})
        gender = demographics.get("gender", {})

        transformed["female_ratio"] = gender.get("female")
        transformed["male_ratio"] = gender.get("male")

        transformed["age_groups"] = demographics.get("age_groups", {})

        posting_freq_raw = creator.get("posting_frequency", "")
        transformed["avg_post_per_week"] = self.parse_posting_frequency(posting_freq_raw)
        transformed["posting_frequency_raw"] = posting_freq_raw

        tier_raw = creator.get("tier", "")
        transformed["tier_numeric"] = self.parse_tier_numeric(tier_raw)
        transformed["tier_raw"] = tier_raw

        return transformed

    def transform_brand(self, brand: Dict) -> Dict:
        transformed = brand.copy()

        target_audience = brand.get("target_audience", {})
        locations = target_audience.get("locations", [])

        transformed["locations_expanded"] = self.expand_locations_with_gemini(locations)
        transformed["locations_raw"] = locations

        campaign_goals = brand.get("campaign_goals", {})
        target_metrics = campaign_goals.get("target_metrics", {})

        reach_str = target_metrics.get("reach", "")
        engagement_str = target_metrics.get("engagement", "")
        conversions_str = target_metrics.get("conversions", "")

        transformed["target_metrics_reach"] = self.extract_metrics_from_string(reach_str)
        transformed["target_metrics_engagement"] = self.extract_metrics_from_string(engagement_str)
        transformed["target_metrics_conversions"] = self.extract_metrics_from_string(conversions_str)

        # Parse follower range from creator_preferences
        creator_prefs = brand.get("creator_preferences", {})
        follower_range_str = creator_prefs.get("follower_range", "")

        min_followers, max_followers, influencer_type = self.parse_follower_range(follower_range_str)
        transformed["follower_range_min"] = min_followers
        transformed["follower_range_max"] = max_followers
        transformed["influencer_type_category"] = influencer_type

        # Extract engagement priority
        transformed["engagement_priority"] = creator_prefs.get("engagement_priority")

        # Extract income level (can be normalized further if needed)
        income_level = target_audience.get("income_level", "")
        transformed["income_level_derived"] = income_level  # Keep as-is for now, can add parsing later

        return transformed

