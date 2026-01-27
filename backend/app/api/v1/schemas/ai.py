from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from uuid import UUID


class BidItemParsed(BaseModel):
    """Parsed bid item from plan"""
    item_number: Optional[str] = None
    description: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    unit_price: Optional[float] = None


class SpecificationParsed(BaseModel):
    """Parsed specification reference"""
    code: str
    description: Optional[str] = None


class MaterialParsed(BaseModel):
    """Parsed material requirement"""
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    specification: Optional[str] = None


class ProjectInfoParsed(BaseModel):
    """Parsed project information"""
    name: Optional[str] = None
    location: Optional[str] = None
    bid_date: Optional[str] = None


class ParsePlanResponse(BaseModel):
    """Response from plan parsing"""
    success: bool
    document_id: UUID
    pages_analyzed: Optional[int] = None
    method: str  # "claude", "openai", "ocr", "claude_tiling", "openai_native", "tesseract_ocr"
    strategy: Optional[str] = None  # NEW: Specific strategy used (e.g., "claude_tiling")
    confidence: Optional[float] = None  # NEW: Confidence score (0.0-1.0)
    processing_time_ms: Optional[int] = None  # NEW: Processing time in milliseconds
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # NEW: Strategy metadata


class ParseStatusResponse(BaseModel):
    """Status of AI services"""
    claude_available: bool
    openai_available: bool
    ocr_available: bool
    message: str
