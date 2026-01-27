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
from app.ai.spec_parser import spec_parser
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

    # Allow parsing of plan, spec, plan_and_spec, and addendum documents
    allowed_types = ["plan", "spec", "plan_and_spec", "addendum"]
    if document.doc_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only parse documents of type: {', '.join(allowed_types)}"
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
        method = result.get("method", "unknown")

        return {
            "success": True,
            "document_id": document_id,
            "pages_analyzed": result.get("pages_analyzed", max_pages),
            "method": method,
            "strategy": result.get("strategy"),
            "confidence": result.get("confidence"),
            "processing_time_ms": result.get("processing_time_ms"),
            "metadata": result.get("metadata"),
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
    # Verify project ownership
    logger.info(f"[PARSE] Step 1/4: Verifying project access...")
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
    logger.info(f"[PARSE] Step 2/4: Loading document...")
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
            detail="Document file not found on disk"
        )

    # Parse the document
    logger.info(f"[PARSE] Step 3/4: Parsing with AI (this may take 30-60 seconds)...")
    logger.info(f"[PARSE] Processing {max_pages} pages with Claude Vision...")

    parse_result = await plan_parser.parse_plan(file_path, max_pages=max_pages)

    if not parse_result.get("success", False):
        logger.error(f"[PARSE] Parsing failed: {parse_result.get('error')}")
        return {
            "success": False,
            "error": parse_result.get("error", "Unknown error"),
            "items_saved": 0
        }

    # Extract parsed data
    parsed_data = parse_result.get("data")
    items_saved = 0

    # Count what we extracted
    bid_items = parsed_data.get("bid_items", []) if parsed_data else []
    materials = parsed_data.get("materials", []) if parsed_data else []

    logger.info(f"[PARSE] Extraction complete: {len(bid_items)} bid items, {len(materials)} materials")

    if not parsed_data or (not bid_items and not materials):
        logger.warning("[PARSE] No data extracted from document")
        return {
            "success": True,
            "message": "Parsing succeeded but no items were extracted. The document may not contain itemized materials or the format may not be recognized.",
            "items_saved": 0,
            "extraction_details": {
                "bid_items_found": 0,
                "materials_found": 0,
                "method": parse_result.get("method", "unknown")
            }
        }

    try:
        logger.info(f"[PARSE] Step 4/4: Saving {len(bid_items) + len(materials)} items to database...")

        # Save bid items as takeoff items
        if bid_items:
            for item in bid_items:
                # Ensure qty is never null - default to 0 if not provided
                qty_value = item.get("quantity")
                if qty_value is None:
                    qty_value = 0
                
                takeoff = TakeoffItem(
                    project_id=project_id,
                    label=item.get("description", "Unknown item"),
                    qty=qty_value,
                    unit=item.get("unit", "") or "",
                    notes=f"Item #{item.get('item_number', 'N/A')}"
                )
                db.add(takeoff)
                items_saved += 1

        # Save materials as takeoff items
        if materials:
            for mat in materials:
                # Ensure qty is never null - default to 0 if not provided
                qty_value = mat.get("quantity")
                if qty_value is None:
                    qty_value = 0
                
                category = mat.get("category", "")
                
                takeoff = TakeoffItem(
                    project_id=project_id,
                    label=mat.get("name", "Unknown material"),
                    qty=qty_value,
                    unit=mat.get("unit", "ea") or "ea",
                    category=category,
                    notes="Extracted from plan by AI"
                )
                db.add(takeoff)
                items_saved += 1
                logger.info(f"[PARSE]   Added: {mat.get('name')} x {qty_value} {mat.get('unit', 'ea')} [{category}]")

        # Mark document as parsed
        document.is_parsed = "true"
        
        # Commit all changes
        db.commit()
        logger.info(f"[PARSE] SUCCESS! Saved {items_saved} items to database")

        return {
            "success": True,
            "message": f"Successfully parsed and saved {items_saved} items",
            "items_saved": items_saved,
            "extraction_details": {
                "bid_items_found": len(bid_items),
                "materials_found": len(materials),
                "method": parse_result.get("method", "unknown"),
                "pages_analyzed": parse_result.get("pages_analyzed", max_pages)
            },
            "parse_result": parse_result
        }

    except Exception as e:
        db.rollback()
        logger.error(f"[PARSE] Failed to save parsed data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save parsed data: {str(e)}"
        )


@router.post("/projects/{project_id}/documents/{document_id}/parse-spec")
async def parse_specification_document(
    project_id: str,
    document_id: str,
    max_pages: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Parse a specification document using text extraction + LLM structuring

    This endpoint analyzes specification documents and extracts:
    - Division and section structure
    - Referenced standards (ASTM, AASHTO, etc.)
    - Material requirements
    - Installation procedures
    - Quality control requirements

    **max_pages**: Number of pages to analyze (1-100, default: 50)
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

    # Check document type
    if document.doc_type != "spec":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This endpoint is for specification documents. Use /parse for plans."
        )

    # Get file path
    file_path = file_storage.get_file_path(document.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on disk"
        )

    # Validate max_pages
    if max_pages < 1 or max_pages > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_pages must be between 1 and 100"
        )

    # Parse the specification
    try:
        result = await spec_parser.parse_specification(file_path, max_pages=max_pages)

        if not result["success"]:
            return {
                "success": False,
                "document_id": document_id,
                "method": result.get("method", "unknown"),
                "error": result.get("error", "Unknown error")
            }

        return {
            "success": True,
            "document_id": document_id,
            "pages_analyzed": result.get("pages_analyzed", 0),
            "method": result.get("method", "text_extraction"),
            "extraction_method": result.get("extraction_method"),
            "is_scanned": result.get("is_scanned", False),
            "character_count": result.get("character_count", 0),
            "processing_time_ms": result.get("processing_time_ms"),
            "data": result.get("data")
        }

    except Exception as e:
        logger.error(f"Failed to parse specification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse specification: {str(e)}"
        )
