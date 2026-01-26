from sqlalchemy import Column, String, DateTime, func, ForeignKey, Numeric, Integer, Text, Date
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
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"))
    takeoff_item_id = Column(UUID(as_uuid=True), ForeignKey("takeoff_items.id"))

    # Vendor info (denormalized for historical record if vendor deleted)
    vendor_name = Column(String, nullable=False)
    vendor_email = Column(String)
    vendor_phone = Column(String)

    # Quote details
    item_description = Column(String, nullable=False)
    quantity = Column(Numeric(15, 2))
    unit = Column(String)
    unit_price = Column(Numeric(15, 2))
    total_price = Column(Numeric(15, 2))

    # Lead time and availability
    lead_time_days = Column(Integer)
    notes = Column(Text)

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


class HistoricalEstimate(Base):
    """Granular estimate data from past projects"""
    __tablename__ = "historical_estimates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    historical_project_id = Column(UUID(as_uuid=True), ForeignKey("historical_projects.id"))

    bid_item_code = Column(String, index=True)
    description = Column(String, nullable=False)
    quantity = Column(Numeric(15, 2), nullable=False)
    unit = Column(String, nullable=False)

    materials_cost = Column(Numeric(15, 2))
    labor_hours = Column(Numeric(10, 2))
    labor_cost = Column(Numeric(15, 2))
    equipment_cost = Column(Numeric(15, 2))

    productivity_rate = Column(Numeric(10, 4))  # Units per hour

    notes = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class QuoteRequest(Base):
    """Track quote request emails sent to vendors"""
    __tablename__ = "quote_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    vendor_id = Column(UUID(as_uuid=True), ForeignKey("vendors.id"), nullable=False)

    email_subject = Column(String, nullable=False)
    email_body = Column(Text, nullable=False)

    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="sent")  # sent, opened, responded, expired
    expected_response_date = Column(Date)

    # Track which takeoff items were requested
    requested_items = Column(Text)  # JSON string of takeoff item IDs

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class BidItemDiscrepancy(Base):
    """Detected mismatches between bid quantities and plan quantities"""
    __tablename__ = "bid_item_discrepancies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    project_bid_item_id = Column(UUID(as_uuid=True), ForeignKey("project_bid_items.id"))
    takeoff_item_id = Column(UUID(as_uuid=True), ForeignKey("takeoff_items.id"))

    discrepancy_type = Column(String, nullable=False)  # quantity_mismatch, missing_item, extra_item
    severity = Column(String, nullable=False)  # critical, high, medium, low

    bid_quantity = Column(Numeric(15, 2))
    plan_quantity = Column(Numeric(15, 2))
    difference_percentage = Column(Numeric(5, 2))

    description = Column(Text)
    recommendation = Column(Text)

    status = Column(String, default="open")  # open, resolved, ignored
    resolution_notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
