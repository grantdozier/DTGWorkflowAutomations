from sqlalchemy import Column, String, DateTime, func, ForeignKey, Numeric, Boolean, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Vendor(Base):
    """Vendors/contacts by category (rental, subcontractor, outside_service, material_supplier)"""
    __tablename__ = "vendors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # rental, subcontractor, outside_service, material_supplier

    # Contact information
    contact_name = Column(String)
    email = Column(String)
    phone = Column(String)

    # Address
    address_line1 = Column(String)
    address_line2 = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)

    # Business details
    license_number = Column(String)
    insurance_expiry = Column(Date)

    # Rating and preferences
    rating = Column(Numeric(3, 2))  # 0.00 to 5.00
    is_preferred = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    notes = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
