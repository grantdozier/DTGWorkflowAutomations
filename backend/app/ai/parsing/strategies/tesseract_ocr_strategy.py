"""
Tesseract OCR Fallback Strategy

Wraps the existing OCR service as a parsing strategy.
Always available, lowest priority - used as final fallback.

Returns raw text without structured extraction.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any

from app.ai.ocr_service import ocr_service

from ..base_strategy import BaseParsingStrategy, ParseResult, DocumentMetrics, StrategyType

logger = logging.getLogger(__name__)


class TesseractOCRStrategy(BaseParsingStrategy):
    """
    Tesseract OCR fallback strategy

    Uses Tesseract OCR to extract raw text from PDF pages.
    Always available as final fallback, but provides minimal structure.
    """

    def _get_strategy_type(self) -> StrategyType:
        return StrategyType.TESSERACT_OCR

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.ocr = ocr_service

    def is_available(self) -> bool:
        """Check if Tesseract is available"""
        enabled = self.config.get("enable_tesseract_parsing", True)
        return enabled and self.ocr.tesseract_available

    def can_handle(self, metrics: DocumentMetrics) -> bool:
        """OCR can handle any document (fallback strategy)"""
        return True

    def get_priority(self) -> int:
        """Priority 4 - final fallback"""
        return 4

    async def parse(self, pdf_path: Path, max_pages: int = 5) -> ParseResult:
        """
        Parse PDF using Tesseract OCR

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process

        Returns:
            ParseResult with extracted text
        """
        start_time = time.time()
        logger.info(f"Starting Tesseract OCR strategy for {pdf_path}")

        try:
            # Extract text from pages
            page_texts = self.ocr.extract_text_from_pdf(pdf_path, max_pages)

            if not page_texts:
                raise ValueError("OCR failed to extract text from PDF")

            # Combine text and attempt basic parsing
            combined_text = "\n\n".join(page_texts)

            # Try to extract some basic structure
            data = self._extract_basic_structure(combined_text)

            # Calculate metrics
            processing_time = int((time.time() - start_time) * 1000)

            # OCR has low confidence since no structured extraction
            confidence = 0.3 if data.get("bid_items") else 0.2

            logger.info(
                f"Tesseract OCR complete: "
                f"{len(page_texts)} pages, "
                f"{len(combined_text)} characters, "
                f"time={processing_time}ms"
            )

            return ParseResult(
                success=True,
                data=data,
                strategy_used=StrategyType.TESSERACT_OCR,
                confidence_score=confidence,
                pages_processed=len(page_texts),
                processing_time_ms=processing_time,
                metadata={
                    "method": "ocr",
                    "character_count": len(combined_text),
                },
            )

        except Exception as e:
            logger.error(f"Tesseract OCR strategy failed: {e}", exc_info=True)
            processing_time = int((time.time() - start_time) * 1000)

            return ParseResult(
                success=False,
                error=str(e),
                strategy_used=StrategyType.TESSERACT_OCR,
                processing_time_ms=processing_time,
            )

    def _extract_basic_structure(self, text: str) -> Dict[str, Any]:
        """
        Attempt to extract basic structure from raw OCR text

        Args:
            text: Raw OCR text

        Returns:
            Dictionary with basic structure (mostly raw text)
        """
        # This is a very basic extraction - just structure the raw text
        # In a production system, you could add more sophisticated parsing

        lines = text.split("\n")

        # Try to identify potential bid items (lines with numbers)
        potential_items = []
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue

            # Look for lines that start with numbers (potential item numbers)
            if line_stripped[0].isdigit():
                potential_items.append({
                    "item_number": None,
                    "description": line_stripped,
                    "quantity": None,
                    "unit": None,
                })

        # Basic structure with raw text
        data = {
            "bid_items": potential_items[:50],  # Limit to first 50
            "specifications": [],
            "project_info": {
                "name": None,
                "location": None,
                "bid_date": None,
            },
            "materials": [],
            "raw_text": text,  # Include full raw text for reference
        }

        return data
