"""
Material Matcher Service

Matches takeoff items from parsed plans to company's material catalog.
Uses fuzzy string matching and ML-based suggestions.
"""

import logging
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz, process

from app.models.material import Material
from app.models.estimation import TakeoffItem

logger = logging.getLogger(__name__)


class MaterialMatcher:
    """
    Match takeoff items to material catalog

    Uses multiple strategies:
    1. Exact product code match
    2. Fuzzy description matching
    3. Category-aware matching
    4. Unit-aware matching
    """

    def __init__(self, db: Session, company_id: str):
        self.db = db
        self.company_id = company_id
        self._materials_cache = None

    def _load_materials(self) -> List[Material]:
        """Load and cache all active materials for the company"""
        if self._materials_cache is None:
            self._materials_cache = self.db.query(Material).filter(
                Material.company_id == self.company_id,
                Material.is_active == True
            ).all()
        return self._materials_cache

    def match_item(
        self,
        description: str,
        quantity: float = None,
        unit: str = None,
        category_hint: str = None,
        threshold: int = 70
    ) -> List[Dict]:
        """
        Find matching materials for a takeoff item

        Args:
            description: Item description from takeoff
            quantity: Item quantity (optional)
            unit: Item unit (optional, helps narrow matches)
            category_hint: Category hint from context (optional)
            threshold: Minimum fuzzy match score (0-100)

        Returns:
            List of matches sorted by confidence, each containing:
            - material: Material object
            - confidence: Match confidence (0.0-1.0)
            - match_type: How it was matched (exact, fuzzy, category)
            - reasoning: Why this match was suggested
        """
        materials = self._load_materials()

        if not materials:
            logger.warning(f"No materials found for company {self.company_id}")
            return []

        matches = []

        # Strategy 1: Try exact product code match
        # Check if description contains a product code pattern
        exact_match = self._find_exact_code_match(description, materials)
        if exact_match:
            matches.append({
                "material": exact_match,
                "confidence": 1.0,
                "match_type": "exact_code",
                "reasoning": f"Exact product code match"
            })
            return matches  # Exact match found, return immediately

        # Strategy 2: Fuzzy description matching
        fuzzy_matches = self._fuzzy_match_description(
            description, materials, unit, category_hint, threshold
        )
        matches.extend(fuzzy_matches)

        # Sort by confidence (descending)
        matches.sort(key=lambda x: x["confidence"], reverse=True)

        # Return top 5 matches
        return matches[:5]

    def _find_exact_code_match(
        self,
        description: str,
        materials: List[Material]
    ) -> Optional[Material]:
        """Try to find exact product code in description"""
        desc_upper = description.upper().strip()

        for material in materials:
            # Check if product code appears in description
            if material.product_code.upper() in desc_upper:
                logger.info(f"Exact code match: {material.product_code}")
                return material

        return None

    def _fuzzy_match_description(
        self,
        description: str,
        materials: List[Material],
        unit: str = None,
        category_hint: str = None,
        threshold: int = 50
    ) -> List[Dict]:
        """
        Fuzzy match item description to material descriptions

        Uses fuzzywuzzy library for string similarity
        """
        matches = []

        # Normalize description
        desc_normalized = self._normalize_description(description)
        
        # Extract lumber dimensions for special matching
        lumber_dims = self._extract_lumber_dimensions(description)

        for material in materials:
            # Skip if category doesn't match (if provided and confident)
            if category_hint and material.category != category_hint:
                # Don't skip entirely, just reduce confidence
                category_penalty = 0.15
            else:
                category_penalty = 0.0

            # Calculate multiple similarity scores
            mat_desc_normalized = self._normalize_description(material.description)

            # Partial ratio: good for substrings
            partial_score = fuzz.partial_ratio(desc_normalized, mat_desc_normalized)

            # Token sort ratio: good for different word orders
            token_sort_score = fuzz.token_sort_ratio(desc_normalized, mat_desc_normalized)

            # Token set ratio: ignores duplicate words
            token_set_score = fuzz.token_set_ratio(desc_normalized, mat_desc_normalized)

            # Take the best score
            best_score = max(partial_score, token_sort_score, token_set_score)
            
            # Bonus for lumber dimension match (e.g., "2x4" in both)
            if lumber_dims:
                mat_lumber_dims = self._extract_lumber_dimensions(material.description)
                if mat_lumber_dims and lumber_dims == mat_lumber_dims:
                    best_score = min(100, best_score + 25)

            if best_score >= threshold:
                # Convert 0-100 score to 0-1 confidence
                confidence = (best_score / 100.0) - category_penalty

                # Bonus for unit match
                if unit and material.unit and material.unit.upper() == unit.upper():
                    confidence = min(1.0, confidence + 0.1)

                matches.append({
                    "material": material,
                    "confidence": max(0.0, confidence),
                    "match_type": "fuzzy",
                    "reasoning": f"Description similarity: {best_score}%"
                })

        return matches

    def _normalize_description(self, text: str) -> str:
        """Normalize description for better matching"""
        # Convert to uppercase
        text = text.upper()

        # Common replacements
        replacements = {
            "NOMINAL": "",
            "ACTUAL": "",
            "#": "NO",
            '"': "INCH",
            "'": "FOOT",
            "X": " ",
            "-": " ",
            "/": " ",
            "STUDS": "STUD",
            "WALL FRAMING": "",
            "EXTERIOR WALLS": "",
            "FLOOR JOISTS": "JOIST",
            "RIDGE BEAM": "RIDGE",
            "SHEATHING": "",
        }

        for old, new in replacements.items():
            text = text.replace(old, new)

        # Remove extra spaces
        text = " ".join(text.split())

        return text

    def _extract_lumber_dimensions(self, text: str) -> Optional[str]:
        """Extract lumber dimensions like 2x4, 2x6, 2x10 from text"""
        import re
        text_upper = text.upper()
        # Match patterns like 2x4, 2x6, 2x10, 2x12
        match = re.search(r'(\d+)\s*[Xx]\s*(\d+)', text_upper)
        if match:
            return f"{match.group(1)}X{match.group(2)}"
        return None

    def match_multiple_items(
        self,
        takeoff_items: List[TakeoffItem],
        threshold: int = 70
    ) -> Dict[str, List[Dict]]:
        """
        Match multiple takeoff items at once

        Returns:
            Dictionary mapping takeoff_item.id to list of material matches
        """
        results = {}

        for item in takeoff_items:
            # Try to infer category from notes or label
            category_hint = self._infer_category(item.label, item.notes)

            matches = self.match_item(
                description=item.label,
                quantity=float(item.qty) if item.qty else None,
                unit=item.unit,
                category_hint=category_hint,
                threshold=threshold
            )

            results[str(item.id)] = matches

        return results

    def _infer_category(self, label: str, notes: str = None) -> Optional[str]:
        """
        Infer material category from item label/notes

        Uses keyword matching to guess category
        """
        text = (label + " " + (notes or "")).upper()

        # Category keywords
        category_keywords = {
            "Foundation": ["FOUNDATION", "FOOTING", "SLAB", "CONCRETE", "REBAR", "ANCHOR"],
            "Walls": ["WALL", "STUD", "PLATE", "BEAM", "JOIST", "FRAMING"],
            "Roofing": ["ROOF", "SHINGLE", "RIDGE", "VALLEY", "DRIP EDGE"],
            "Siding": ["SIDING", "HARDIE", "LAP", "TRIM", "SOFFIT"],
            "Insulation": ["INSUL", "R-13", "R-30", "BATT"],
            "Drywall": ["DRYWALL", "GYPSUM", "SHEETROCK"],
            "Hardware": ["HANGER", "TIE", "BOLT", "SCREW", "NAIL", "LOCK"],
            "Trim": ["TRIM", "CROWN", "BASE", "CASING", "MOLDING"],
        }

        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category

        return None

    def get_match_summary(self, takeoff_item_id: str) -> Dict:
        """
        Get summary statistics for a matched item

        Returns:
            - total_matches: Number of matches found
            - best_match: Highest confidence match
            - confidence_distribution: Count by confidence range
        """
        # This would query saved matches from database
        # For now, just a placeholder structure
        return {
            "total_matches": 0,
            "best_match": None,
            "confidence_distribution": {
                "high": 0,  # >= 0.8
                "medium": 0,  # 0.6-0.8
                "low": 0,  # < 0.6
            }
        }


def match_takeoff_to_materials(
    db: Session,
    company_id: str,
    takeoff_items: List[TakeoffItem],
    threshold: int = 70
) -> Dict[str, List[Dict]]:
    """
    Convenience function to match takeoff items to materials

    Args:
        db: Database session
        company_id: Company ID
        takeoff_items: List of takeoff items to match
        threshold: Minimum fuzzy match score (0-100)

    Returns:
        Dictionary mapping takeoff_item.id to list of material matches
    """
    matcher = MaterialMatcher(db, company_id)
    return matcher.match_multiple_items(takeoff_items, threshold)
