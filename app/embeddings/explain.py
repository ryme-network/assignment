def explain_match(result: dict, creator: dict, brand: dict) -> str: #TODO: Make sure that the explainability feature is dynamic
    reasons = []

    if result["content_score"] > 0.75:
        reasons.append(
            f"Strong content alignment in {', '.join(creator['content_categories'])}"
        )

    if result["values_score"] > 0.75:
        reasons.append(
            "Shared values around sustainability, safety, and conscious consumption"
        )

    if result["audience_score"] > 0.70:
        reasons.append(
            f"Audience overlap with urban families in {', '.join(creator['audience_demographics']['top_locations'])}"
        )

    return "Matched because:\n• " + "\n• ".join(reasons)
