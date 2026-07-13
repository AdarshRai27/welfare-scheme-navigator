"""Graph node forward-chaining related schemes based on eligibility matching."""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


async def forward_chain_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Suggests related schemes if a base/master scheme eligibility is matched.

    Args:
        state: Shared graph state dictionary.

    Returns:
        State updates containing suggested_schemes list.
    """
    eligible = state.get("eligible_schemes", [])
    suggested: List[Dict[str, Any]] = []

    # Check if PM-Kisan is qualified
    has_pm_kisan = any("pm kisan" in s["name"].lower() or "pm-kisan" in s["name"].lower() for s in eligible)

    if has_pm_kisan:
        logger.info(
            "[AGENT forward_chain] PM-Kisan eligibility detected. Forward-chaining related agricultural schemes."
        )
        # Suggest Kisan Credit Card (KCC)
        suggested.append(
            {
                "name": "Kisan Credit Card (KCC)",
                "description": "Concessional short-term credit limit to meet agricultural requirements.",
                "eligibility_rules": {},
                "source_url": "https://pmkisan.gov.in",
            }
        )
        # Suggest Pradhan Mantri Fasal Bima Yojana (Crop Insurance)
        suggested.append(
            {
                "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
                "description": "Yield-based crop insurance coverage against production losses.",
                "eligibility_rules": {},
                "source_url": "https://pmfby.gov.in",
            }
        )

    return {"suggested_schemes": suggested}
