from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from collections import defaultdict

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.estimation import BidItemDiscrepancy
from app.models.project import Project
from app.services.discrepancy_detector import DiscrepancyDetector
from app.api.v1.schemas.discrepancy import (
    DiscrepancyResponse,
    DiscrepancyDetectionResponse,
    DiscrepancyResolve,
    DiscrepancyListResponse,
    DiscrepancySummary
)

router = APIRouter()


@router.post("/projects/{project_id}/discrepancies/detect", response_model=DiscrepancyDetectionResponse)
async def detect_discrepancies(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run discrepancy detection for a project"""
    # Verify project exists and belongs to user's company
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    try:
        # Run discrepancy detection
        discrepancies = DiscrepancyDetector.detect_discrepancies(project_id, db)

        # Get summary
        summary = DiscrepancyDetector.get_discrepancy_summary(project_id, db)

        return DiscrepancyDetectionResponse(
            total_discrepancies=len(discrepancies),
            discrepancies=discrepancies,
            summary=summary
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect discrepancies: {str(e)}"
        )


@router.get("/projects/{project_id}/discrepancies", response_model=DiscrepancyListResponse)
async def list_discrepancies(
    project_id: UUID,
    discrepancy_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all discrepancies for a project with optional filters"""
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

    query = db.query(BidItemDiscrepancy).filter(
        BidItemDiscrepancy.project_id == project_id
    )

    if discrepancy_type:
        query = query.filter(BidItemDiscrepancy.discrepancy_type == discrepancy_type)
    if severity:
        query = query.filter(BidItemDiscrepancy.severity == severity)
    if status_filter:
        query = query.filter(BidItemDiscrepancy.status == status_filter)

    total = query.count()

    # Get statistics
    all_discrepancies = query.all()

    by_severity = defaultdict(int)
    by_type = defaultdict(int)
    by_status = defaultdict(int)

    for disc in all_discrepancies:
        by_severity[disc.severity] += 1
        by_type[disc.discrepancy_type] += 1
        by_status[disc.status] += 1

    # Get paginated results
    discrepancies = query.order_by(
        BidItemDiscrepancy.severity.desc(),
        BidItemDiscrepancy.created_at.desc()
    ).offset(skip).limit(limit).all()

    return DiscrepancyListResponse(
        total=total,
        by_severity=dict(by_severity),
        by_type=dict(by_type),
        by_status=dict(by_status),
        discrepancies=discrepancies
    )


@router.get("/projects/{project_id}/discrepancies/{discrepancy_id}", response_model=DiscrepancyResponse)
async def get_discrepancy(
    project_id: UUID,
    discrepancy_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get discrepancy details"""
    discrepancy = db.query(BidItemDiscrepancy).join(Project).filter(
        BidItemDiscrepancy.id == discrepancy_id,
        BidItemDiscrepancy.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not discrepancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discrepancy not found"
        )

    return discrepancy


@router.patch("/projects/{project_id}/discrepancies/{discrepancy_id}/status", response_model=DiscrepancyResponse)
async def update_discrepancy_status(
    project_id: UUID,
    discrepancy_id: UUID,
    resolve_data: DiscrepancyResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resolve or ignore a discrepancy"""
    discrepancy = db.query(BidItemDiscrepancy).join(Project).filter(
        BidItemDiscrepancy.id == discrepancy_id,
        BidItemDiscrepancy.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not discrepancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discrepancy not found"
        )

    # Validate status
    if resolve_data.status not in ["resolved", "ignored"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be 'resolved' or 'ignored'"
        )

    discrepancy.status = resolve_data.status
    if resolve_data.resolution_notes:
        discrepancy.resolution_notes = resolve_data.resolution_notes

    db.commit()
    db.refresh(discrepancy)
    return discrepancy


@router.delete("/projects/{project_id}/discrepancies/{discrepancy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discrepancy(
    project_id: UUID,
    discrepancy_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a discrepancy"""
    discrepancy = db.query(BidItemDiscrepancy).join(Project).filter(
        BidItemDiscrepancy.id == discrepancy_id,
        BidItemDiscrepancy.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not discrepancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discrepancy not found"
        )

    db.delete(discrepancy)
    db.commit()
    return None


@router.get("/projects/{project_id}/discrepancies/summary/stats", response_model=DiscrepancySummary)
async def get_discrepancy_summary(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get discrepancy summary statistics"""
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

    # Use DiscrepancyDetector service for summary
    summary = DiscrepancyDetector.get_discrepancy_summary(project_id, db)

    # Get status counts
    open_count = db.query(func.count(BidItemDiscrepancy.id)).filter(
        BidItemDiscrepancy.project_id == project_id,
        BidItemDiscrepancy.status == "open"
    ).scalar()

    resolved_count = db.query(func.count(BidItemDiscrepancy.id)).filter(
        BidItemDiscrepancy.project_id == project_id,
        BidItemDiscrepancy.status == "resolved"
    ).scalar()

    ignored_count = db.query(func.count(BidItemDiscrepancy.id)).filter(
        BidItemDiscrepancy.project_id == project_id,
        BidItemDiscrepancy.status == "ignored"
    ).scalar()

    return DiscrepancySummary(
        total=summary["total"],
        by_severity=summary["by_severity"],
        by_type=summary["by_type"],
        open_count=open_count,
        resolved_count=resolved_count,
        ignored_count=ignored_count
    )


@router.post("/projects/{project_id}/discrepancies/clear-all", status_code=status.HTTP_200_OK)
async def clear_all_discrepancies(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clear all discrepancies for a project (before re-running detection)"""
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

    deleted_count = db.query(BidItemDiscrepancy).filter(
        BidItemDiscrepancy.project_id == project_id
    ).delete()

    db.commit()

    return {
        "message": f"Cleared {deleted_count} discrepancies",
        "deleted_count": deleted_count
    }
