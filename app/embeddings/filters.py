def apply_hard_filters(
    creators: list[dict],
    brand: dict,
) -> list[dict]:

    prefs = brand["creator_preferences"]
    min_f, max_f = 80_000, 350_000 

    allowed_platforms = set(prefs["platforms"])
    preferred_langs = {'Hindi','English'}               #TODO: Extract language by yourself

    filtered = []

    for c in creators:
        if c["platform"] not in allowed_platforms:
            continue

        if not (min_f <= c["followers"] <= max_f):
            continue

        if not preferred_langs.intersection(set(c["language"])):
            continue

        filtered.append(c)

    return filtered
