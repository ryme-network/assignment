from typing import Dict, Optional, Tuple
import re


class DirectFieldScorer:
    def __init__(self):
        pass

    def calculate_gender_match_score(
        self,
        creator_gender: Dict[str, float],
        brand_gender_female: float,
        brand_gender_male: float
    ) -> float:
    
        creator_female = creator_gender.get("female", 0.0)
        creator_male = creator_gender.get("male", 0.0)
        
        gender_ratio = (creator_female * brand_gender_female) + (creator_male * brand_gender_male)
        
        return min(1.0, max(0.0, gender_ratio))

    def parse_age_range(self, age_range_str: str) -> Optional[Tuple[int, int]]:
        if not age_range_str:
            return None
        
        # Match pattern like "25-45" or "18-24"
        pattern = r'(\d+)\s*-\s*(\d+)'
        match = re.search(pattern, age_range_str)
        
        if match:
            min_age = int(match.group(1))
            max_age = int(match.group(2))
            return (min_age, max_age)
        
        return None

    def calculate_age_match_score(
        self,
        creator_age_groups: Dict[str, float],
        brand_age_range: str
    ) -> float:
        if not brand_age_range or not creator_age_groups:
            return 0.5  # Default neutral score
        
        brand_age_tuple = self.parse_age_range(brand_age_range)
        if not brand_age_tuple:
            return 0.5
        
        brand_min, brand_max = brand_age_tuple
        
        total_overlap = 0.0
        
        for age_group_str, proportion in creator_age_groups.items():
            group_tuple = self.parse_age_range(age_group_str)
            if not group_tuple:
                continue
            
            group_min, group_max = group_tuple
            
            overlap_min = max(brand_min, group_min)
            overlap_max = min(brand_max, group_max)
            
            if overlap_min <= overlap_max:
                group_span = group_max - group_min
                if group_span > 0:
                    overlap_span = overlap_max - overlap_min
                    overlap_ratio = overlap_span / group_span
                    total_overlap += proportion * overlap_ratio
        
        return min(1.0, max(0.0, total_overlap))

    def calculate_direct_field_scores(
        self,
        creator: Dict,
        brand: Dict
    ) -> Dict[str, float]:
        # Extract creator gender data
        creator_demographics = creator.get("audience_demographics", {})
        creator_gender = creator_demographics.get("gender", {})
        creator_age_groups = creator_demographics.get("age_groups", {})
        
        # Extract brand gender requirements (from transformed brand)
        brand_gender_female = brand.get("gender_female_percent", 0.0)
        brand_gender_male = brand.get("gender_male_percent", 0.0)
        
        # If not in transformed brand, try to extract from primary_gender
        if brand_gender_female == 0.0 and brand_gender_male == 0.0:
            # Fallback: try to extract from primary_gender string
            primary_gender = brand.get("target_audience", {}).get("primary_gender", "")
            if primary_gender:
                # Simple extraction as fallback
                if "70%" in primary_gender and "Female" in primary_gender:
                    brand_gender_female = 0.7
                    brand_gender_male = 0.3
                elif "60%" in primary_gender and "Female" in primary_gender:
                    brand_gender_female = 0.6
                    brand_gender_male = 0.4
                else:
                    # Default split
                    brand_gender_female = 0.5
                    brand_gender_male = 0.5
        
        # Extract brand age range
        brand_age_range = brand.get("target_audience", {}).get("age_range", "")
        
        # Calculate scores
        gender_score = self.calculate_gender_match_score(
            creator_gender,
            brand_gender_female,
            brand_gender_male
        )
        
        age_score = self.calculate_age_match_score(
            creator_age_groups,
            brand_age_range
        )
        
        # Calculate average of direct field scores
        direct_field_avg = (gender_score + age_score) / 2.0
        
        return {
            "gender_score": round(gender_score, 4),
            "age_score": round(age_score, 4),
            "direct_field_avg": round(direct_field_avg, 4)
        }

