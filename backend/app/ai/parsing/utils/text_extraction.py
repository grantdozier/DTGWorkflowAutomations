"""
Text Extraction Utilities

Utilities for extracting text from PDFs using multiple methods with automatic fallback.
"""

import logging
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extracts text from PDF documents using multiple methods"""

    def __init__(self):
        # Check available libraries
        self.pypdf2_available = self._check_pypdf2()
        self.pdfplumber_available = self._check_pdfplumber()
        self.ocr_available = self._check_ocr()

    def _check_pypdf2(self) -> bool:
        """Check if PyPDF2 is available"""
        try:
            import PyPDF2
            return True
        except ImportError:
            logger.warning("PyPDF2 not available")
            return False

    def _check_pdfplumber(self) -> bool:
        """Check if pdfplumber is available"""
        try:
            import pdfplumber
            return True
        except ImportError:
            logger.warning("pdfplumber not available")
            return False

    def _check_ocr(self) -> bool:
        """Check if OCR is available"""
        try:
            from app.ai.ocr_service import ocr_service
            return ocr_service.tesseract_available
        except Exception:
            return False

    def extract_text(
        self,
        pdf_path: Path,
        max_pages: Optional[int] = None,
        method: str = "auto"
    ) -> Tuple[List[str], str]:
        """
        Extract text from PDF using best available method

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to extract (None = all)
            method: Extraction method ("auto", "pypdf2", "pdfplumber", "ocr")

        Returns:
            Tuple of (list of page texts, method used)
        """
        logger.info(f"Extracting text from {pdf_path} using method={method}")

        if method == "auto":
            # Try methods in order of preference
            for method_name in ["pdfplumber", "pypdf2", "ocr"]:
                page_texts, actual_method = self._try_method(
                    method_name, pdf_path, max_pages
                )
                if page_texts:
                    logger.info(
                        f"Successfully extracted text using {actual_method}: "
                        f"{len(page_texts)} pages, "
                        f"{sum(len(t) for t in page_texts)} characters"
                    )
                    return page_texts, actual_method

            # All methods failed
            logger.error("All text extraction methods failed")
            return [], "none"

        else:
            # Use specific method
            page_texts, actual_method = self._try_method(method, pdf_path, max_pages)
            return page_texts, actual_method

    def _try_method(
        self,
        method: str,
        pdf_path: Path,
        max_pages: Optional[int]
    ) -> Tuple[List[str], str]:
        """Try a specific extraction method"""
        try:
            if method == "pdfplumber" and self.pdfplumber_available:
                return self._extract_with_pdfplumber(pdf_path, max_pages), "pdfplumber"
            elif method == "pypdf2" and self.pypdf2_available:
                return self._extract_with_pypdf2(pdf_path, max_pages), "pypdf2"
            elif method == "ocr" and self.ocr_available:
                return self._extract_with_ocr(pdf_path, max_pages), "ocr"
            else:
                return [], "unavailable"
        except Exception as e:
            logger.warning(f"Method {method} failed: {e}")
            return [], "failed"

    def _extract_with_pdfplumber(
        self,
        pdf_path: Path,
        max_pages: Optional[int]
    ) -> List[str]:
        """
        Extract text using pdfplumber (best for structured PDFs)

        pdfplumber is better at preserving layout and extracting tables
        """
        import pdfplumber

        page_texts = []

        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages[:max_pages] if max_pages else pdf.pages

            for i, page in enumerate(pages):
                try:
                    text = page.extract_text()
                    if text:
                        page_texts.append(text)
                        logger.debug(f"Page {i+1}: {len(text)} characters")
                    else:
                        page_texts.append("")
                        logger.warning(f"Page {i+1}: No text extracted")
                except Exception as e:
                    logger.error(f"Failed to extract page {i+1}: {e}")
                    page_texts.append("")

        return page_texts

    def _extract_with_pypdf2(
        self,
        pdf_path: Path,
        max_pages: Optional[int]
    ) -> List[str]:
        """
        Extract text using PyPDF2 (good for digital PDFs)

        PyPDF2 is fast and works well with native PDF text
        """
        import PyPDF2

        page_texts = []

        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            pages_to_read = min(max_pages, total_pages) if max_pages else total_pages

            for i in range(pages_to_read):
                try:
                    page = pdf_reader.pages[i]
                    text = page.extract_text()
                    if text:
                        page_texts.append(text)
                        logger.debug(f"Page {i+1}: {len(text)} characters")
                    else:
                        page_texts.append("")
                        logger.warning(f"Page {i+1}: No text extracted")
                except Exception as e:
                    logger.error(f"Failed to extract page {i+1}: {e}")
                    page_texts.append("")

        return page_texts

    def _extract_with_ocr(
        self,
        pdf_path: Path,
        max_pages: Optional[int]
    ) -> List[str]:
        """
        Extract text using OCR (for scanned documents)

        Slower but works on scanned/image-based PDFs
        """
        from app.ai.ocr_service import ocr_service

        max_pages_to_ocr = max_pages if max_pages else 50  # Default limit for OCR
        page_texts = ocr_service.extract_text_from_pdf(pdf_path, max_pages_to_ocr)

        return page_texts

    def is_scanned_document(self, pdf_path: Path, sample_pages: int = 3) -> bool:
        """
        Detect if PDF is scanned (image-based) vs digital

        Args:
            pdf_path: Path to PDF
            sample_pages: Number of pages to check

        Returns:
            True if document appears to be scanned
        """
        # Try to extract text from first few pages
        page_texts, method = self.extract_text(
            pdf_path, max_pages=sample_pages, method="pypdf2"
        )

        if not page_texts:
            return True  # Can't extract text = probably scanned

        # Calculate average text length per page
        avg_length = sum(len(text) for text in page_texts) / len(page_texts)

        # If average is very low, likely scanned
        # Threshold: less than 100 characters per page
        is_scanned = avg_length < 100

        logger.debug(
            f"Scanned detection: avg_length={avg_length:.0f}, "
            f"is_scanned={is_scanned}"
        )

        return is_scanned

    def get_page_count(self, pdf_path: Path) -> int:
        """
        Get number of pages in PDF

        Args:
            pdf_path: Path to PDF

        Returns:
            Number of pages
        """
        if self.pypdf2_available:
            try:
                import PyPDF2
                with open(pdf_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    return len(pdf_reader.pages)
            except Exception as e:
                logger.error(f"Failed to get page count: {e}")

        if self.pdfplumber_available:
            try:
                import pdfplumber
                with pdfplumber.open(pdf_path) as pdf:
                    return len(pdf.pages)
            except Exception as e:
                logger.error(f"Failed to get page count: {e}")

        return 0


# Singleton instance
text_extractor = TextExtractor()
