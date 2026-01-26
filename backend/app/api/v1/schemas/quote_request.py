from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date


class QuoteRequestItemCreate(BaseModel):
    """Item to request quote for"""
    takeoff_item_id: UUID
    description: str
    quantity: float
    unit: str


class QuoteRequestCreate(BaseModel):
    """Create quote request"""
    vendor_ids: List[UUID] = Field(..., min_items=1, max_items=20)
    takeoff_item_ids: List[UUID] = Field(..., min_items=1)
    message: Optional[str] = None
    expected_response_date: Optional[date] = None
    attach_documents: bool = False


class QuoteRequestBulkCreate(BaseModel):
    """Send quote requests to multiple vendors"""
    vendor_ids: List[UUID] = Field(..., min_items=1)
    takeoff_item_ids: List[UUID] = Field(..., min_items=1)
    message: Optional[str] = None
    expected_response_date: Optional[date] = None


class QuoteRequestResponse(BaseModel):
    """Quote request response"""
    id: UUID
    project_id: UUID
    vendor_id: UUID
    vendor_name: str
    vendor_email: Optional[str]
    email_subject: str
    sent_at: datetime
    status: str
    expected_response_date: Optional[date]
    requested_items_count: int

    class Config:
        from_attributes = True


class QuoteRequestDetail(BaseModel):
    """Detailed quote request"""
    id: UUID
    project_id: UUID
    vendor_id: UUID
    vendor_name: str
    vendor_email: Optional[str]
    email_subject: str
    email_body: str
    sent_at: datetime
    status: str
    expected_response_date: Optional[date]
    requested_items: List[dict]

    class Config:
        from_attributes = True


class QuoteRequestStatusUpdate(BaseModel):
    """Update quote request status"""
    status: str = Field(..., pattern="^(sent|opened|responded|expired)$")


class QuoteRequestBulkResponse(BaseModel):
    """Response from bulk quote request"""
    success_count: int
    error_count: int
    errors: List[dict]
    request_ids: List[UUID]


class QuoteRequestSummary(BaseModel):
    """Summary of quote requests"""
    total_requests: int
    sent_count: int
    responded_count: int
    expired_count: int
    pending_count: int
