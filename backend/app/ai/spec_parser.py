"""
Specification Parser

Parses specification documents using text extraction and LLM structuring.

Different from plan parsing:
- Plans: Vision models (tables, diagrams, spatial layout)
- Specs: Text extraction + LLM (dense text, hierarchical structure)
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional

from app.ai.config import anthropic_client, openai_client, is_ai_available
from app.ai.parsing.utils.text_extraction import text_extractor

logger = logging.getLogger(__name__)


class SpecificationParser:
    """
    Parse specification documents with text extraction and LLM structuring
    """

    def __init__(self):
        self.anthropic = anthropic_client
        self.openai = openai_client
        self.text_extractor = text_extractor

    async def parse_specification(
        self,
        pdf_path: Path,
        max_pages: int = 50,
        use_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Parse a specification document

        Args:
            pdf_path: Path to specification PDF
            max_pages: Maximum pages to process (specs can be long)
            use_ai: Whether to use AI for structuring

        Returns:
            Dictionary with structured specification data
        """
        start_time = time.time()
        logger.info(f"Parsing specification: {pdf_path}")

        try:
            # Step 1: Extract text from PDF
            page_texts, extraction_method = self.text_extractor.extract_text(
                pdf_path, max_pages=max_pages
            )

            if not page_texts:
                return {
                    "success": False,
                    "error": "Failed to extract text from PDF",
                    "method": "text_extraction"
                }

            # Combine all pages
            full_text = "\n\n".join(page_texts)
            total_chars = len(full_text)

            logger.info(
                f"Extracted text: {len(page_texts)} pages, "
                f"{total_chars} characters using {extraction_method}"
            )

            # Check if scanned document
            is_scanned = extraction_method == "ocr"

            # Step 2: Structure with LLM (if AI available and requested)
            if use_ai and is_ai_available()["any"]:
                structured_data = await self._structure_with_llm(
                    full_text, page_texts
                )

                if structured_data:
                    processing_time = int((time.time() - start_time) * 1000)

                    return {
                        "success": True,
                        "data": structured_data,
                        "pages_analyzed": len(page_texts),
                        "method": "text_extraction_llm",
                        "extraction_method": extraction_method,
                        "is_scanned": is_scanned,
                        "processing_time_ms": processing_time,
                        "character_count": total_chars,
                    }

            # Fallback: Return raw text with basic structure
            processing_time = int((time.time() - start_time) * 1000)

            return {
                "success": True,
                "data": {
                    "raw_text": full_text,
                    "page_texts": page_texts,
                    "divisions": [],
                    "sections": [],
                    "requirements": [],
                    "standards": [],
                },
                "pages_analyzed": len(page_texts),
                "method": "text_extraction_only",
                "extraction_method": extraction_method,
                "is_scanned": is_scanned,
                "processing_time_ms": processing_time,
                "character_count": total_chars,
            }

        except Exception as e:
            logger.error(f"Failed to parse specification: {e}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)

            return {
                "success": False,
                "error": str(e),
                "method": "specification",
                "processing_time_ms": processing_time,
            }

    async def _structure_with_llm(
        self,
        full_text: str,
        page_texts: list
    ) -> Optional[Dict[str, Any]]:
        """
        Use LLM to structure specification text

        Args:
            full_text: Complete specification text
            page_texts: List of page texts

        Returns:
            Structured specification data or None if failed
        """
        # Limit text length for LLM (most models have token limits)
        # ~4000 tokens = ~16000 characters (conservative estimate)
        max_chars = 50000  # Allow up to 50k characters
        text_to_analyze = full_text[:max_chars]

        if len(full_text) > max_chars:
            logger.warning(
                f"Text truncated from {len(full_text)} to {max_chars} characters"
            )

        prompt = f"""You are analyzing a construction specification document. Extract and structure the information.

Specification documents typically follow CSI MasterFormat with divisions and sections.

Analyze this specification text and extract:

1. **Document Structure**:
   - Division number (e.g., "Division 03", "03")
   - Division title (e.g., "Concrete")
   - Section number (e.g., "03 31 00", "Section 03310")
   - Section title (e.g., "Structural Concrete")

2. **Document Parts** (if present):
   - PART 1 - GENERAL (administrative, references, submittals)
   - PART 2 - PRODUCTS (materials, equipment, mixes)
   - PART 3 - EXECUTION (installation, quality control)

3. **Referenced Standards** (extract ALL mentioned):
   - Standard code (e.g., "ASTM C150", "AASHTO M31")
   - Standard title if mentioned
   - Context where it's referenced

4. **Material Requirements**:
   - Material name
   - Required properties (strength, grade, type)
   - Applicable standards
   - Quality requirements

5. **Key Requirements**:
   - Installation procedures
   - Quality control measures
   - Testing requirements
   - Acceptance criteria

Return structured JSON format:
{{
  "division_number": "03",
  "division_title": "Concrete",
  "section_number": "03 31 00",
  "section_title": "Structural Concrete",
  "parts": {{
    "part_1_general": "Summary of Part 1...",
    "part_2_products": "Summary of Part 2...",
    "part_3_execution": "Summary of Part 3..."
  }},
  "standards": [
    {{
      "code": "ASTM C150",
      "title": "Standard Specification for Portland Cement",
      "context": "Cement shall conform to ASTM C150 Type I or Type II"
    }}
  ],
  "materials": [
    {{
      "name": "Portland Cement",
      "properties": "Type I or Type II",
      "standard": "ASTM C150",
      "requirements": "Air-entrained, 4000 psi minimum compressive strength"
    }}
  ],
  "requirements": [
    {{
      "type": "installation",
      "description": "Concrete placement and consolidation procedures",
      "details": "Place concrete in continuous operation..."
    }},
    {{
      "type": "quality_control",
      "description": "Testing requirements",
      "details": "Submit compressive strength test results..."
    }}
  ]
}}

If information is not found, use null or empty arrays.

TEXT TO ANALYZE:
{text_to_analyze}

Return ONLY the JSON, no other text."""

        try:
            # Try Claude first (better at understanding structured documents)
            if self.anthropic:
                logger.info("Structuring with Claude")
                structured_data = await self._structure_with_claude(prompt)
                if structured_data:
                    return structured_data

            # Try OpenAI as fallback
            if self.openai:
                logger.info("Structuring with OpenAI")
                structured_data = await self._structure_with_openai(prompt)
                if structured_data:
                    return structured_data

            logger.warning("No AI service available for structuring")
            return None

        except Exception as e:
            logger.error(f"LLM structuring failed: {e}")
            return None

    async def _structure_with_claude(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Structure with Claude"""
        try:
            claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

            message = self.anthropic.messages.create(
                model=claude_model,
                max_tokens=16000,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            response_text = message.content[0].text

            # Parse JSON response
            return self._parse_json_response(response_text)

        except Exception as e:
            logger.error(f"Claude structuring failed: {e}")
            return None

    async def _structure_with_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Structure with OpenAI"""
        try:
            openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")

            response = self.openai.chat.completions.create(
                model=openai_model,
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                max_tokens=16000,
                temperature=0.0,
            )

            response_text = response.choices[0].message.content

            # Parse JSON response
            return self._parse_json_response(response_text)

        except Exception as e:
            logger.error(f"OpenAI structuring failed: {e}")
            return None

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from LLM response, handling markdown code blocks"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try extracting from markdown
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                if json_end > json_start:
                    json_str = text[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
            elif "```" in text:
                # Try generic code block
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                if json_end > json_start:
                    json_str = text[json_start:json_end].strip()
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass

            logger.warning("Could not parse JSON from LLM response")
            return None


# Singleton instance
spec_parser = SpecificationParser()
