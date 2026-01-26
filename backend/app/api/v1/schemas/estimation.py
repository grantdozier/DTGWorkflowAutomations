from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal
from uuid import UUID


class CostBreakdown(BaseModel):
    """Cost breakdown for estimate"""
    materials: float = 0.0
    labor: float = 0.0
    equipment: float = 0.0
    subcontractors: float = 0.0
    subtotal: float = 0.0
    overhead: float = 0.0
    profit: float = 0.0
    total: float = 0.0


class EstimateItemDetail(BaseModel):
    """Detail for a single estimate item"""
    item_id: str
    description: str
    quantity: float
    unit: str
    unit_cost: float
    total_cost: float
    labor_hours: Optional[float] = None
    category: str  # material, labor, equipment


class GenerateEstimateRequest(BaseModel):
    """Request to generate an estimate"""
    include_takeoffs: bool = True
    include_bid_items: bool = True
    overhead_percentage: Optional[float] = None
    profit_percentage: Optional[float] = None


class EstimateResponse(BaseModel):
    """Estimate response"""
    id: UUID
    project_id: UUID
    created_by: UUID
    created_at: datetime

    # Cost breakdown
    materials_cost: float
    labor_cost: float
    equipment_cost: float
    subcontractor_cost: float
    overhead: float
    profit: float
    total_cost: float

    # Metadata
    confidence_score: Optional[float] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class EstimateDetailResponse(BaseModel):
    """Detailed estimate with line items"""
    estimate: EstimateResponse
    breakdown: CostBreakdown
    items: List[EstimateItemDetail]
    summary: Dict[str, Any]


class EstimateListResponse(BaseModel):
    """List of estimates"""
    total: int
    estimates: List[EstimateResponse]


class EstimateSummary(BaseModel):
    """Summary statistics for estimates"""
    total_estimates: int
    average_estimate: float
    min_estimate: float
    max_estimate: float
