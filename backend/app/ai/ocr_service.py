import logging
from pathlib import Path
from typing import List, Optional
import base64
from io import BytesIO

try:
    import pytesseract
    from PIL import Image
    from pdf2image import convert_from_path
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


class OCRService:
    """
    Extract text from PDFs using OCR
    Fallback service when AI vision models are not available
    """

    def __init__(self):
        self.tesseract_available = TESSERACT_AVAILABLE

    def extract_text_from_pdf(self, pdf_path: Path, max_pages: int = 10) -> List[str]:
        """
        Extract text from PDF pages using OCR

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to process

        Returns:
            List of text strings, one per page
        """
        if not self.tesseract_available:
            logger.warning("Tesseract not available, cannot perform OCR")
            return []

        try:
            # Convert PDF to images
            images = convert_from_path(pdf_path, first_page=1, last_page=max_pages)

            # Extract text from each page
            page_texts = []
            for i, image in enumerate(images):
                try:
                    text = pytesseract.image_to_string(image)
                    page_texts.append(text)
                    logger.info(f"Extracted text from page {i+1}: {len(text)} characters")
                except Exception as e:
                    logger.error(f"Failed to OCR page {i+1}: {str(e)}")
                    page_texts.append("")

            return page_texts

        except Exception as e:
            logger.error(f"Failed to process PDF: {str(e)}")
            return []

    def pdf_page_to_base64(self, pdf_path: Path, page_num: int = 1) -> Optional[str]:
        """
        Convert a PDF page to base64-encoded image for AI vision models

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)

        Returns:
            Base64-encoded image string, or None on error
        """
        if not self.tesseract_available:
            logger.warning("pdf2image not available")
            return None

        try:
            # Convert single page to image
            images = convert_from_path(pdf_path, first_page=page_num, last_page=page_num)

            if not images:
                return None

            # Convert to base64
            image = images[0]
            buffer = BytesIO()
            image.save(buffer, format="PNG")
            img_bytes = buffer.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            return img_base64

        except Exception as e:
            logger.error(f"Failed to convert PDF page to image: {str(e)}")
            return None

    def get_pdf_page_count(self, pdf_path: Path) -> int:
        """
        Get the number of pages in a PDF

        Args:
            pdf_path: Path to PDF file

        Returns:
            Number of pages, or 0 on error
        """
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(str(pdf_path))
            return len(reader.pages)
        except Exception as e:
            logger.error(f"Failed to get page count: {str(e)}")
            return 0


# Singleton instance
ocr_service = OCRService()
