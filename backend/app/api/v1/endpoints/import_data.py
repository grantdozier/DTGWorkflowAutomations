from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from io import BytesIO

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import HistoricalProject
from app.models.estimation import HistoricalEstimate
from app.models.material import Material
from app.services.import_service import ImportService
from app.api.v1.schemas.import_data import ImportValidationResult, ImportResult

router = APIRouter()


@router.post("/projects/validate", response_model=ImportValidationResult)
async def validate_projects_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Validate historical projects CSV/Excel file before import"""
    content = await file.read()
    valid_rows, errors = ImportService.validate_historical_projects(content, file.filename)

    return ImportValidationResult(
        valid_rows=len(valid_rows),
        error_count=len(errors),
        errors=[e.to_dict() for e in errors]
    )


@router.post("/projects", response_model=ImportResult)
async def import_historical_projects(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import historical projects from CSV/Excel file"""
    content = await file.read()
    valid_rows, errors = ImportService.validate_historical_projects(content, file.filename)

    if len(errors) > 0:
        # Still import valid rows if any exist
        if len(valid_rows) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No valid rows to import. {len(errors)} errors found."
            )

    imported_ids = []
    success_count = 0

    try:
        for row_data in valid_rows:
            project = HistoricalProject(
                **row_data,
                company_id=current_user.company_id
            )
            db.add(project)
            db.flush()
            imported_ids.append(str(project.id))
            success_count += 1

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import projects: {str(e)}"
        )

    return ImportResult(
        success_count=success_count,
        error_count=len(errors),
        errors=[e.to_dict() for e in errors],
        imported_ids=imported_ids
    )


@router.post("/estimates/validate", response_model=ImportValidationResult)
async def validate_estimates_import(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Validate historical estimates CSV/Excel file before import"""
    content = await file.read()
    valid_rows, errors = ImportService.validate_historical_estimates(content, file.filename)

    return ImportValidationResult(
        valid_rows=len(valid_rows),
        error_count=len(errors),
        errors=[e.to_dict() for e in errors]
    )


@router.post("/estimates", response_model=ImportResult)
async def import_historical_estimates(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import historical estimates from CSV/Excel file"""
    content = await file.read()
    valid_rows, errors = ImportService.validate_historical_estimates(content, file.filename)

    if len(errors) > 0:
        if len(valid_rows) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No valid rows to import. {len(errors)} errors found."
            )

    imported_ids = []
    success_count = 0

    try:
        for row_data in valid_rows:
            # Find project by job_number if provided
            historical_project_id = None
            if row_data.get('job_number'):
                project = db.query(HistoricalProject).filter(
                    HistoricalProject.job_number == row_data['job_number'],
                    HistoricalProject.company_id == current_user.company_id
                ).first()
                if project:
                    historical_project_id = project.id

            # Remove job_number from row_data as it's not a field in HistoricalEstimate
            job_number = row_data.pop('job_number', None)

            estimate = HistoricalEstimate(
                **row_data,
                company_id=current_user.company_id,
                historical_project_id=historical_project_id
            )
            db.add(estimate)
            db.flush()
            imported_ids.append(str(estimate.id))
            success_count += 1

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import estimates: {str(e)}"
        )

    return ImportResult(
        success_count=success_count,
        error_count=len(errors),
        errors=[e.to_dict() for e in errors],
        imported_ids=imported_ids
    )


@router.get("/projects/template")
async def download_projects_template():
    """Download CSV template for historical projects import (public endpoint)"""
    template = ImportService.generate_projects_template()

    return StreamingResponse(
        BytesIO(template),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=historical_projects_template.csv"
        }
    )


@router.get("/estimates/template")
async def download_estimates_template():
    """Download CSV template for historical estimates import (public endpoint)"""
    template = ImportService.generate_estimates_template()

    return StreamingResponse(
        BytesIO(template),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=historical_estimates_template.csv"
        }
    )


@router.post("/scrape-materials")
async def scrape_materials(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Scrape materials from web sources and import into the material catalog.
    
    This is a placeholder endpoint - actual web scraping implementation
    would need to be added based on specific vendor websites.
    """
    # For now, return a message indicating this needs implementation
    # In production, this would call a scraping service
    
    # Count existing materials
    existing_count = db.query(Material).filter(
        Material.company_id == current_user.company_id
    ).count()
    
    return {
        "success": True,
        "message": "Material scraping endpoint ready. Configure scraping sources in settings.",
        "existing_materials": existing_count,
        "imported_count": 0,
        "note": "Web scraping requires configuration of vendor websites and API keys"
    }
