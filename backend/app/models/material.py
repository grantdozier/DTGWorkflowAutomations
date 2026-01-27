from sqlalchemy import Column, String, DateTime, func, ForeignKey, Numeric, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Material(Base):
    """
    Material catalog for companies

    Stores pricing and details for construction materials.
    Each company maintains their own material catalog.
    """
    __tablename__ = "materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)

    # Product identification
    product_code = Column(String, nullable=False, index=True)  # Vendor SKU/product code
    description = Column(Text, nullable=False)
    category = Column(String, nullable=False, index=True)  # Foundation, Walls, Roofing, etc.

    # Pricing
    unit_price = Column(Numeric(15, 2), nullable=False)
    unit = Column(String, nullable=False)  # ea, BDL, RL, sq, LF, etc.

    # Additional details
    manufacturer = Column(String)
    specifications = Column(Text)  # Technical specs, dimensions, etc.
    notes = Column(Text)

    # Availability
    is_active = Column(Boolean, default=True)
    lead_time_days = Column(Numeric(5, 1))  # Typical delivery time
    minimum_order = Column(Numeric(10, 2))  # Minimum order quantity

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Material {self.product_code}: {self.description} @ ${self.unit_price}/{self.unit}>"
