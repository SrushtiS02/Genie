# --------- utils.py ---------
import random

def run_ab_test_simulation(variations):
    """
    Simulate A/B test scoring for multiple caption variations.
    Uses provided scores if available, otherwise assigns a plausible random value.
    Recommends the highest-scoring option.
    """
    for v in variations:
        if v.get("score") is None:
            v["score"] = round(random.uniform(6.5, 9.2), 1)
        v["why"] = v.get("why", "Likely to drive strong engagement for the target audience.")
    # Recommend the highest
    if variations:
        top_idx = max(range(len(variations)), key=lambda i: variations[i]['score'] or 0)
        for idx, v in enumerate(variations):
            v["recommended"] = (idx == top_idx)
    return variations

def format_score(score):
    """
    Format the engagement score for display (e.g., '8.3/10').
    """
    if score is None:
        return "N/A"
    return f"{score}/10"

def get_supported_languages():
    """
    Returns a list of localization languages supported for campaign translations.
    Focus is on European markets and Hindi.
    """
    return [
        "English",
        "Spanish",
        "German",
        "French",
        "Italian",
        "Dutch",
        "Portuguese",
        "Polish",
        "Hindi"
    ]
