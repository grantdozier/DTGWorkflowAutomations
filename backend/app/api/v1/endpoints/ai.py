from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectDocument
from app.models.estimation import TakeoffItem
from app.services.file_storage import file_storage
from app.ai.config import is_ai_available
from app.ai.plan_parser import plan_parser
from app.ai.ocr_service import ocr_service
from app.api.v1.schemas.ai import (
    ParsePlanResponse,
    ParseStatusResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status", response_model=ParseStatusResponse)
async def get_ai_status(current_user: User = Depends(get_current_user)):
    """
    Check status of AI services
    """
    ai_status = is_ai_available()

    return {
        "claude_available": ai_status["claude"],
        "openai_available": ai_status["openai"],
        "ocr_available": ocr_service.tesseract_available,
        "message": "AI services configured" if ai_status["any"] else "No AI services configured. Add API keys to .env file."
    }


@router.post("/projects/{project_id}/documents/{document_id}/parse", response_model=ParsePlanResponse)
async def parse_plan_document(
    project_id: str,
    document_id: str,
    max_pages: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parse a plan document using AI vision models

    This endpoint analyzes construction plans and extracts:
    - Bid items with quantities and units
    - Specifications and material requirements
    - Project information

    **max_pages**: Number of pages to analyze (1-10, default: 5)
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

    # Verify document type is plan
    if document.doc_type != "plan":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only parse 'plan' documents. Use doc_type='plan' when uploading."
        )

    # Get file path
    file_path = file_storage.get_file_path(document.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on disk"
        )

    # Validate max_pages
    if max_pages < 1 or max_pages > 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_pages must be between 1 and 10"
        )

    # Parse the plan
    try:
        result = await plan_parser.parse_plan(file_path, max_pages=max_pages)

        if not result["success"]:
            return {
                "success": False,
                "document_id": document_id,
                "method": result.get("method", "unknown"),
                "error": result.get("error", "Unknown error")
            }

        # Determine method used
        method = "claude" if is_ai_available()["claude"] else "ocr"

        return {
            "success": True,
            "document_id": document_id,
            "pages_analyzed": result.get("pages_analyzed", max_pages),
            "method": method,
            "data": result.get("data")
        }

    except Exception as e:
        logger.error(f"Failed to parse document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse document: {str(e)}"
        )


@router.post("/projects/{project_id}/documents/{document_id}/parse-and-save")
async def parse_and_save_plan_document(
    project_id: str,
    document_id: str,
    max_pages: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parse a plan document and save extracted items to database

    This endpoint:
    1. Parses the document using AI
    2. Saves bid items to the database
    3. Saves takeoff items to the database
    4. Returns summary of saved items
    """
    # First, parse the document
    parse_result = await parse_plan_document(
        project_id, document_id, max_pages, current_user, db
    )

    if not parse_result.success:
        return {
            "success": False,
            "error": parse_result.error,
            "items_saved": 0
        }

    # Extract parsed data
    parsed_data = parse_result.data
    items_saved = 0

    if not parsed_data:
        return {
            "success": True,
            "message": "Parsing succeeded but no data extracted",
            "items_saved": 0
        }

    try:
        # Save bid items as takeoff items
        if "bid_items" in parsed_data and parsed_data["bid_items"]:
            for item in parsed_data["bid_items"]:
                takeoff = TakeoffItem(
                    project_id=project_id,
                    label=item.get("description", "Unknown item"),
                    qty=item.get("quantity", 0),
                    unit=item.get("unit", ""),
                    notes=f"Item #{item.get('item_number', 'N/A')}"
                )
                db.add(takeoff)
                items_saved += 1

        # Commit all changes
        db.commit()

        return {
            "success": True,
            "message": f"Successfully parsed and saved {items_saved} items",
            "items_saved": items_saved,
            "parse_result": parse_result
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save parsed data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save parsed data: {str(e)}"
        )
