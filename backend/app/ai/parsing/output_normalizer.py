"""
Output Normalizer

Ensures all parsing strategies return consistent schema regardless of source.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class OutputNormalizer:
    """
    Normalizes output from different parsing strategies to consistent schema
    """

    @staticmethod
    def normalize(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize parsed data to standard schema

        Args:
            data: Raw parsed data from any strategy

        Returns:
            Normalized data with consistent schema
        """
        if not data:
            return OutputNormalizer._empty_schema()

        normalized = {
            "bid_items": OutputNormalizer._normalize_bid_items(
                data.get("bid_items", [])
            ),
            "specifications": OutputNormalizer._normalize_specifications(
                data.get("specifications", [])
            ),
            "project_info": OutputNormalizer._normalize_project_info(
                data.get("project_info", {})
            ),
            "materials": OutputNormalizer._normalize_materials(
                data.get("materials", [])
            ),
        }

        # Preserve raw_text if present (from OCR)
        if "raw_text" in data:
            normalized["raw_text"] = data["raw_text"]

        return normalized

    @staticmethod
    def _empty_schema() -> Dict[str, Any]:
        """Return empty schema structure"""
        return {
            "bid_items": [],
            "specifications": [],
            "project_info": {
                "name": None,
                "location": None,
                "bid_date": None,
            },
            "materials": [],
        }

    @staticmethod
    def _normalize_bid_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize bid items to standard schema

        Standard fields:
        - item_number: str
        - description: str
        - quantity: float
        - unit: str
        - unit_price: float (optional)
        """
        normalized = []

        for item in items:
            if not item or not isinstance(item, dict):
                continue

            # Extract and normalize fields
            normalized_item = {
                "item_number": OutputNormalizer._normalize_string(
                    item.get("item_number") or item.get("number") or item.get("id")
                ),
                "description": OutputNormalizer._normalize_string(
                    item.get("description") or item.get("desc") or item.get("name")
                ),
                "quantity": OutputNormalizer._normalize_number(
                    item.get("quantity") or item.get("qty") or item.get("amount")
                ),
                "unit": OutputNormalizer._normalize_string(
                    item.get("unit") or item.get("units") or item.get("uom")
                ),
                "unit_price": OutputNormalizer._normalize_number(
                    item.get("unit_price") or item.get("price") or item.get("cost")
                ),
            }

            # Only include if has meaningful data
            if normalized_item["item_number"] or normalized_item["description"]:
                normalized.append(normalized_item)

        return normalized

    @staticmethod
    def _normalize_specifications(specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize specifications to standard schema

        Standard fields:
        - code: str
        - description: str
        """
        normalized = []

        for spec in specs:
            if not spec or not isinstance(spec, dict):
                continue

            normalized_spec = {
                "code": OutputNormalizer._normalize_string(
                    spec.get("code") or spec.get("spec_code") or spec.get("specification")
                ),
                "description": OutputNormalizer._normalize_string(
                    spec.get("description") or spec.get("desc") or spec.get("title")
                ),
            }

            # Only include if has code
            if normalized_spec["code"]:
                normalized.append(normalized_spec)

        return normalized

    @staticmethod
    def _normalize_project_info(info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize project info to standard schema

        Standard fields:
        - name: str
        - location: str
        - bid_date: str
        """
        if not info or not isinstance(info, dict):
            info = {}

        return {
            "name": OutputNormalizer._normalize_string(
                info.get("name") or info.get("project_name") or info.get("title")
            ),
            "location": OutputNormalizer._normalize_string(
                info.get("location") or info.get("site") or info.get("address")
            ),
            "bid_date": OutputNormalizer._normalize_string(
                info.get("bid_date") or info.get("date") or info.get("due_date")
            ),
        }

    @staticmethod
    def _normalize_materials(materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize materials to standard schema

        Standard fields:
        - name: str
        - quantity: float
        - unit: str
        - specification: str (optional)
        """
        normalized = []

        for material in materials:
            if not material or not isinstance(material, dict):
                continue

            normalized_material = {
                "name": OutputNormalizer._normalize_string(
                    material.get("name") or material.get("material") or material.get("description")
                ),
                "quantity": OutputNormalizer._normalize_number(
                    material.get("quantity") or material.get("qty") or material.get("amount")
                ),
                "unit": OutputNormalizer._normalize_string(
                    material.get("unit") or material.get("units") or material.get("uom")
                ),
                "specification": OutputNormalizer._normalize_string(
                    material.get("specification") or material.get("spec") or material.get("spec_code")
                ),
            }

            # Only include if has name
            if normalized_material["name"]:
                normalized.append(normalized_material)

        return normalized

    @staticmethod
    def _normalize_string(value: Any) -> Optional[str]:
        """Normalize value to string or None"""
        if value is None:
            return None

        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None

        # Convert other types to string
        try:
            return str(value).strip() or None
        except Exception:
            return None

    @staticmethod
    def _normalize_number(value: Any) -> Optional[float]:
        """Normalize value to float or None"""
        if value is None:
            return None

        # Already a number
        if isinstance(value, (int, float)):
            return float(value)

        # Try to parse string
        if isinstance(value, str):
            # Remove common formatting
            cleaned = value.strip().replace(",", "").replace("$", "")

            try:
                return float(cleaned)
            except ValueError:
                return None

        return None

    @staticmethod
    def validate_schema(data: Dict[str, Any]) -> bool:
        """
        Validate that data conforms to expected schema

        Args:
            data: Data to validate

        Returns:
            True if valid schema
        """
        if not isinstance(data, dict):
            return False

        # Check required top-level keys
        required_keys = ["bid_items", "specifications", "project_info", "materials"]
        for key in required_keys:
            if key not in data:
                logger.warning(f"Missing required key: {key}")
                return False

        # Check types
        if not isinstance(data["bid_items"], list):
            logger.warning("bid_items must be a list")
            return False

        if not isinstance(data["specifications"], list):
            logger.warning("specifications must be a list")
            return False

        if not isinstance(data["project_info"], dict):
            logger.warning("project_info must be a dict")
            return False

        if not isinstance(data["materials"], list):
            logger.warning("materials must be a list")
            return False

        return True
