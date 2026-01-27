"""
Base Strategy Interface

Defines the abstract base class and data structures that all parsing strategies must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class StrategyType(Enum):
    """Enumeration of available parsing strategies"""
    OPENAI_NATIVE = "openai_native"
    CLAUDE_TILING = "claude_tiling"
    DOCUMENT_AI = "document_ai"
    TESSERACT_OCR = "tesseract_ocr"


@dataclass
class DocumentMetrics:
    """
    Metrics about a document used for strategy selection
    """
    file_path: Path
    file_size_mb: float
    page_count: int
    average_dpi: Optional[int] = None
    complexity_score: float = 0.0
    is_scanned: bool = False
    has_tables: bool = False
    has_images: bool = False

    def __post_init__(self):
        """Calculate complexity score if not provided"""
        if self.complexity_score == 0.0:
            self.complexity_score = self._calculate_complexity()

    def _calculate_complexity(self) -> float:
        """
        Calculate document complexity score (0.0-1.0)

        Factors:
        - File size (larger = more complex)
        - Page count (more pages = more complex)
        - DPI (higher = more complex)
        - Scanned documents (more complex)
        """
        score = 0.0

        # File size component (0-0.3)
        if self.file_size_mb < 5:
            score += 0.0
        elif self.file_size_mb < 20:
            score += 0.1
        elif self.file_size_mb < 50:
            score += 0.2
        else:
            score += 0.3

        # Page count component (0-0.3)
        if self.page_count < 5:
            score += 0.0
        elif self.page_count < 15:
            score += 0.1
        elif self.page_count < 30:
            score += 0.2
        else:
            score += 0.3

        # DPI component (0-0.2)
        if self.average_dpi:
            if self.average_dpi < 150:
                score += 0.0
            elif self.average_dpi < 250:
                score += 0.1
            else:
                score += 0.2

        # Scanned document penalty (0-0.2)
        if self.is_scanned:
            score += 0.2

        return min(score, 1.0)


@dataclass
class ParseResult:
    """
    Standardized output from any parsing strategy
    """
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    strategy_used: Optional[StrategyType] = None
    confidence_score: float = 0.0
    pages_processed: int = 0
    processing_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "strategy": self.strategy_used.value if self.strategy_used else None,
            "confidence": self.confidence_score,
            "pages_analyzed": self.pages_processed,
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseParsingStrategy(ABC):
    """
    Abstract base class for all document parsing strategies

    Each strategy must implement:
    - parse(): Main parsing logic
    - can_handle(): Whether the strategy can handle a specific document
    - get_priority(): Priority level (lower = higher priority)
    - is_available(): Whether the strategy is currently available
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the strategy with configuration

        Args:
            config: Dictionary containing strategy-specific configuration
        """
        self.config = config
        self.strategy_type = self._get_strategy_type()

    @abstractmethod
    def _get_strategy_type(self) -> StrategyType:
        """Return the strategy type enum value"""
        pass

    @abstractmethod
    async def parse(
        self,
        pdf_path: Path,
        max_pages: int = 5
    ) -> ParseResult:
        """
        Parse a PDF document and extract structured data

        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum number of pages to process

        Returns:
            ParseResult with success status and extracted data
        """
        pass

    @abstractmethod
    def can_handle(self, metrics: DocumentMetrics) -> bool:
        """
        Determine if this strategy can handle the given document

        Args:
            metrics: Document metrics

        Returns:
            True if the strategy can handle the document
        """
        pass

    @abstractmethod
    def get_priority(self) -> int:
        """
        Get the priority of this strategy (lower = higher priority)

        Priority order:
        1. OpenAI Native (fast, good for small-medium docs)
        2. Document AI (best for scanned, large docs)
        3. Claude Tiling (universal, works for any size)
        4. Tesseract OCR (fallback, raw text only)

        Returns:
            Priority level (1-4)
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this strategy is currently available

        Returns:
            True if the strategy can be used (API keys configured, etc.)
        """
        pass

    def get_name(self) -> str:
        """Get human-readable strategy name"""
        return self.strategy_type.value.replace("_", " ").title()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(available={self.is_available()}, priority={self.get_priority()})>"
