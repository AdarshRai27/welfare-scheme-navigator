"""Graph node evaluating structured eligibility rules against user profile."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


async def evaluate_rules_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluates candidate schemes against user's demographic profile.

    Args:
        state: Shared graph state dictionary.

    Returns:
        State updates containing eligible_schemes list.
    """
    profile = state.get("extracted_profile", {})
    candidates = state.get("candidate_schemes", [])

    eligible: List[Dict[str, Any]] = []

    for scheme in candidates:
        rules = scheme.get("eligibility_rules", {})
        is_eligible = True

        # 1. Evaluate Age Bounds
        if "min_age" in rules and "age" in profile:
            if profile["age"] < rules["min_age"]:
                is_eligible = False
        if "max_age" in rules and "age" in profile:
            if profile["age"] > rules["max_age"]:
                is_eligible = False

        # 2. Evaluate Income Limits
        if "income_limit" in rules and "annual_income" in profile:
            if profile["annual_income"] > rules["income_limit"]:
                is_eligible = False

        # 3. Evaluate Land Size Thresholds
        if "land_size_limit" in rules and "land_size_hectares" in profile:
            if profile["land_size_hectares"] > rules["land_size_limit"]:
                is_eligible = False

        # 4. Evaluate Caste Category Matches
        if "caste_categories" in rules and "caste_category" in profile:
            allowed_castes = [c.lower() for c in rules["caste_categories"]]
            if profile["caste_category"].lower() not in allowed_castes:
                is_eligible = False

        if is_eligible:
            eligible.append(scheme)
            logger.debug(f"[AGENT evaluate_rules] Scheme '{scheme['name']}' passes rules evaluation.")
        else:
            logger.debug(
                f"[AGENT evaluate_rules] Scheme '{scheme['name']}' fails rules evaluation."
            )

    logger.info(
        f"[AGENT evaluate_rules] Filtered {len(eligible)}/{len(candidates)} eligible schemes."
    )
    return {"eligible_schemes": eligible}
