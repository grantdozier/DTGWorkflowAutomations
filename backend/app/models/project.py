from sqlalchemy import Column, String, DateTime, func, ForeignKey, Numeric, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    name = Column(String, nullable=False)
    job_number = Column(String, unique=True, nullable=False, index=True)
    location = Column(String)
    type = Column(String)  # state, private, federal, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProjectDocument(Base):
    __tablename__ = "project_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    doc_type = Column(String, nullable=False)  # plan, spec, addendum, etc.
    file_path = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())


class BidItem(Base):
    __tablename__ = "bid_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectBidItem(Base):
    __tablename__ = "project_bid_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    bid_item_id = Column(UUID(as_uuid=True), ForeignKey("bid_items.id"), nullable=False)

    bid_qty = Column(Numeric(15, 2))
    bid_unit_price = Column(Numeric(15, 2))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class HistoricalProject(Base):
    """Imported past projects for productivity analysis"""
    __tablename__ = "historical_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    name = Column(String, nullable=False)
    job_number = Column(String, nullable=False, index=True)
    completion_date = Column(Date)

    original_bid = Column(Numeric(15, 2))
    final_cost = Column(Numeric(15, 2))
    profit_margin = Column(Numeric(5, 2))  # Percentage

    import_source = Column(String)  # csv, quickbooks, procore, etc.
    notes = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
