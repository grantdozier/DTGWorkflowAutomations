"""
Parsing Configuration

Configuration management for the multi-strategy document parsing system.
"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ParsingConfig(BaseModel):
    """Configuration for document parsing strategies"""

    # API Keys
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key for Claude")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")

    # Google Cloud Document AI
    google_credentials_path: Optional[str] = Field(None, description="Path to GCP credentials JSON")
    google_project_id: Optional[str] = Field(None, description="GCP project ID")
    google_location: str = Field("us", description="GCP location for Document AI")
    google_processor_id: Optional[str] = Field(None, description="Document AI processor ID")

    # Strategy toggles
    enable_openai_parsing: bool = Field(True, description="Enable OpenAI native PDF strategy")
    enable_document_ai_parsing: bool = Field(False, description="Enable Google Document AI strategy")
    enable_claude_parsing: bool = Field(True, description="Enable Claude tiling strategy")
    enable_tesseract_parsing: bool = Field(True, description="Enable Tesseract OCR fallback")

    # Image processing settings - HIGH QUALITY for microscopic detail
    max_image_size_mb: float = Field(4.5, description="Maximum image size in MB")
    tile_overlap_percent: float = Field(0.1, description="Overlap percentage for tiles (0.0-0.5)")
    coarse_scan_dpi: int = Field(100, description="DPI for coarse ROI detection scan (low-res is fine)")
    detail_scan_dpi: int = Field(300, description="DPI for detailed tile scanning (INCREASED to 300 for microscopic detail)")

    # Processing limits
    max_concurrent_tiles: int = Field(5, description="Maximum concurrent tile processing")
    default_max_pages: int = Field(5, description="Default maximum pages to process")

    # Claude settings
    claude_model: str = Field("claude-sonnet-4-5-20250929", description="Claude model to use (current: claude-sonnet-4-5-20250929 or claude-opus-4-5-20251101)")
    claude_max_tokens: int = Field(16000, description="Maximum tokens for Claude responses")
    claude_temperature: float = Field(0.0, description="Temperature for Claude (0.0-1.0)")

    # OpenAI settings
    openai_model: str = Field("gpt-4o", description="OpenAI model to use")
    openai_max_tokens: int = Field(16000, description="Maximum tokens for OpenAI responses")
    openai_temperature: float = Field(0.0, description="Temperature for OpenAI (0.0-1.0)")

    # Deduplication settings
    fuzzy_match_threshold: int = Field(85, description="Fuzzy match threshold (0-100)")
    merge_iou_threshold: float = Field(0.5, description="IoU threshold for merging bounding boxes")

    # Logging
    log_level: str = Field("INFO", description="Logging level")
    log_strategy_selection: bool = Field(True, description="Log strategy selection details")
    log_processing_time: bool = Field(True, description="Log processing time metrics")

    class Config:
        env_prefix = ""


def load_parsing_config() -> ParsingConfig:
    """
    Load parsing configuration from environment variables

    Returns:
        ParsingConfig instance
    """
    config = ParsingConfig(
        # API Keys
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),

        # Google Cloud
        google_credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
        google_project_id=os.getenv("GOOGLE_PROJECT_ID"),
        google_location=os.getenv("GOOGLE_LOCATION", "us"),
        google_processor_id=os.getenv("GOOGLE_PROCESSOR_ID"),

        # Strategy toggles
        enable_openai_parsing=os.getenv("ENABLE_OPENAI_PARSING", "true").lower() == "true",
        enable_document_ai_parsing=os.getenv("ENABLE_DOCUMENT_AI_PARSING", "false").lower() == "true",
        enable_claude_parsing=os.getenv("ENABLE_CLAUDE_PARSING", "true").lower() == "true",
        enable_tesseract_parsing=os.getenv("ENABLE_TESSERACT_PARSING", "true").lower() == "true",

        # Image processing
        max_image_size_mb=float(os.getenv("MAX_IMAGE_SIZE_MB", "4.5")),
        tile_overlap_percent=float(os.getenv("TILE_OVERLAP_PERCENT", "0.1")),
        coarse_scan_dpi=int(os.getenv("COARSE_SCAN_DPI", "100")),
        detail_scan_dpi=int(os.getenv("DETAIL_SCAN_DPI", "200")),

        # Processing limits
        max_concurrent_tiles=int(os.getenv("MAX_CONCURRENT_TILES", "5")),
        default_max_pages=int(os.getenv("DEFAULT_MAX_PAGES", "5")),

        # Claude settings
        claude_model=os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929"),
        claude_max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", "16000")),
        claude_temperature=float(os.getenv("CLAUDE_TEMPERATURE", "0.0")),

        # OpenAI settings
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        openai_max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "16000")),
        openai_temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.0")),

        # Deduplication
        fuzzy_match_threshold=int(os.getenv("FUZZY_MATCH_THRESHOLD", "85")),
        merge_iou_threshold=float(os.getenv("MERGE_IOU_THRESHOLD", "0.5")),

        # Logging
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        log_strategy_selection=os.getenv("LOG_STRATEGY_SELECTION", "true").lower() == "true",
        log_processing_time=os.getenv("LOG_PROCESSING_TIME", "true").lower() == "true",
    )

    return config


def get_strategy_config(config: ParsingConfig) -> Dict[str, Any]:
    """
    Convert ParsingConfig to dictionary for strategy initialization

    Args:
        config: ParsingConfig instance

    Returns:
        Dictionary of configuration values
    """
    return config.dict()
