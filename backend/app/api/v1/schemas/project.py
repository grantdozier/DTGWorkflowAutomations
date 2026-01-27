from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class ProjectBase(BaseModel):
    """Base project model"""
    name: str
    job_number: str
    location: Optional[str] = None
    type: Optional[str] = None  # state, private, federal, etc.


class ProjectCreate(ProjectBase):
    """Create project request"""
    pass


class ProjectUpdate(BaseModel):
    """Update project request (all fields optional)"""
    name: Optional[str] = None
    job_number: Optional[str] = None
    location: Optional[str] = None
    type: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Project response"""
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    """List of projects with pagination"""
    total: int
    projects: List[ProjectResponse]


class ProjectDocumentResponse(BaseModel):
    """Project document response"""
    id: UUID
    project_id: UUID
    doc_type: str
    file_path: str
    file_name: Optional[str] = None
    is_parsed: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class BidItemBase(BaseModel):
    """Base bid item model"""
    code: str
    name: str
    unit: str


class BidItemResponse(BidItemBase):
    """Bid item response"""
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectBidItemCreate(BaseModel):
    """Create project bid item"""
    bid_item_id: UUID
    bid_qty: Optional[float] = None
    bid_unit_price: Optional[float] = None


class ProjectBidItemUpdate(BaseModel):
    """Update project bid item"""
    bid_qty: Optional[float] = None
    bid_unit_price: Optional[float] = None


class ProjectBidItemResponse(BaseModel):
    """Project bid item response"""
    id: UUID
    project_id: UUID
    bid_item_id: UUID
    bid_qty: Optional[float]
    bid_unit_price: Optional[float]
    created_at: datetime
    updated_at: Optional[datetime]
    bid_item: Optional[BidItemResponse] = None

    class Config:
        from_attributes = True
