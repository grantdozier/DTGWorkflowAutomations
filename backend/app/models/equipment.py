from sqlalchemy import Column, String, DateTime, func, ForeignKey, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class InternalEquipment(Base):
    """Company-owned equipment (distinct from rental rates)"""
    __tablename__ = "internal_equipment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    name = Column(String, nullable=False)
    equipment_type = Column(String, nullable=False)  # excavator, loader, truck, etc.
    model = Column(String)
    serial_number = Column(String)

    purchase_price = Column(Numeric(15, 2))
    hourly_cost = Column(Numeric(10, 2), nullable=False)  # Operating cost per hour

    is_available = Column(Boolean, default=True)
    condition = Column(String, default="good")  # good, fair, poor, maintenance, out_of_service

    notes = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
