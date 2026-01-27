"""
PDF Analyzer

Analyzes PDF documents to extract metrics for intelligent strategy selection.
"""

import logging
from pathlib import Path
from typing import Optional
import PyPDF2
from pdf2image import convert_from_path
from PIL import Image

from ..base_strategy import DocumentMetrics

logger = logging.getLogger(__name__)


class PDFAnalyzer:
    """Analyzes PDF documents to extract metrics"""

    def __init__(self):
        pass

    def analyze(self, pdf_path: Path) -> DocumentMetrics:
        """
        Analyze a PDF document and extract metrics

        Args:
            pdf_path: Path to the PDF file

        Returns:
            DocumentMetrics with file analysis
        """
        logger.info(f"Analyzing document: {pdf_path}")

        # Get file size
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)

        # Get page count
        page_count = self._get_page_count(pdf_path)

        # Estimate DPI from sample pages
        average_dpi = self._estimate_dpi(pdf_path, sample_pages=min(3, page_count))

        # Detect if scanned
        is_scanned = self._is_scanned_document(pdf_path, sample_pages=min(2, page_count))

        metrics = DocumentMetrics(
            file_path=pdf_path,
            file_size_mb=file_size_mb,
            page_count=page_count,
            average_dpi=average_dpi,
            is_scanned=is_scanned,
        )

        logger.info(
            f"Document analysis complete: "
            f"size={file_size_mb:.2f}MB, "
            f"pages={page_count}, "
            f"dpi={average_dpi}, "
            f"scanned={is_scanned}, "
            f"complexity={metrics.complexity_score:.2f}"
        )

        return metrics

    def _get_page_count(self, pdf_path: Path) -> int:
        """
        Get the number of pages in a PDF

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Number of pages
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            logger.error(f"Error getting page count: {e}")
            return 1

    def _estimate_dpi(self, pdf_path: Path, sample_pages: int = 3) -> Optional[int]:
        """
        Estimate average DPI by sampling pages

        Args:
            pdf_path: Path to the PDF file
            sample_pages: Number of pages to sample

        Returns:
            Estimated average DPI or None if cannot determine
        """
        try:
            # Convert first few pages to images
            images = convert_from_path(
                str(pdf_path),
                first_page=1,
                last_page=sample_pages,
                dpi=72,  # Use low DPI for analysis
            )

            if not images:
                return None

            # Calculate DPI from image dimensions
            # Standard letter size: 8.5" x 11"
            dpis = []
            for img in images:
                width, height = img.size
                # Estimate based on width (8.5 inches for letter)
                dpi_x = width / 8.5
                # Estimate based on height (11 inches for letter)
                dpi_y = height / 11
                # Use average
                avg_dpi = (dpi_x + dpi_y) / 2
                dpis.append(avg_dpi)

            if dpis:
                return int(sum(dpis) / len(dpis))

            return None

        except Exception as e:
            logger.warning(f"Could not estimate DPI: {e}")
            return None

    def _is_scanned_document(self, pdf_path: Path, sample_pages: int = 2) -> bool:
        """
        Detect if a PDF is a scanned document (images) vs native PDF

        Args:
            pdf_path: Path to the PDF file
            sample_pages: Number of pages to sample

        Returns:
            True if the document appears to be scanned
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)

                pages_to_check = min(sample_pages, len(pdf_reader.pages))
                text_counts = []

                for i in range(pages_to_check):
                    page = pdf_reader.pages[i]
                    try:
                        text = page.extract_text()
                        # Count non-whitespace characters
                        text_length = len(text.strip())
                        text_counts.append(text_length)
                    except Exception:
                        text_counts.append(0)

                # If average text length is very low, likely scanned
                avg_text = sum(text_counts) / len(text_counts) if text_counts else 0

                # Threshold: less than 100 characters per page suggests scanned
                is_scanned = avg_text < 100

                logger.debug(f"Scanned detection: avg_text={avg_text:.0f}, is_scanned={is_scanned}")

                return is_scanned

        except Exception as e:
            logger.warning(f"Could not determine if scanned: {e}")
            # Default to False (assume native PDF)
            return False


def analyze_document(pdf_path: Path) -> DocumentMetrics:
    """
    Convenience function to analyze a document

    Args:
        pdf_path: Path to the PDF file

    Returns:
        DocumentMetrics with file analysis
    """
    analyzer = PDFAnalyzer()
    return analyzer.analyze(pdf_path)
