def creator_content_text(creator: dict) -> str:
    return (
        f"The creator focuses on {', '.join(creator['content_categories'])}. "
        f"Their primary niche is {creator['primary_niche']}. "
        f"Key themes include: {', '.join(creator['content_themes'])}. "
        f"Bio: {creator['bio']}."
    )


def creator_values_text(creator: dict) -> str:
    return (
        "The creator strongly believes in the following values: "
        + ", ".join(creator["values"])
        + "."
    )


def creator_audience_text(creator: dict) -> str:
    demographics = creator["audience_demographics"]
    return (
        f"The creator's audience is primarily "
        f"{demographics['gender']['female']*100:.0f}% female, "
        f"aged mainly 25 to 44, located in "
        f"{', '.join(demographics['top_locations'])}. "
        f"Income levels include upper middle class and affluent households. "
        f"Content is delivered in {', '.join(creator['language'])}."
    )


def brand_mission_text(brand: dict) -> str:
    return (
        f"{brand['brand_name']} operates in the {brand['industry']} space. "
        f"{brand['description']} "
        f"Core values include: {', '.join(brand['brand_values'])}. "
        f"Unique strengths: {', '.join(brand['unique_selling_points'])}."
    )


def brand_creator_fit_text(brand: dict) -> str:
    prefs = brand["creator_preferences"]
    return (
        "The brand prefers creators aligned with "
        f"{', '.join(prefs['niche_alignment'])}. "
        f"Content style should be {prefs['content_style']}. "
        f"Past successful partnerships include "
        f"{', '.join(brand['past_successful_partnerships'])}."
    )

def brand_content_query_text(brand: dict) -> str:
    prefs = brand["creator_preferences"]
    return (
        f"The brand is looking for creators aligned with "
        f"{', '.join(prefs['niche_alignment'])}. "
        f"Content should be {prefs['content_style']}."
    )


def brand_values_query_text(brand: dict) -> str:
    return (
        "The brand strongly believes in the following values: "
        + ", ".join(brand["brand_values"])
        + "."
    )


def brand_audience_query_text(brand: dict) -> str:
    ta = brand["target_audience"]
    return (
        f"The brand targets {ta['age_range']} year old urban Indian families, "
        f"primarily {ta['primary_gender']}. "
        f"Audience is interested in {', '.join(ta['interests'])}. "
        f"Psychographics: {ta['psychographics']}."
    )
