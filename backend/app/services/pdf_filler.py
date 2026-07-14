"""Service helper to auto-fill government welfare scheme application forms."""

import json
import logging
import os
from typing import Any, Dict

logger = logging.getLogger(__name__)


class FormFillerService:
    """Pre-fills application forms using demographic user attributes."""

    def __init__(self, output_dir: str = "backend/static/forms") -> None:
        """Initializes the output directory paths for static forms.

        Args:
            output_dir: Local path target to output form files.
        """
        self.output_dir = output_dir
        # Guarantee output directories exist
        os.makedirs(self.output_dir, exist_ok=True)

    def fill_form(self, scheme_name: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Maps user profile properties and saves pre-filled structured files.

        Args:
            scheme_name: Government target scheme name.
            profile: Dictionary containing user properties (name, Aadhaar, etc.).

        Returns:
            Dictionary containing filled form details and web URL.
        """
        sanitized_name = (
            scheme_name.lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("(", "")
            .replace(")", "")
        )
        filename = f"{sanitized_name}_filled.json"
        filepath = os.path.join(self.output_dir, filename)

        # Pre-fill layout matching general eligibility items
        prefilled_fields = {
            "scheme_name": scheme_name,
            "applicant_name": profile.get("name", "N/A"),
            "identity_aadhaar": profile.get("aadhaar_number", "N/A"),
            "annual_income_inr": profile.get("annual_income", "N/A"),
            "landholdings_hectares": profile.get("land_size_hectares", "N/A"),
            "state_residence": profile.get("state", "N/A"),
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(prefilled_fields, f, indent=4)
            logger.info(
                f"[FORM FILLER] Generated pre-filled schema form: {filepath}"
            )
        except Exception as err:
            logger.error(f"Failed writing pre-filled form file: {err}")

        return {
            "scheme_name": scheme_name,
            "status": "pre-filled",
            "fields": prefilled_fields,
            "download_url": f"/static/forms/{filename}",
        }
