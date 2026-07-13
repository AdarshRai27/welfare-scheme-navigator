"""Form auto-fill service helper (placeholder)."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FormAutoFillService:
    """Mock service to pre-fill scheme forms using extracted user data."""

    def auto_fill_form(
        self, scheme_id: str, user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Pre-fill application forms with user profile fields.

        Args:
            scheme_id: ID of targeted welfare scheme.
            user_profile: Extracted fields from user documents.

        Returns:
            Pre-filled application form fields.
        """
        logger.info(
            f"[MOCK FORM AUTOFILL] Auto-filling form for scheme={scheme_id}"
        )
        return {
            "scheme_id": scheme_id,
            "form_status": "partially_filled",
            "filled_fields": {
                "applicant_name": user_profile.get("name", ""),
                "state": user_profile.get("state", "Uttar Pradesh"),
                "aadhaar_no": user_profile.get("aadhaar_number", ""),
                "income": user_profile.get("annual_income", ""),
            },
        }
