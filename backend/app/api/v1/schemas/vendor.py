from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


class VendorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1)  # rental, subcontractor, outside_service, material_supplier
    contact_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    license_number: Optional[str] = Field(None, max_length=100)
    insurance_expiry: Optional[date] = None
    rating: Optional[Decimal] = Field(None, ge=0, le=5)
    is_preferred: bool = False
    is_active: bool = True
    notes: Optional[str] = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None
    contact_name: Optional[str] = Field(None, max_length=200)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=20)
    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=50)
    zip_code: Optional[str] = Field(None, max_length=20)
    license_number: Optional[str] = Field(None, max_length=100)
    insurance_expiry: Optional[date] = None
    rating: Optional[Decimal] = Field(None, ge=0, le=5)
    is_preferred: Optional[bool] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class VendorResponse(VendorBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class VendorBulkImportRow(BaseModel):
    name: str
    category: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    license_number: Optional[str] = None
    rating: Optional[float] = None
    notes: Optional[str] = None


class VendorBulkImportResponse(BaseModel):
    success_count: int
    error_count: int
    errors: List[dict]
