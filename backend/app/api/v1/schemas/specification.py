from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from decimal import Decimal


class SpecificationLibraryBase(BaseModel):
    spec_code: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    requirements: Optional[str] = None
    source: str = Field(..., min_length=1)
    cached_content: Optional[str] = None
    external_url: Optional[str] = None


class SpecificationLibraryCreate(SpecificationLibraryBase):
    pass


class SpecificationLibraryUpdate(BaseModel):
    spec_code: Optional[str] = None
    category: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    source: Optional[str] = None
    cached_content: Optional[str] = None
    external_url: Optional[str] = None


class SpecificationLibraryResponse(SpecificationLibraryBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ProjectSpecificationBase(BaseModel):
    extracted_code: str
    context: Optional[str] = None
    source_page: Optional[int] = None
    notes: Optional[str] = None


class ProjectSpecificationCreate(ProjectSpecificationBase):
    specification_id: Optional[UUID] = None


class ProjectSpecificationResponse(ProjectSpecificationBase):
    id: UUID
    project_id: UUID
    specification_id: Optional[UUID]
    confidence_score: Optional[Decimal]
    is_verified: str
    created_at: datetime
    updated_at: Optional[datetime]

    # Joined data from library
    spec_code: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None

    class Config:
        from_attributes = True


class SpecificationMatchRequest(BaseModel):
    codes: List[str] = Field(..., min_items=1, max_items=100)


class SpecificationMatchResult(BaseModel):
    input_code: str
    matched: bool
    confidence: float
    confidence_level: str  # high, medium, low
    spec_id: Optional[str] = None
    spec_code: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None


class SpecificationSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    source: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)


class ProjectSpecificationVerify(BaseModel):
    is_verified: str = Field(..., pattern="^(verified|rejected|pending)$")
    notes: Optional[str] = None


class SpecificationListResponse(BaseModel):
    total: int
    specifications: List[SpecificationLibraryResponse]


class ProjectSpecificationListResponse(BaseModel):
    total: int
    verified_count: int
    pending_count: int
    rejected_count: int
    specifications: List[ProjectSpecificationResponse]
