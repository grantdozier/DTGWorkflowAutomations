"""
OpenAI Native PDF Strategy

Uses OpenAI's native PDF input support (GPT-4 Vision with PDF) for fast, direct PDF parsing
without image conversion overhead.

Best for: Small-medium documents (<50MB, <10 pages, <300 DPI)
"""

import base64
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from openai import OpenAI

from ..base_strategy import BaseParsingStrategy, ParseResult, DocumentMetrics, StrategyType

logger = logging.getLogger(__name__)


class OpenAINativeStrategy(BaseParsingStrategy):
    """
    OpenAI native PDF input strategy

    Uses GPT-4 Vision with direct PDF upload (no base64 conversion).
    Handles PDFs up to 50MB efficiently.
    """

    def _get_strategy_type(self) -> StrategyType:
        return StrategyType.OPENAI_NATIVE

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Initialize OpenAI client
        api_key = config.get("openai_api_key")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None

        # Configuration
        self.model = config.get("openai_model", "gpt-4o")
        self.max_tokens = config.get("openai_max_tokens", 16000)
        self.temperature = config.get("openai_temperature", 0.0)

    def is_available(self) -> bool:
        """Check if OpenAI API is configured"""
        enabled = self.config.get("enable_openai_parsing", True)
        return enabled and self.client is not None

    def can_handle(self, metrics: DocumentMetrics) -> bool:
        """
        Check if this strategy can handle the document

        Criteria:
        - File size < 50MB
        - Page count <= 10
        - Average DPI < 300 (or unknown)
        """
        if metrics.file_size_mb >= 50:
            return False

        if metrics.page_count > 10:
            return False

        if metrics.average_dpi and metrics.average_dpi >= 300:
            return False

        return True

    def get_priority(self) -> int:
        """Priority 1 - try first for small-medium documents"""
        return 1

    async def parse(self, pdf_path: Path, max_pages: int = 5) -> ParseResult:
        """
        Parse PDF using OpenAI native PDF input

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process (note: OpenAI processes all pages)

        Returns:
            ParseResult with extracted data
        """
        start_time = time.time()
        logger.info(f"Starting OpenAI native PDF strategy for {pdf_path}")

        try:
            # Read PDF as binary
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()

            # Encode to base64
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')

            # Create extraction prompt
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

            # Call OpenAI API with PDF
            # Note: OpenAI's PDF support may vary by model and API version
            # Using the image content type with PDF MIME type
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:application/pdf;base64,{pdf_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            # Extract response
            response_text = response.choices[0].message.content

            # Parse JSON
            parsed_data = self._parse_json_response(response_text)

            if not parsed_data:
                raise ValueError("Failed to parse JSON from response")

            # Calculate metrics
            processing_time = int((time.time() - start_time) * 1000)
            confidence = self._calculate_confidence(parsed_data)

            logger.info(
                f"OpenAI native parsing complete: "
                f"confidence={confidence:.2f}, "
                f"time={processing_time}ms"
            )

            return ParseResult(
                success=True,
                data=parsed_data,
                strategy_used=StrategyType.OPENAI_NATIVE,
                confidence_score=confidence,
                pages_processed=max_pages,
                processing_time_ms=processing_time,
                metadata={
                    "model": self.model,
                    "method": "native_pdf",
                },
            )

        except Exception as e:
            logger.error(f"OpenAI native strategy failed: {e}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)

            return ParseResult(
                success=False,
                error=str(e),
                strategy_used=StrategyType.OPENAI_NATIVE,
                processing_time_ms=processing_time,
            )

    def _parse_json_response(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from OpenAI response, handling markdown code blocks"""
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

            logger.warning("Could not parse JSON from OpenAI response")
            return None

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data completeness"""
        score = 0.0

        # Bid items (most important)
        bid_items = data.get("bid_items", [])
        if bid_items:
            score += 0.4
            # Bonus for well-structured items
            complete_items = sum(
                1 for item in bid_items
                if item.get("item_number") and item.get("description")
            )
            score += 0.2 * min(complete_items / max(len(bid_items), 1), 1.0)

        # Project info
        proj_info = data.get("project_info", {})
        if proj_info and any(v for v in proj_info.values() if v):
            score += 0.2

        # Specifications
        if data.get("specifications"):
            score += 0.1

        # Materials
        if data.get("materials"):
            score += 0.1

        return min(score, 1.0)
