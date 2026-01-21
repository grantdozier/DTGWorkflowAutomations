from sqlalchemy import Column, String, DateTime, func, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class TakeoffItem(Base):
    __tablename__ = "takeoff_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    label = Column(String, nullable=False)
    qty = Column(Numeric(15, 2), nullable=False)
    unit = Column(String, nullable=False)
    source_page = Column(Integer)  # Page number from PDF
    notes = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    vendor_name = Column(String, nullable=False)
    vendor_email = Column(String)
    vendor_phone = Column(String)

    item_description = Column(String, nullable=False)
    quantity = Column(Numeric(15, 2))
    unit_price = Column(Numeric(15, 2))
    total_price = Column(Numeric(15, 2))

    status = Column(String, default="pending")  # pending, accepted, rejected
    received_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Estimate(Base):
    __tablename__ = "estimates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # Cost breakdown
    materials_cost = Column(Numeric(15, 2), default=0)
    labor_cost = Column(Numeric(15, 2), default=0)
    equipment_cost = Column(Numeric(15, 2), default=0)
    subcontractor_cost = Column(Numeric(15, 2), default=0)
    overhead = Column(Numeric(15, 2), default=0)
    profit = Column(Numeric(15, 2), default=0)
    total_cost = Column(Numeric(15, 2), nullable=False)

    # Metadata
    confidence_score = Column(Numeric(5, 2))  # 0-100
    notes = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
