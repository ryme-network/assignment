# AI Developer Take-Home Assignment: Creator-Brand Matching System

## Overview

Build an AI-powered command-line tool that analyzes creator profiles and brand requirements to recommend optimal creator-brand matches for influencer marketing campaigns. This assignment provides a glimpse of how creator and brand fit analysis happens at ryme.ai, although it is not the actual algorithm but downsized to fit an assignment scope level.

**Timeline:** Maximum 2 working days (16 hours)

---

## Objective

Create a CLI application that:
1. Reads creator and brand profile data from JSON files
2. Analyzes compatibility between creators and brands using AI/ML techniques
3. Generates match scores with detailed reasoning
4. Outputs ranked recommendations in structured JSON format

---

## Problem Statement

You're building a matching algorithm for an influencer marketing platform. Given:
- **10 Indian creator profiles** with audience demographics, content themes, past collaborations, and engagement metrics
- **2 Indian brand profiles** (Happi Planet & Upside Health) with target audiences, campaign goals, and creator preferences

Your task is to recommend the best creator matches for each brand with explainable scoring.

---

## Requirements

### Functional Requirements

**Input:**
- Accept brand ID as a command-line argument
- Read `creators.json` and `brands.json`

**Processing:**
- Design a matching algorithm considering multiple factors:
  - Audience alignment (demographics, interests, income levels)
  - Content relevance (niche fit, content themes)
  - Value alignment (brand values vs creator values and past collaborations)
  - Engagement quality (engagement rate, content quality score)
- Use LLM/AI for semantic analysis of:
  - Creator bios and content themes vs brand messaging
  - Value alignment between creator and brand
  - Past collaboration patterns
- Calculate weighted match scores (0-1 scale)
- Rank creators by overall match score

**Output (JSON format):**
```json
{
  "brand_name": "Happi Planet",
  "analysis_timestamp": "2024-12-21T10:30:00Z",
  "total_creators_analyzed": 10,
  "recommended_creators": [
    {
      "creator_id": "CR001",
      "creator_name": "Priya's Sustainable Home",
      "overall_match_score": 0.87,
      "score_breakdown": {
        "audience_alignment": 0.90,
        "content_relevance": 0.88,
        "value_alignment": 0.85,
        "engagement_quality": 0.86
      },
      "reasoning": "Strong alignment with eco-conscious messaging...",
      "strengths": [
        "Perfect niche match - sustainability + home care",
        "Audience demographics align with brand target"
      ],
      "concerns": [
        "Slightly smaller follower count than ideal"
      ],
      "campaign_fit": "Ideal for eco-friendly home products launch"
    }
  ]
}
```

### Technical Requirements

**Must Have:**
- Python 3.8+ (or JavaScript/TypeScript with justification in README)
- CLI argument parsing for brand selection
- LLM API integration (OpenAI, Anthropic Claude, Google Gemini, or others)
- Environment variable support for API keys
- Basic error handling (file not found, API failures, invalid input)
- Modular, clean code with meaningful variable/function names
- Proper code comments explaining key logic

**Code Quality:**
- Separation of concerns (data loading, scoring, LLM integration)
- Reusable functions
- Avoid hardcoding - use configuration where appropriate

---

## Matching Algorithm Guidance

Your algorithm should consider these factors (weights are suggestions, you can adjust):

### 1. Audience Alignment
- Age group overlap between creator audience and brand target
- Gender distribution match
- Geographic location relevance
- Income level compatibility
- Interest overlap

### 2. Content Relevance
- Primary niche alignment with brand industry
- Content themes matching brand messaging
- Platform suitability for campaign type
- Past collaboration relevance

### 3. Value Alignment
- Semantic similarity between creator and brand values (use LLM)
- Past collaboration quality and authenticity
- Consistency in messaging

### 4. Engagement Quality
- Engagement rate relative to follower count
- Content quality score
- Posting consistency

**Important Considerations:**
- How do you normalize scores across different follower ranges?
- Should micro-influencers (high engagement) rank above macro-influencers (lower engagement)?
- How do you detect value contradictions (e.g., sustainability claims vs fast-fashion partnerships)?
- How do you weight different factors for brand creator alignment?

---

## Test Data

You'll receive three files:

1. **`creators.json`** - diverse Indian creator profiles
2. **`brands.json`** - 2 real Indian brand profiles:
   - **Happi Planet**: Eco-friendly home care products
   - **Upside Health**: Healthy desserts (no sugar, no gluten)
3. **`TEST_DATA.md`** - Data structure and test case explanations

**Note:** The data contains deliberate edge cases and anomalies to test analytical thinking. Good algorithms will identify these.

---

## Deliverables

### 1. Source Code
- Git repository with clear commit history
- Minimum 8-12 meaningful commits showing iterative development
- **Not acceptable:** Single large commit with all code

### 2. README.md
Must include:
- **Setup Instructions**: Dependencies, installation steps
- **Configuration**: How to set API keys (environment variables)
- **Usage Examples**: 
  ```bash
  python matcher.py --brand "Happi Planet"
  python matcher.py --brand "Upside Health"
  ```
- **Algorithm Design**: 
  - Your approach to the matching problem
  - Factor weights and rationale
  - How you use LLM vs rule-based scoring
  - Assumptions made
- **Known Limitations**: What could be improved with more time/data

### 3. Results Analysis Document (PDF or Markdown)

**This is critical - 30% of your evaluation.**

Must include:

#### A. Cross-Brand Comparison
- Run your algorithm on both brands
- Show how the same creators ranked differently
- Pick 2-3 creators and explain in detail why rankings differ
- Example: "Priya's Sustainable Home ranks #1 for Happi Planet but #8 for Upside Health because..."

#### B. Surprising Results
- Identify 3 results that surprised you
- Explain why they were surprising
- Discuss whether the algorithm's reasoning makes sense

#### C. Edge Cases Discovered
- Did you find any anomalies or contradictions in creator profiles?
- How did your algorithm handle them?
- Examples: Value misalignment, audience mismatch, past collaboration inconsistencies

#### D. Prompt Engineering
- Share 2-3 different LLM prompts you tried
- Show actual LLM outputs for the same creator with different prompts
- Explain which worked best and why

#### E. Specific Score Breakdown
- Pick one controversial or borderline match
- Show complete score breakdown with reasoning for each component

### 4. Sample Output Files
- JSON output for both brands (`happi_planet_matches.json`, `upside_health_matches.json`)

---

## Evaluation Criteria

| Criteria | Weight | What We're Testing |
|----------|--------|-------------------|
| **Results Analysis** | 30% | Do you understand your algorithm? Depth of analysis and self-critique |
| **AI/ML Implementation** | 25% | Quality of LLM integration, prompt engineering, scoring methodology |
| **Algorithm Design** | 25% | Soundness of matching logic, thoughtful factor weighting, handling edge cases |
| **Code Quality** | 15% | Clean implementation, modularity, readability |
| **Domain Understanding** | 5% | Understanding of Indian creator economy and influencer marketing |

---

## Submission Instructions

**Email to:** [rahul@ryme.ai]

**Subject:** [Your Name] - AI Developer Assignment Submission

**Include:**
1. Link to Git repository (public or provide access)
2. Results Analysis Document (PDF/Markdown)
3. Sample JSON output files
4. Brief note on:
   - Which LLM API you chose and why
   - Any blockers you faced and how you handled them
   - Total time spent (optional but appreciated)

**Due Date:** 2 working days from receipt

---

## Important Notes

- **Focus on thoughtful analysis over perfect code** - We value your thinking process
- **The data contains deliberate anomalies** - Identifying them shows attention to detail
- **Document your assumptions clearly** - There are multiple valid approaches
- **AI assistance is fine for coding** - But your analysis must show original thinking
- **We may schedule a 30-minute discussion** - Be prepared to explain your decisions
- **Git history matters** - Show iterative development, not copy-paste

---

## Red Flags We Watch For

**Indicates Shallow/AI-Generated Work:**
- ❌ Ranks purely by follower count without niche consideration
- ❌ Misses obvious value contradictions in creator profiles
- ❌ Generic analysis that could apply to any dataset
- ❌ No mention of specific creators or brands by name
- ❌ Perfect algorithm with no limitations discussed
- ❌ Single commit with all code
- ❌ Can't explain scoring decisions in follow-up discussion

**Indicates Authentic Thinking:**
- ✅ Identifies specific anomalies or edge cases in data
- ✅ Explains trade-offs (micro vs macro influencers, niche vs reach)
- ✅ References specific creators/brands in analysis
- ✅ Self-critique of algorithm weaknesses
- ✅ Different rankings across brands with clear reasoning
- ✅ Multiple commits showing thought evolution
- ✅ Can walk through any scoring decision

---

## Example Questions We Might Ask

1. Walk me through how your algorithm scored [Specific Creator] for [Specific Brand]. Why did they get that score?

2. Your code weighted engagement at X%. What happens if we change it to Y%? Which creators would move up/down?

3. Did you notice anything unusual about any creator profiles? How did your algorithm handle it?

4. Why did [Creator A] rank higher than [Creator B] for this brand despite having fewer followers?

5. Show me your LLM prompt for value alignment. Let's modify it together - how would results change?

---

## Questions?

For clarifications within 24 hours of receiving this assignment, contact: [rahul@ryme.ai]

---

## Good Luck!

We're excited to see your approach to this problem. Remember: We're not looking for perfection - we're looking for thoughtful problem-solving, clear communication, and genuine analytical thinking.

The best submissions show deep engagement with the problem, honest self-assessment, and evidence of iterative refinement.
