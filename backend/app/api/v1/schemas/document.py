from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document"""
    id: str
    project_id: str
    doc_type: str
    file_path: str
    filename: str
    file_size: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Document list item"""
    id: str
    project_id: str
    doc_type: str
    file_path: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentDeleteResponse(BaseModel):
    """Response after deleting a document"""
    success: bool
    message: str
