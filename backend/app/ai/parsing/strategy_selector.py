"""
Strategy Selector

Intelligent routing system that:
1. Analyzes documents to extract metrics
2. Selects optimal parsing strategy
3. Executes with automatic fallback chain
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base_strategy import BaseParsingStrategy, ParseResult, DocumentMetrics
from .output_normalizer import OutputNormalizer
from .utils.pdf_analyzer import PDFAnalyzer
from .strategies.openai_native_strategy import OpenAINativeStrategy
from .strategies.claude_tiling_strategy import ClaudeTilingStrategy
from .strategies.tesseract_ocr_strategy import TesseractOCRStrategy

logger = logging.getLogger(__name__)


class StrategySelector:
    """
    Orchestrates document parsing with intelligent strategy selection and fallback
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize strategy selector

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.analyzer = PDFAnalyzer()
        self.normalizer = OutputNormalizer()

        # Initialize all strategies
        self.strategies: List[BaseParsingStrategy] = [
            OpenAINativeStrategy(config),
            ClaudeTilingStrategy(config),
            TesseractOCRStrategy(config),
        ]

        # Log configuration
        if config.get("log_strategy_selection", True):
            logger.info("Initialized strategy selector with strategies:")
            for strategy in self.strategies:
                logger.info(
                    f"  - {strategy.get_name()}: "
                    f"available={strategy.is_available()}, "
                    f"priority={strategy.get_priority()}"
                )

    async def parse_with_fallback(
        self,
        pdf_path: Path,
        max_pages: int = 5
    ) -> ParseResult:
        """
        Parse document with intelligent strategy selection and automatic fallback

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum pages to process

        Returns:
            ParseResult from first successful strategy
        """
        # Step 1: Analyze document
        logger.info(f"Analyzing document: {pdf_path}")
        metrics = self.analyzer.analyze(pdf_path)

        # Step 2: Build strategy chain
        chain = await self.analyze_and_select(pdf_path, metrics)

        if not chain:
            logger.error("No strategies available")
            return ParseResult(
                success=False,
                error="No parsing strategies available",
            )

        # Step 3: Try each strategy in order
        errors = []

        for i, strategy in enumerate(chain):
            strategy_name = strategy.get_name()
            logger.info(
                f"Attempting strategy {i + 1}/{len(chain)}: {strategy_name}"
            )

            try:
                result = await strategy.parse(pdf_path, max_pages)

                if result.success:
                    # Normalize output
                    if result.data:
                        result.data = self.normalizer.normalize(result.data)

                    logger.info(
                        f"Success with {strategy_name}: "
                        f"confidence={result.confidence_score:.2f}, "
                        f"time={result.processing_time_ms}ms"
                    )

                    return result
                else:
                    error_msg = f"{strategy_name} failed: {result.error}"
                    logger.warning(error_msg)
                    errors.append(error_msg)

            except Exception as e:
                error_msg = f"{strategy_name} exception: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)

        # All strategies failed
        logger.error("All strategies failed")
        return ParseResult(
            success=False,
            error="All parsing strategies failed. " + "; ".join(errors),
        )

    async def analyze_and_select(
        self,
        pdf_path: Path,
        metrics: Optional[DocumentMetrics] = None
    ) -> List[BaseParsingStrategy]:
        """
        Analyze document and select strategy chain

        Args:
            pdf_path: Path to PDF file
            metrics: Pre-computed metrics (will analyze if not provided)

        Returns:
            Ordered list of strategies to try
        """
        # Analyze if metrics not provided
        if metrics is None:
            metrics = self.analyzer.analyze(pdf_path)

        # Filter to available strategies
        available = [s for s in self.strategies if s.is_available()]

        if not available:
            logger.warning("No strategies available")
            return []

        # Filter to strategies that can handle this document
        capable = [s for s in available if s.can_handle(metrics)]

        if not capable:
            logger.warning(
                "No strategies can handle document, using all available"
            )
            capable = available

        # Sort by priority (lower = higher priority)
        chain = sorted(capable, key=lambda s: s.get_priority())

        # Ensure OCR is always last (if available)
        ocr_strategies = [s for s in chain if s.get_priority() == 4]
        non_ocr = [s for s in chain if s.get_priority() != 4]

        chain = non_ocr + ocr_strategies

        # Log selection
        if self.config.get("log_strategy_selection", True):
            logger.info(
                f"Document metrics: "
                f"size={metrics.file_size_mb:.2f}MB, "
                f"pages={metrics.page_count}, "
                f"dpi={metrics.average_dpi}, "
                f"complexity={metrics.complexity_score:.2f}"
            )
            logger.info(
                f"Strategy chain ({len(chain)}): "
                + " -> ".join(s.get_name() for s in chain)
            )

        return chain

    def get_available_strategies(self) -> List[str]:
        """
        Get list of available strategy names

        Returns:
            List of strategy names
        """
        return [
            s.get_name()
            for s in self.strategies
            if s.is_available()
        ]

    def get_strategy_info(self) -> List[Dict[str, Any]]:
        """
        Get detailed info about all strategies

        Returns:
            List of strategy information dictionaries
        """
        return [
            {
                "name": s.get_name(),
                "type": s.strategy_type.value,
                "available": s.is_available(),
                "priority": s.get_priority(),
            }
            for s in self.strategies
        ]
