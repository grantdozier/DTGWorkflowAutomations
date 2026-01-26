from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectDocument, BidItem, ProjectBidItem
from app.models.estimation import TakeoffItem
from app.api.v1.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    ProjectDocumentResponse,
    BidItemResponse,
    ProjectBidItemCreate,
    ProjectBidItemUpdate,
    ProjectBidItemResponse
)

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project for the current user's company
    """
    # Check if job number already exists
    existing = db.query(Project).filter(
        Project.job_number == project_data.job_number
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Project with job number '{project_data.job_number}' already exists"
        )

    # Create project
    project = Project(
        company_id=current_user.company_id,
        **project_data.model_dump()
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all projects for the current user's company
    Optional filtering by project type
    """
    query = db.query(Project).filter(Project.company_id == current_user.company_id)

    # Filter by type if provided
    if type:
        query = query.filter(Project.type == type)

    # Get total count
    total = query.count()

    # Get paginated results
    projects = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "projects": projects
    }


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific project by ID
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a project
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    # Update fields
    update_data = project_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project
    """
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    db.delete(project)
    db.commit()

    return None


@router.get("/{project_id}/documents", response_model=list[ProjectDocumentResponse])
async def list_project_documents(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all documents for a project
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

    documents = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == project_id
    ).all()

    return documents


@router.get("/{project_id}/bid-items", response_model=list[ProjectBidItemResponse])
async def list_project_bid_items(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all bid items for a project
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

    bid_items = db.query(ProjectBidItem).filter(
        ProjectBidItem.project_id == project_id
    ).all()

    # Load related bid item data
    for item in bid_items:
        item.bid_item = db.query(BidItem).filter(BidItem.id == item.bid_item_id).first()

    return bid_items


@router.post("/{project_id}/bid-items", response_model=ProjectBidItemResponse, status_code=status.HTTP_201_CREATED)
async def add_project_bid_item(
    project_id: str,
    bid_item_data: ProjectBidItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a bid item to a project
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

    # Verify bid item exists
    bid_item = db.query(BidItem).filter(BidItem.id == bid_item_data.bid_item_id).first()
    if not bid_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bid item not found"
        )

    # Create project bid item
    project_bid_item = ProjectBidItem(
        project_id=project_id,
        **bid_item_data.model_dump()
    )

    db.add(project_bid_item)
    db.commit()
    db.refresh(project_bid_item)

    # Load bid item data
    project_bid_item.bid_item = bid_item

    return project_bid_item


# ============================================================
# TAKEOFF ITEMS ENDPOINTS
# ============================================================

@router.get("/{project_id}/takeoffs")
async def list_project_takeoffs(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all takeoff items for a project
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

    takeoffs = db.query(TakeoffItem).filter(
        TakeoffItem.project_id == project_id
    ).all()

    return [
        {
            "id": str(t.id),
            "label": t.label,
            "description": t.notes or "",
            "quantity": float(t.qty) if t.qty else 0,
            "unit": t.unit,
            "source_page": t.source_page,
            "category": None,
            "quote_status": None,
        }
        for t in takeoffs
    ]


@router.post("/{project_id}/takeoffs", status_code=status.HTTP_201_CREATED)
async def create_project_takeoff(
    project_id: str,
    takeoff_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new takeoff item for a project
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

    takeoff = TakeoffItem(
        project_id=project_id,
        label=takeoff_data.get("label", "New Item"),
        qty=takeoff_data.get("quantity", 0),
        unit=takeoff_data.get("unit", "EA"),
        notes=takeoff_data.get("description", ""),
        source_page=takeoff_data.get("source_page"),
    )

    db.add(takeoff)
    db.commit()
    db.refresh(takeoff)

    return {
        "id": str(takeoff.id),
        "label": takeoff.label,
        "description": takeoff.notes or "",
        "quantity": float(takeoff.qty) if takeoff.qty else 0,
        "unit": takeoff.unit,
        "source_page": takeoff.source_page,
        "category": None,
        "quote_status": None,
    }


@router.patch("/{project_id}/takeoffs/{takeoff_id}")
async def update_project_takeoff(
    project_id: str,
    takeoff_id: str,
    takeoff_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a takeoff item
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

    takeoff = db.query(TakeoffItem).filter(
        TakeoffItem.id == takeoff_id,
        TakeoffItem.project_id == project_id
    ).first()

    if not takeoff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Takeoff item not found"
        )

    # Map frontend fields to model fields
    field_mapping = {
        "label": "label",
        "description": "notes",
        "quantity": "qty",
        "unit": "unit",
        "source_page": "source_page",
    }

    for frontend_field, model_field in field_mapping.items():
        if frontend_field in takeoff_data:
            setattr(takeoff, model_field, takeoff_data[frontend_field])

    db.commit()
    db.refresh(takeoff)

    return {
        "id": str(takeoff.id),
        "label": takeoff.label,
        "description": takeoff.notes or "",
        "quantity": float(takeoff.qty) if takeoff.qty else 0,
        "unit": takeoff.unit,
        "source_page": takeoff.source_page,
        "category": None,
        "quote_status": None,
    }


@router.delete("/{project_id}/takeoffs/{takeoff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project_takeoff(
    project_id: str,
    takeoff_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a takeoff item
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

    takeoff = db.query(TakeoffItem).filter(
        TakeoffItem.id == takeoff_id,
        TakeoffItem.project_id == project_id
    ).first()

    if not takeoff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Takeoff item not found"
        )

    db.delete(takeoff)
    db.commit()

    return None
