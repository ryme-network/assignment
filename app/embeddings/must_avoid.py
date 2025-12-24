def violates_must_avoid(creator: dict, brand: dict) -> bool:
    avoid = brand["creator_preferences"]["must_avoid"]

    creator_text = (
        " ".join(creator["content_themes"])
        + " "
        + " ".join(creator["past_brand_collaborations"])
    ).lower()

    for rule in avoid:
        if "chemical" in rule.lower() and "chemical" in creator_text:
            return True
        if "luxury" in rule.lower() and "luxury" in creator_text:
            return True

    return False
