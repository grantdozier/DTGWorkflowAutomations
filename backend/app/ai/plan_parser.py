import logging
from pathlib import Path
from typing import Dict, List, Optional
import json

from app.ai.config import anthropic_client, openai_client, is_ai_available
from app.ai.ocr_service import ocr_service

logger = logging.getLogger(__name__)


class PlanParser:
    """
    Parse construction plans and extract bid items, quantities, and specifications
    Uses Claude 3.5 Sonnet vision API
    """

    def __init__(self):
        self.anthropic = anthropic_client
        self.openai = openai_client

    async def parse_plan_with_claude(
        self,
        pdf_path: Path,
        max_pages: int = 5
    ) -> Dict:
        """
        Parse construction plan using Claude 3.5 Sonnet vision

        Args:
            pdf_path: Path to PDF plan
            max_pages: Maximum pages to analyze

        Returns:
            Dictionary with extracted data
        """
        if not self.anthropic:
            return {
                "success": False,
                "error": "Claude API not configured"
            }

        try:
            # Convert first few pages to base64 images
            images = []
            for page_num in range(1, min(max_pages + 1, 6)):
                img_base64 = ocr_service.pdf_page_to_base64(pdf_path, page_num)
                if img_base64:
                    images.append(img_base64)

            if not images:
                return {
                    "success": False,
                    "error": "Failed to convert PDF pages to images"
                }

            # Create prompt for Claude
            prompt = """
You are analyzing a construction plan document. Extract the following information:

1. **Bid Items**: List all bid items with their item numbers, descriptions, quantities, and units.
2. **Specifications**: List any specification codes or references (e.g., ASTM, AASHTO).
3. **Project Details**: Extract project name, location, bid date if visible.
4. **Materials**: List specific materials mentioned with quantities.

Return the data in this JSON format:
{
  "bid_items": [
    {
      "item_number": "101",
      "description": "Clearing and Grubbing",
      "quantity": 1.0,
      "unit": "LS",
      "unit_price": null
    }
  ],
  "specifications": [
    {
      "code": "ASTM C150",
      "description": "Portland Cement"
    }
  ],
  "project_info": {
    "name": "Highway 90 Expansion",
    "location": "Lafayette, LA",
    "bid_date": "2024-03-15"
  },
  "materials": [
    {
      "name": "Concrete",
      "quantity": 500,
      "unit": "CY",
      "specification": "ASTM C150"
    }
  ]
}

Be thorough but only include items explicitly mentioned in the documents.
If information is not found, use null or empty arrays.
"""

            # Build content with multiple images
            content = [
                {
                    "type": "text",
                    "text": prompt
                }
            ]

            for img_base64 in images:
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_base64
                    }
                })

            # Call Claude API
            message = self.anthropic.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": content
                }]
            )

            # Extract response text
            response_text = message.content[0].text

            # Try to parse JSON
            try:
                parsed_data = json.loads(response_text)
            except json.JSONDecodeError:
                # If not valid JSON, try to extract JSON from markdown code blocks
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    json_str = response_text[json_start:json_end].strip()
                    parsed_data = json.loads(json_str)
                else:
                    raise ValueError("Could not parse JSON from response")

            return {
                "success": True,
                "data": parsed_data,
                "pages_analyzed": len(images)
            }

        except Exception as e:
            logger.error(f"Failed to parse plan with Claude: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def parse_plan_with_ocr(
        self,
        pdf_path: Path,
        max_pages: int = 5
    ) -> Dict:
        """
        Fallback: Extract text using OCR and basic parsing

        Args:
            pdf_path: Path to PDF plan
            max_pages: Maximum pages to process

        Returns:
            Dictionary with extracted text
        """
        try:
            page_texts = ocr_service.extract_text_from_pdf(pdf_path, max_pages)

            if not page_texts:
                return {
                    "success": False,
                    "error": "OCR failed to extract text"
                }

            return {
                "success": True,
                "data": {
                    "raw_text": page_texts,
                    "pages_analyzed": len(page_texts)
                },
                "method": "ocr"
            }

        except Exception as e:
            logger.error(f"Failed to parse plan with OCR: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def parse_plan(
        self,
        pdf_path: Path,
        max_pages: int = 5,
        use_ai: bool = True
    ) -> Dict:
        """
        Parse construction plan using best available method

        Args:
            pdf_path: Path to PDF plan
            max_pages: Maximum pages to analyze
            use_ai: Whether to use AI (Claude) if available

        Returns:
            Dictionary with parsed data
        """
        ai_status = is_ai_available()

        # Try Claude first if available and requested
        if use_ai and ai_status["claude"]:
            logger.info("Parsing plan with Claude 3.5 Sonnet")
            result = await self.parse_plan_with_claude(pdf_path, max_pages)
            if result["success"]:
                return result

        # Fallback to OCR
        logger.info("Falling back to OCR parsing")
        return await self.parse_plan_with_ocr(pdf_path, max_pages)


# Singleton instance
plan_parser = PlanParser()
