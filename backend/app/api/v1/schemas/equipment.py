from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class InternalEquipmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    equipment_type: str = Field(..., min_length=1, max_length=100)
    model: Optional[str] = Field(None, max_length=200)
    serial_number: Optional[str] = Field(None, max_length=100)
    purchase_price: Optional[Decimal] = None
    hourly_cost: Decimal = Field(..., gt=0)
    is_available: bool = True
    condition: str = Field(default="good")
    notes: Optional[str] = None


class InternalEquipmentCreate(InternalEquipmentBase):
    pass


class InternalEquipmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    equipment_type: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, max_length=200)
    serial_number: Optional[str] = Field(None, max_length=100)
    purchase_price: Optional[Decimal] = None
    hourly_cost: Optional[Decimal] = Field(None, gt=0)
    is_available: Optional[bool] = None
    condition: Optional[str] = None
    notes: Optional[str] = None


class InternalEquipmentResponse(InternalEquipmentBase):
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class InternalEquipmentAvailabilityUpdate(BaseModel):
    is_available: bool
