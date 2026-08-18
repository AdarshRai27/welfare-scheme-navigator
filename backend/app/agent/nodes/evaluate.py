"""Graph node evaluating structured eligibility rules against user profile."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def calculate_benefit_priority(scheme: Dict[str, Any]) -> int:
    """Calculates impact score to rank direct cash transfers and essential health benefits first."""
    name = (scheme.get("name") or "").lower()
    category = (scheme.get("category") or "").lower()
    desc = (scheme.get("description") or "").lower()

    # Tier 1 (100): Direct Income Transfers & Social Pensions
    if any(k in name or k in desc for k in ["kisan samman", "old age pension", "vridha", "senior pension", "ladli behna", "matru vandana"]):
        return 100
    # Tier 2 (85): Essential Cashless Healthcare
    if "ayushman" in name or "jan arogya" in name or "health" in category:
        return 85
    # Tier 3 (70): Housing & Solar Infrastructure Subsidies
    if "surya ghar" in name or "awas" in name or "pmay" in name:
        return 70
    # Tier 4 (55): Concessional Credit & Farmer Subsidies
    if "fasal bima" in name or "credit card" in name or "kcc" in name or "mudra" in name or "svanidhi" in name:
        return 55
    # Tier 5 (40): Education & Scholarships
    if "scholarship" in name or "education" in category:
        return 40

    return 30


async def evaluate_rules_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates candidate schemes against user's demographic profile with strict multi-constraint validation.

    Args:
        state: Shared graph state dictionary.

    Returns:
        State updates containing eligible_schemes list and disqualification audit metadata.
    """
    profile = state.get("extracted_profile", {})
    candidates = state.get("candidate_schemes", [])

    eligible: List[Dict[str, Any]] = []
    disqualified: List[Dict[str, Any]] = []

    for scheme in candidates:
        rules = scheme.get("eligibility_rules", {})
        scheme_state = scheme.get("state")
        is_eligible = True
        failed_reasons = []

        # 1. Evaluate Age Bounds
        user_age = profile.get("age")
        if user_age is not None:
            if "min_age" in rules and user_age < rules["min_age"]:
                is_eligible = False
                failed_reasons.append(f"Requires minimum age {rules['min_age']} (user is {user_age})")
            if "max_age" in rules and user_age > rules["max_age"]:
                is_eligible = False
                failed_reasons.append(f"Requires maximum entry age {rules['max_age']} (user is {user_age})")

        # 2. Evaluate Income Limits
        annual_income = profile.get("annual_income")
        if annual_income is not None and "income_limit" in rules:
            if annual_income > rules["income_limit"]:
                is_eligible = False
                failed_reasons.append(f"Income ₹{annual_income:,} exceeds limit ₹{rules['income_limit']:,}")

        # 3. Evaluate Land Size Thresholds
        land_limit = rules.get("max_land_size_hectares") or rules.get("land_size_limit")
        user_land = profile.get("land_size_hectares")
        if land_limit is not None and user_land is not None:
            if user_land > land_limit:
                is_eligible = False
                failed_reasons.append(f"Land {user_land} Ha exceeds ceiling {land_limit} Ha")

        # 4. Evaluate State / Domicile Restrictions
        user_state = profile.get("state")
        if scheme_state and user_state:
            s_state = scheme_state.lower().strip()
            u_state = user_state.lower().strip()
            if s_state not in u_state and u_state not in s_state:
                is_eligible = False
                failed_reasons.append(f"Restricted to residents of {scheme_state} (user is in {user_state})")

        # 5. Evaluate Caste Category Matches
        if "caste_categories" in rules and "caste_category" in profile:
            allowed_castes = [c.lower() for c in rules["caste_categories"]]
            if profile["caste_category"].lower() not in allowed_castes:
                is_eligible = False
                failed_reasons.append(f"Restricted to categories: {', '.join(rules['caste_categories'])}")

        # 6. Evaluate Gender Match
        if "gender" in rules and "gender" in profile:
            if profile["gender"].lower() != rules["gender"].lower():
                is_eligible = False
                failed_reasons.append(f"Restricted to {rules['gender']} applicants")

        if is_eligible:
            eligible.append(scheme)
            logger.debug(f"[AGENT evaluate_rules] Scheme '{scheme['name']}' passes rules evaluation.")
        else:
            disqualified.append({
                "scheme_name": scheme["name"],
                "reasons": failed_reasons,
            })
            logger.debug(
                f"[AGENT evaluate_rules] Scheme '{scheme['name']}' fails rules: {failed_reasons}"
            )

    # Sort eligible schemes by Benefit Impact Priority
    eligible.sort(key=calculate_benefit_priority, reverse=True)

    logger.info(
        f"[AGENT evaluate_rules] Filtered {len(eligible)}/{len(candidates)} eligible schemes (Disqualified: {len(disqualified)})."
    )
    return {
        "eligible_schemes": eligible,
        "disqualified_schemes": disqualified,
    }
