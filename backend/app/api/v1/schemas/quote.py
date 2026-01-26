from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class QuoteBase(BaseModel):
    vendor_id: Optional[UUID] = None
    takeoff_item_id: Optional[UUID] = None
    vendor_name: str = Field(..., min_length=1, max_length=200)
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    item_description: str = Field(..., min_length=1)
    quantity: Decimal = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    unit_price: Decimal = Field(..., gt=0)
    total_price: Optional[Decimal] = None
    lead_time_days: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    received_at: Optional[datetime] = None


class QuoteCreate(QuoteBase):
    """Create new quote (manual entry)"""
    pass


class QuoteUpdate(BaseModel):
    """Update existing quote"""
    vendor_id: Optional[UUID] = None
    takeoff_item_id: Optional[UUID] = None
    vendor_name: Optional[str] = Field(None, min_length=1, max_length=200)
    vendor_email: Optional[str] = None
    vendor_phone: Optional[str] = None
    item_description: Optional[str] = None
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = None
    unit_price: Optional[Decimal] = Field(None, gt=0)
    total_price: Optional[Decimal] = None
    lead_time_days: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = None
    status: Optional[str] = None
    received_at: Optional[datetime] = None


class QuoteResponse(QuoteBase):
    """Quote response"""
    id: UUID
    project_id: UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class QuoteStatusUpdate(BaseModel):
    """Update quote status"""
    status: str = Field(..., pattern="^(pending|accepted|rejected)$")


class QuoteComparisonItem(BaseModel):
    """Single quote in comparison"""
    quote_id: UUID
    vendor_name: str
    unit_price: Decimal
    total_price: Decimal
    lead_time_days: Optional[int]
    vendor_rating: Optional[Decimal] = None
    notes: Optional[str] = None
    status: str


class QuoteComparison(BaseModel):
    """Comparison of quotes for a single item"""
    item_description: str
    quantity: Decimal
    unit: str
    quotes: List[QuoteComparisonItem]
    lowest_price: Decimal
    highest_price: Decimal
    average_price: Decimal
    recommended_quote_id: Optional[UUID] = None
    recommendation_reason: Optional[str] = None


class QuoteRankingCriteria(BaseModel):
    """Criteria weights for ranking quotes"""
    price_weight: float = Field(default=0.7, ge=0, le=1)
    rating_weight: float = Field(default=0.2, ge=0, le=1)
    lead_time_weight: float = Field(default=0.1, ge=0, le=1)


class QuoteRankingResult(BaseModel):
    """Ranked quote result"""
    quote_id: UUID
    vendor_name: str
    total_score: float
    price_score: float
    rating_score: float
    lead_time_score: float
    rank: int


class QuoteListResponse(BaseModel):
    """List of quotes"""
    total: int
    quotes: List[QuoteResponse]


class QuoteSummary(BaseModel):
    """Summary statistics for quotes"""
    total_quotes: int
    pending_quotes: int
    accepted_quotes: int
    rejected_quotes: int
    total_value_pending: Decimal
    total_value_accepted: Decimal
    items_with_quotes: int
    items_without_quotes: int
