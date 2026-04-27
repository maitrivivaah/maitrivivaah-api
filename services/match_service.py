"""
MaitriVivaah Match Scoring Engine
----------------------------------
Scores compatibility between two profiles on a 0–100 scale.
Weights are tunable — adjust based on user feedback over time.
"""

WEIGHTS = {
    "jain_sect":        20,
    "age_gap":          15,
    "location":         15,
    "education":        10,
    "income":           10,
    "height":           10,
    "family_values":    10,
    "partner_prefs":    10,
}


def score_match(seeker: dict, candidate: dict) -> int:
    """
    Returns a 0–100 compatibility score between two profile dicts.
    seeker   — the logged-in user's profile
    candidate — the profile being evaluated
    """
    score = 0

    # 1. Jain sect match (20 pts)
    if seeker.get("jain_sect") == candidate.get("jain_sect"):
        score += WEIGHTS["jain_sect"]
    elif seeker.get("jain_sect") and candidate.get("jain_sect"):
        score += 5  # Partial credit — both are Jain

    # 2. Age gap (15 pts — prefer ±5 years)
    seeker_age   = seeker.get("age", 0)
    candidate_age = candidate.get("age", 0)
    if seeker_age and candidate_age:
        gap = abs(seeker_age - candidate_age)
        if gap <= 2:
            score += WEIGHTS["age_gap"]
        elif gap <= 5:
            score += 10
        elif gap <= 8:
            score += 5

    # 3. Location match (15 pts)
    if seeker.get("city") == candidate.get("city"):
        score += WEIGHTS["location"]
    elif seeker.get("state") == candidate.get("state"):
        score += 8
    elif seeker.get("country") == candidate.get("country"):
        score += 3

    # 4. Education level match (10 pts)
    edu_order = ["high_school", "diploma", "bachelors", "masters", "phd"]
    seeker_edu = seeker.get("education_level", "")
    cand_edu   = candidate.get("education_level", "")
    if seeker_edu in edu_order and cand_edu in edu_order:
        diff = abs(edu_order.index(seeker_edu) - edu_order.index(cand_edu))
        if diff == 0:
            score += WEIGHTS["education"]
        elif diff == 1:
            score += 6
        elif diff == 2:
            score += 3

    # 5. Income compatibility (10 pts)
    seeker_inc = seeker.get("annual_income", "")
    cand_inc   = candidate.get("annual_income", "")
    if seeker_inc and cand_inc and seeker_inc == cand_inc:
        score += WEIGHTS["income"]
    elif seeker_inc and cand_inc:
        score += 4  # Both employed but different brackets

    # 6. Height preference (10 pts — only if seeker has preferences set)
    h_min = seeker.get("partner_height_min")
    h_max = seeker.get("partner_height_max")
    cand_h = candidate.get("height_cm")
    if h_min and h_max and cand_h:
        if h_min <= cand_h <= h_max:
            score += WEIGHTS["height"]
    else:
        score += WEIGHTS["height"] // 2  # No preference = neutral

    # 7. Family values (10 pts)
    if seeker.get("family_values") == candidate.get("family_values"):
        score += WEIGHTS["family_values"]
    elif seeker.get("family_values") and candidate.get("family_values"):
        score += 4

    # 8. Partner preferences met (10 pts)
    prefs_score = 0
    pref_checks = 0

    seeker_partner_sect = seeker.get("partner_jain_sect")
    if seeker_partner_sect:
        pref_checks += 1
        if candidate.get("jain_sect") in seeker_partner_sect:
            prefs_score += 1

    seeker_partner_edu = seeker.get("partner_education")
    if seeker_partner_edu:
        pref_checks += 1
        if candidate.get("education_level") in seeker_partner_edu:
            prefs_score += 1

    seeker_partner_loc = seeker.get("partner_location")
    if seeker_partner_loc:
        pref_checks += 1
        if candidate.get("city") in seeker_partner_loc or candidate.get("state") in seeker_partner_loc:
            prefs_score += 1

    if pref_checks > 0:
        score += int((prefs_score / pref_checks) * WEIGHTS["partner_prefs"])
    else:
        score += WEIGHTS["partner_prefs"] // 2

    return min(score, 100)


def get_match_label(score: int) -> str:
    """Human-readable label for a compatibility score."""
    if score >= 85:
        return "Excellent Match"
    elif score >= 70:
        return "Very Good Match"
    elif score >= 55:
        return "Good Match"
    elif score >= 40:
        return "Potential Match"
    else:
        return "Low Compatibility"
