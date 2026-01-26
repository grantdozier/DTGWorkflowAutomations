from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    id: UUID
    project_id: UUID
    doc_type: str
    file_path: str
    filename: str
    file_size: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Document list item"""
    id: UUID
    project_id: UUID
    doc_type: str
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentDeleteResponse(BaseModel):
    """Response after deleting a document"""
    success: bool
    message: str
