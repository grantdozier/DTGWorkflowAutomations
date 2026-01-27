"""
Document Parsing Strategies

Contains implementations of different parsing strategies:
- OpenAI Native PDF: Direct PDF upload to GPT-4 Vision
- Claude Tiling: Map-reduce approach with intelligent tiling
- Document AI: Google Cloud Document AI with targeted VLM
- Tesseract OCR: Fallback OCR strategy
"""

from .openai_native_strategy import OpenAINativeStrategy
from .claude_tiling_strategy import ClaudeTilingStrategy
from .tesseract_ocr_strategy import TesseractOCRStrategy

__all__ = [
    "OpenAINativeStrategy",
    "ClaudeTilingStrategy",
    "TesseractOCRStrategy",
]
