from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.specification import SpecificationLibrary, ProjectSpecification
from app.models.project import Project
from app.services.specification_service import SpecificationService
from app.api.v1.schemas.specification import (
    SpecificationLibraryCreate,
    SpecificationLibraryUpdate,
    SpecificationLibraryResponse,
    ProjectSpecificationCreate,
    ProjectSpecificationResponse,
    SpecificationMatchRequest,
    SpecificationMatchResult,
    SpecificationSearchRequest,
    ProjectSpecificationVerify,
    SpecificationListResponse,
    ProjectSpecificationListResponse
)

router = APIRouter()


# ========== Specification Library Management ==========

@router.get("/specifications/search", response_model=List[SpecificationLibraryResponse])
async def search_specifications(
    query: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search specification library"""
    specs = SpecificationService.search_specifications(
        query=query,
        category=category,
        source=source,
        db=db,
        limit=limit
    )
    return specs


@router.get("/specifications/{spec_code}", response_model=SpecificationLibraryResponse)
async def get_specification(
    spec_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specification details by code"""
    spec = db.query(SpecificationLibrary).filter(
        SpecificationLibrary.spec_code == spec_code.upper()
    ).first()

    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specification not found"
        )

    return spec


@router.post("/specifications", response_model=SpecificationLibraryResponse, status_code=status.HTTP_201_CREATED)
async def create_specification(
    spec_data: SpecificationLibraryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add specification to library (admin only)"""
    # Check if spec code already exists
    existing = db.query(SpecificationLibrary).filter(
        SpecificationLibrary.spec_code == spec_data.spec_code.upper()
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Specification code already exists"
        )

    spec = SpecificationLibrary(
        **spec_data.dict(),
        spec_code=spec_data.spec_code.upper()
    )
    db.add(spec)
    db.commit()
    db.refresh(spec)
    return spec


@router.put("/specifications/{spec_code}", response_model=SpecificationLibraryResponse)
async def update_specification(
    spec_code: str,
    spec_data: SpecificationLibraryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update specification in library"""
    spec = db.query(SpecificationLibrary).filter(
        SpecificationLibrary.spec_code == spec_code.upper()
    ).first()

    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specification not found"
        )

    update_data = spec_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "spec_code" and value:
            value = value.upper()
        setattr(spec, field, value)

    db.commit()
    db.refresh(spec)
    return spec


@router.delete("/specifications/{spec_code}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_specification(
    spec_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete specification from library"""
    spec = db.query(SpecificationLibrary).filter(
        SpecificationLibrary.spec_code == spec_code.upper()
    ).first()

    if not spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Specification not found"
        )

    db.delete(spec)
    db.commit()
    return None


@router.get("/specifications", response_model=SpecificationListResponse)
async def list_specifications(
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all specifications in library"""
    query = db.query(SpecificationLibrary)

    if category:
        query = query.filter(SpecificationLibrary.category == category)
    if source:
        query = query.filter(SpecificationLibrary.source == source)

    total = query.count()
    specs = query.order_by(SpecificationLibrary.spec_code).offset(skip).limit(limit).all()

    return SpecificationListResponse(
        total=total,
        specifications=specs
    )


# ========== Project Specifications ==========

@router.get("/projects/{project_id}/specs", response_model=ProjectSpecificationListResponse)
async def get_project_specifications(
    project_id: UUID,
    verified_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all specifications for a project"""
    # Verify project access
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    query = db.query(ProjectSpecification).filter(
        ProjectSpecification.project_id == project_id
    )

    if verified_only:
        query = query.filter(ProjectSpecification.is_verified == "verified")

    total = query.count()

    # Get counts by verification status
    verified_count = db.query(func.count(ProjectSpecification.id)).filter(
        ProjectSpecification.project_id == project_id,
        ProjectSpecification.is_verified == "verified"
    ).scalar()

    pending_count = db.query(func.count(ProjectSpecification.id)).filter(
        ProjectSpecification.project_id == project_id,
        ProjectSpecification.is_verified == "pending"
    ).scalar()

    rejected_count = db.query(func.count(ProjectSpecification.id)).filter(
        ProjectSpecification.project_id == project_id,
        ProjectSpecification.is_verified == "rejected"
    ).scalar()

    # Get project specs with library data joined
    project_specs = query.order_by(ProjectSpecification.source_page).offset(skip).limit(limit).all()

    # Enrich with library data
    enriched_specs = []
    for ps in project_specs:
        spec_data = ProjectSpecificationResponse.from_orm(ps)

        # Add library data if matched
        if ps.specification_id:
            lib_spec = db.query(SpecificationLibrary).filter(
                SpecificationLibrary.id == ps.specification_id
            ).first()
            if lib_spec:
                spec_data.spec_code = lib_spec.spec_code
                spec_data.title = lib_spec.title
                spec_data.source = lib_spec.source

        enriched_specs.append(spec_data)

    return ProjectSpecificationListResponse(
        total=total,
        verified_count=verified_count,
        pending_count=pending_count,
        rejected_count=rejected_count,
        specifications=enriched_specs
    )


@router.post("/projects/{project_id}/specs", response_model=ProjectSpecificationResponse, status_code=status.HTTP_201_CREATED)
async def add_project_specification(
    project_id: UUID,
    spec_data: ProjectSpecificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually add specification to project"""
    # Verify project access
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Try to match specification if not provided
    if not spec_data.specification_id:
        matched_spec, confidence = SpecificationService.match_specification_code(
            spec_data.extracted_code,
            spec_data.context,
            db
        )
        if matched_spec:
            spec_data.specification_id = matched_spec.id

    project_spec = ProjectSpecification(
        **spec_data.dict(),
        project_id=project_id
    )
    db.add(project_spec)
    db.commit()
    db.refresh(project_spec)

    return project_spec


@router.patch("/projects/{project_id}/specs/{spec_id}/verify", response_model=ProjectSpecificationResponse)
async def verify_project_specification(
    project_id: UUID,
    spec_id: UUID,
    verify_data: ProjectSpecificationVerify,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verify or reject a project specification"""
    project_spec = db.query(ProjectSpecification).join(Project).filter(
        ProjectSpecification.id == spec_id,
        ProjectSpecification.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project_spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project specification not found"
        )

    try:
        updated_spec = SpecificationService.verify_project_specification(
            spec_id,
            verify_data.is_verified,
            verify_data.notes,
            db
        )
        return updated_spec
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/specifications/match", response_model=List[SpecificationMatchResult])
async def match_specifications(
    match_request: SpecificationMatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Match specification codes to library (bulk operation)"""
    results = SpecificationService.bulk_match_specifications(
        match_request.codes,
        db
    )
    return results


@router.delete("/projects/{project_id}/specs/{spec_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_specification(
    project_id: UUID,
    spec_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete project specification"""
    project_spec = db.query(ProjectSpecification).join(Project).filter(
        ProjectSpecification.id == spec_id,
        ProjectSpecification.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project_spec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project specification not found"
        )

    db.delete(project_spec)
    db.commit()
    return None
