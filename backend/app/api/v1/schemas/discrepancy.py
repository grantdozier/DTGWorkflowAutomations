from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class DiscrepancyResponse(BaseModel):
    """Discrepancy response"""
    id: UUID
    project_id: UUID
    project_bid_item_id: Optional[UUID]
    takeoff_item_id: Optional[UUID]
    discrepancy_type: str  # quantity_mismatch, missing_item, extra_item
    severity: str  # critical, high, medium, low
    bid_quantity: Optional[Decimal]
    plan_quantity: Optional[Decimal]
    difference_percentage: Optional[Decimal]
    description: str
    recommendation: Optional[str]
    status: str  # open, resolved, ignored
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class DiscrepancyDetectionResponse(BaseModel):
    """Response from discrepancy detection"""
    total_discrepancies: int
    discrepancies: List[DiscrepancyResponse]
    summary: dict


class DiscrepancyResolve(BaseModel):
    """Resolve a discrepancy"""
    status: str  # resolved, ignored
    resolution_notes: Optional[str] = None


class DiscrepancyListResponse(BaseModel):
    """List of discrepancies"""
    total: int
    by_severity: dict
    by_type: dict
    by_status: dict
    discrepancies: List[DiscrepancyResponse]


class DiscrepancySummary(BaseModel):
    """Summary of discrepancies"""
    total: int
    by_severity: dict
    by_type: dict
    open_count: int
    resolved_count: int
    ignored_count: int
