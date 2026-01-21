from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectDocument
from app.services.file_storage import file_storage
from app.api.v1.schemas.document import (
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDeleteResponse
)

router = APIRouter()

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".PDF"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file"""
    # Check extension
    file_ext = Path(file.filename).suffix
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )


@router.post("/projects/{project_id}/documents", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_project_document(
    project_id: str,
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload a document (plan or spec) to a project

    - **project_id**: Project ID
    - **file**: PDF file to upload
    - **doc_type**: Document type (plan, spec)
    """
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Validate file
    validate_file(file)

    # Validate doc_type
    if doc_type not in ["plan", "spec"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="doc_type must be 'plan' or 'spec'"
        )

    # Save file to disk
    try:
        file_path = await file_storage.save_file(file, doc_type, project_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

    # Create database record
    document = ProjectDocument(
        project_id=project_id,
        doc_type=doc_type,
        file_path=file_path
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Get file size
    file_size = file_storage.get_file_size(file_path)

    return {
        **document.__dict__,
        "filename": file.filename,
        "file_size": file_size
    }


@router.get("/projects/{project_id}/documents", response_model=list[DocumentListResponse])
async def list_project_documents(
    project_id: str,
    doc_type: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents for a project

    Optional filter by doc_type (plan, spec)
    """
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Query documents
    query = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)

    if doc_type:
        query = query.filter(ProjectDocument.doc_type == doc_type)

    documents = query.all()

    return documents


@router.get("/projects/{project_id}/documents/{document_id}")
async def download_project_document(
    project_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a project document
    """
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Get document
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Get file path
    file_path = file_storage.get_file_path(document.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk"
        )

    # Return file
    return FileResponse(
        path=file_path,
        filename=f"{document.doc_type}_{document_id}.pdf",
        media_type="application/pdf"
    )


@router.delete("/projects/{project_id}/documents/{document_id}", response_model=DocumentDeleteResponse)
async def delete_project_document(
    project_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project document
    """
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Get document
    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == document_id,
        ProjectDocument.project_id == project_id
    ).first()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # Delete file from disk
    file_deleted = file_storage.delete_file(document.file_path)

    # Delete database record
    db.delete(document)
    db.commit()

    return {
        "success": True,
        "message": f"Document deleted {'with file' if file_deleted else 'but file was already missing'}"
    }
