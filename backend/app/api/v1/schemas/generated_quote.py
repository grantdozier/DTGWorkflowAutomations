from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal


class GeneratedQuoteLineItemCreate(BaseModel):
    """Create a line item for a generated quote"""
    takeoff_item_id: Optional[UUID] = None
    material_id: Optional[UUID] = None
    line_number: int
    category: Optional[str] = None
    quantity: Decimal
    unit: str
    product_code: Optional[str] = None
    description: str
    unit_price: Decimal
    total_price: Optional[Decimal] = None
    notes: Optional[str] = None


class GeneratedQuoteLineItemResponse(BaseModel):
    """Response for a line item"""
    id: UUID
    generated_quote_id: UUID
    takeoff_item_id: Optional[UUID] = None
    material_id: Optional[UUID] = None
    line_number: int
    category: Optional[str] = None
    quantity: Decimal
    unit: str
    product_code: Optional[str] = None
    description: str
    unit_price: Decimal
    total_price: Decimal
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class GeneratedQuoteLineItemUpdate(BaseModel):
    """Update a line item"""
    category: Optional[str] = None
    quantity: Optional[Decimal] = None
    unit: Optional[str] = None
    product_code: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[Decimal] = None
    notes: Optional[str] = None


class GeneratedQuoteCreate(BaseModel):
    """Create a new generated quote"""
    quote_number: Optional[str] = None  # Auto-generated if not provided
    quote_date: Optional[date] = None
    expiration_date: Optional[date] = None
    customer_name: Optional[str] = None
    customer_company: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    job_name: Optional[str] = None
    job_reference: Optional[str] = None
    tax_rate: Optional[Decimal] = Field(default=Decimal("0"))
    special_instructions: Optional[str] = None
    notes: Optional[str] = None
    line_items: Optional[List[GeneratedQuoteLineItemCreate]] = None


class GeneratedQuoteUpdate(BaseModel):
    """Update a generated quote"""
    quote_date: Optional[date] = None
    expiration_date: Optional[date] = None
    customer_name: Optional[str] = None
    customer_company: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    job_name: Optional[str] = None
    job_reference: Optional[str] = None
    tax_rate: Optional[Decimal] = None
    special_instructions: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class GeneratedQuoteResponse(BaseModel):
    """Response for a generated quote"""
    id: UUID
    project_id: UUID
    created_by: UUID
    quote_number: str
    quote_date: date
    expiration_date: Optional[date] = None
    customer_name: Optional[str] = None
    customer_company: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    job_name: Optional[str] = None
    job_reference: Optional[str] = None
    subtotal: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    total: Decimal
    status: str
    special_instructions: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    line_items: Optional[List[GeneratedQuoteLineItemResponse]] = None

    class Config:
        from_attributes = True


class GeneratedQuoteListResponse(BaseModel):
    """List of generated quotes"""
    total: int
    quotes: List[GeneratedQuoteResponse]


class GenerateQuoteFromTakeoffsRequest(BaseModel):
    """Request to generate a quote from takeoff items"""
    takeoff_item_ids: Optional[List[UUID]] = None  # None means all items
    customer_name: Optional[str] = None
    customer_company: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    job_name: Optional[str] = None
    job_reference: Optional[str] = None
    tax_rate: Optional[Decimal] = Field(default=Decimal("0"))
    expiration_days: Optional[int] = Field(default=7)
    special_instructions: Optional[str] = None
    notes: Optional[str] = None
