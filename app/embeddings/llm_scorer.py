from typing import Dict, List, Optional
import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
import time
from tqdm import tqdm

load_dotenv()


class LLMScorer:

    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model_name: Optional[str] = None,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=self.api_key)
        
        # Get model name from parameter, env var, or use default
        model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        
        self.max_retries = max_retries
        
        # Try to initialize the model
        try:
            self.model = genai.GenerativeModel(model_name)
            print(f"Initialized Gemini model: {model_name}")
        except Exception as e:
            print(f"Warning: Failed to initialize {model_name}: {e}")
            # Try fallback models
            fallback_models = ['gemini-2.5-flash', 'gemini-2.5-flash-lite', 'gemini-2.5-pro']
            model_initialized = False
            for fallback in fallback_models:
                if fallback == model_name:
                    continue  # Skip the one we already tried
                try:
                    self.model = genai.GenerativeModel(fallback)
                    print(f"Successfully initialized fallback model: {fallback}")
                    model_initialized = True
                    break
                except Exception:
                    continue
            
            if not model_initialized:
                # Last resort: try to list available models for debugging
                try:
                    models = genai.list_models()
                    print("Available models:")
                    for m in models:
                        if 'generateContent' in m.supported_generation_methods:
                            print(f"  - {m.name}")
                except Exception:
                    pass
                raise ValueError(f"Failed to initialize any Gemini model. Tried: {model_name}, {', '.join([m for m in fallback_models if m != model_name])}")

    def _is_quota_error(self, error: Exception) -> bool:
        """Check if error is a quota/rate limit error."""
        error_str = str(error).lower()
        quota_keywords = ['quota', 'rate limit', '429', 'resource_exhausted', 'too many requests']
        return any(keyword in error_str for keyword in quota_keywords)

    def score_creator_brand_match(
        self,
        creator: Dict,
        brand: Dict
    ) -> Dict:
        prompt = self._create_scoring_prompt(creator, brand)

        # Retry logic with exponential backoff for quota errors
        for attempt in range(self.max_retries):
            try:
                response = self.model.generate_content(prompt)
                result_text = response.text.strip()

                scores = self._parse_llm_response(result_text)
                return scores

            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a quota/rate limit error
                if self._is_quota_error(e) and attempt < self.max_retries - 1:
                    # Exponential backoff: wait longer each retry (1s, 2s, 4s...)
                    wait_time = 2 ** attempt
                    print(f"Quota/rate limit error for creator {creator.get('creator_id')}, "
                          f"retrying in {wait_time} seconds (attempt {attempt + 1}/{self.max_retries})...")
                    time.sleep(wait_time)
                    continue
                else:
                    # For other errors or max retries reached, return default scores
                    if self._is_quota_error(e):
                        print(f"Max retries reached for creator {creator.get('creator_id')} due to quota limits")
                    else:
                        print(f"Error scoring creator {creator.get('creator_id')}: {e}")
                    
                    return {
                        "content_score": 0.5,
                        "values_score": 0.5,
                        "audience_score": 0.5,
                        "final_score": 0.5,
                        "reasoning": f"Error during LLM scoring: {error_msg}"
                    }
        
        # If we get here, all retries failed
        return {
            "content_score": 0.5,
            "values_score": 0.5,
            "audience_score": 0.5,
            "final_score": 0.5,
            "reasoning": "Failed after all retry attempts"
        }

    def _create_scoring_prompt(self, creator: Dict, brand: Dict) -> str:
        """Create prompt for LLM scoring."""
        
        # Extract creator info
        creator_audience = creator.get('audience_demographics', {})
        creator_gender = creator_audience.get('gender', {})
        creator_locations = creator_audience.get('top_locations', [])
        
        # Extract brand info
        brand_audience = brand.get('target_audience', {})
        brand_prefs = brand.get('creator_preferences', {})
        
        prompt = f"""You are a marketing agency expert at matching influencers with brands for marketing campaigns.

Analyze the compatibility between this creator and brand, and provide scores (0.0 to 1.0) for three dimensions:

**Creator Profile:**
- Name: {creator.get('name', 'N/A')}
- Platform: {creator.get('platform', 'N/A')}
- Followers: {creator.get('followers', 'N/A')}
- Primary Niche: {creator.get('primary_niche', 'N/A')}
- Content Categories: {', '.join(creator.get('content_categories', []))}
- Bio: {creator.get('bio', 'N/A')}
- Content Themes: {', '.join(creator.get('content_themes', [])[:5])}
- Values: {', '.join(creator.get('values', []))}
- Past Collaborations: {', '.join(creator.get('past_brand_collaborations', []))}
- Audience Gender: Female {creator_gender.get('female', 0)*100:.0f}%, Male {creator_gender.get('male', 0)*100:.0f}%
- Top Locations: {', '.join(creator_locations[:5])}
- Engagement Rate: {creator.get('engagement_rate', 'N/A')}

**Brand Profile:**
- Name: {brand.get('brand_name', 'N/A')}
- Industry: {brand.get('industry', 'N/A')}
- Description: {brand.get('description', 'N/A')[:300]}
- Brand Values: {', '.join(brand.get('brand_values', []))}
- Target Audience Gender: {brand_audience.get('primary_gender', 'N/A')}
- Target Locations: {', '.join(brand_audience.get('locations', [])[:5])}
- Niche Alignment Needed: {', '.join(brand_prefs.get('niche_alignment', []))}
- Content Style: {brand_prefs.get('content_style', 'N/A')}

Score the match on these dimensions (0.0 to 1.0):

1. **Content Alignment**: How well does the creator's content, niche, and themes align with the brand's needs?
2. **Values Alignment**: How well do the creator's values and past collaborations align with brand values?
3. **Audience Alignment**: How well does the creator's audience (demographics, locations, interests) match the brand's target audience?

Return ONLY a JSON object in this exact format:
{{
    "content_score": 0.85,
    "values_score": 0.90,
    "audience_score": 0.80,
    "reasoning": "Brief explanation of the scores (2-3 sentences)"
}}

Do not include any other text, only the JSON."""

        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict:
        """Parse LLM response to extract scores."""
        try:
            cleaned = response_text.strip()
            if "```json" in cleaned:
                cleaned = cleaned.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned:
                cleaned = cleaned.split("```")[1].split("```")[0].strip()

            scores = json.loads(cleaned)

            # Validate scores
            content_score = float(scores.get("content_score", 0.5))
            values_score = float(scores.get("values_score", 0.5))
            audience_score = float(scores.get("audience_score", 0.5))

            # Clamp scores to [0, 1]
            content_score = max(0.0, min(1.0, content_score))
            values_score = max(0.0, min(1.0, values_score))
            audience_score = max(0.0, min(1.0, audience_score))

            # Calculate weighted final score
            weights = {
                "content": 0.45,
                "values": 0.35,
                "audience": 0.20
            }
            final_score = (
                weights["content"] * content_score +
                weights["values"] * values_score +
                weights["audience"] * audience_score
            )

            return {
                "content_score": round(content_score, 4),
                "values_score": round(values_score, 4),
                "audience_score": round(audience_score, 4),
                "final_score": round(final_score, 4),
                "reasoning": scores.get("reasoning", "")
            }

        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Response was: {response_text[:200]}")
            # Return default scores
            return {
                "content_score": 0.5,
                "values_score": 0.5,
                "audience_score": 0.5,
                "final_score": 0.5,
                "reasoning": "Error parsing LLM response"
            }

    def score_batch(
        self,
        creators: List[Dict],
        brand: Dict,
        batch_size: int = 5
    ) -> List[Dict]:
        """
        Score multiple creators in batches.
        Returns list of score dictionaries with creator_id.
        """
        results = []
        total = len(creators)

        print(f"Scoring {total} creators...")
        
        for i, creator in tqdm(enumerate(creators, 1)):
            if i % 10 == 0:
                print(f"  Progress: {i}/{total} creators scored...")
            
            scores = self.score_creator_brand_match(creator, brand)
            scores["creator_id"] = creator["creator_id"]
            results.append(scores)

        print(f"Completed scoring {total} creators")
        return results

