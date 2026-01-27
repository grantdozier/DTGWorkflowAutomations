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

    def pdf_page_to_base64(self, pdf_path: Path, page_num: int = 1, max_size_mb: float = 4.5) -> Optional[str]:
        """
        Convert a PDF page to base64-encoded image for AI vision models

        FIXED: Now uses JPEG with adaptive compression to stay under size limit
        (was using PNG which caused 5MB+ images and API rejections)

        Args:
            pdf_path: Path to PDF file
            page_num: Page number (1-indexed)
            max_size_mb: Maximum size in MB (default 4.5 for safety margin)

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

            image = images[0]

            # Convert RGBA/P to RGB for JPEG
            if image.mode in ('RGBA', 'P', 'LA'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = rgb_image

            # HIGH-QUALITY compression to preserve microscopic detail
            # NOTE: For construction plans needing maximum detail, use Claude Tiling strategy instead
            # This method should only be used for legacy/fallback scenarios
            max_bytes = int(max_size_mb * 1024 * 1024)
            quality = 95
            min_quality = 85  # CHANGED: Don't go below 85 to preserve detail

            while quality >= min_quality:
                buffer = BytesIO()
                image.save(buffer, format='JPEG', quality=quality, optimize=True)
                size = buffer.tell()

                # Check base64 size (base64 is ~133% of binary)
                estimated_base64_size = size * 4 / 3

                if estimated_base64_size <= max_bytes:
                    buffer.seek(0)
                    img_base64 = base64.b64encode(buffer.read()).decode('utf-8')
                    actual_mb = len(img_base64) * 3 / 4 / 1024 / 1024
                    logger.info(f"Page {page_num}: {actual_mb:.2f}MB at quality={quality}")
                    return img_base64

                quality -= 5  # CHANGED: Smaller steps to preserve quality

            # If we get here, image is too large even at quality 85
            # ERROR: Don't resize - that loses detail! Use tiling strategy instead
            logger.error(
                f"Page {page_num} exceeds size limit even at quality {min_quality}. "
                f"Image size: {image.size}, estimated: {size/1024/1024:.1f}MB. "
                f"For construction plans requiring microscopic detail, use Claude Tiling strategy instead "
                f"which tiles BEFORE compression to preserve full resolution."
            )

            # Return None to force fallback to tiling strategy
            return None

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
