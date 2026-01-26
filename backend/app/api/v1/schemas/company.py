from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class CompanyRatesBase(BaseModel):
    """Base model for company rates"""
    labor_rate_json: Optional[Dict[str, Any]] = {}
    equipment_rate_json: Optional[Dict[str, Any]] = {}
    overhead_json: Optional[Dict[str, Any]] = {}
    margin_json: Optional[Dict[str, Any]] = {}


class CompanyRatesCreate(CompanyRatesBase):
    """Create company rates"""
    pass


class CompanyRatesUpdate(CompanyRatesBase):
    """Update company rates (all fields optional)"""
    pass


class CompanyRatesResponse(CompanyRatesBase):
    """Company rates response"""
    id: UUID
    company_id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CompanyUpdate(BaseModel):
    """Update company information"""
    name: Optional[str] = None


class CompanyResponse(BaseModel):
    """Company response with rates"""
    id: UUID
    name: str
    created_at: datetime
    rates: Optional[CompanyRatesResponse] = None

    class Config:
        from_attributes = True


# Example structures for JSON fields (for documentation)
class LaborRateExample(BaseModel):
    """Example structure for labor_rate_json"""
    foreman: float = 45.00
    operator: float = 35.00
    laborer: float = 25.00
    equipment_operator: float = 38.00


class EquipmentRateExample(BaseModel):
    """Example structure for equipment_rate_json"""
    excavator: float = 125.00
    bulldozer: float = 150.00
    dump_truck: float = 85.00
    concrete_mixer: float = 95.00


class OverheadExample(BaseModel):
    """Example structure for overhead_json"""
    percentage: float = 15.0
    fixed_costs: float = 10000.00
    insurance: float = 5000.00
    office: float = 3000.00


class MarginExample(BaseModel):
    """Example structure for margin_json"""
    default_percentage: float = 10.0
    minimum_percentage: float = 5.0
    target_percentage: float = 12.0
