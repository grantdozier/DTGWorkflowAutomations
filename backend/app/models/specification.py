from sqlalchemy import Column, String, DateTime, func, ForeignKey, Text, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core.database import Base


class SpecificationLibrary(Base):
    """External specification database (ASTM, ACI, AASHTO, etc.)"""
    __tablename__ = "specifications_library"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    spec_code = Column(String, unique=True, nullable=False, index=True)
    category = Column(String)  # Cement, Concrete, Asphalt, Steel, etc.
    title = Column(String, nullable=False)
    description = Column(Text)

    requirements = Column(Text)  # Key requirements summary
    source = Column(String, nullable=False)  # ASTM, AASHTO, ACI, etc.

    cached_content = Column(Text)  # Full spec content if available
    external_url = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ProjectSpecification(Base):
    """Specifications extracted from project documents and matched to library"""
    __tablename__ = "project_specifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    specification_id = Column(UUID(as_uuid=True), ForeignKey("specifications_library.id"))

    extracted_code = Column(String, nullable=False)  # Code as found in document
    context = Column(Text)  # Surrounding text for context
    source_page = Column(Integer)

    confidence_score = Column(Numeric(5, 2))  # Match confidence (0-100)
    is_verified = Column(String, default="pending")  # pending, verified, rejected

    notes = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
