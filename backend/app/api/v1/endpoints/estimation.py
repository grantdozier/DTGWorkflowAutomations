from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.estimation import Estimate, TakeoffItem
from app.services.estimation_engine import estimation_engine
from app.api.v1.schemas.estimation import (
    GenerateEstimateRequest,
    EstimateResponse,
    EstimateDetailResponse,
    EstimateListResponse,
    CostBreakdown,
    EstimateItemDetail
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/projects/{project_id}/estimate", response_model=EstimateDetailResponse, status_code=status.HTTP_201_CREATED)
async def generate_project_estimate(
    project_id: str,
    request: GenerateEstimateRequest = GenerateEstimateRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a cost estimate for a project

    This endpoint:
    1. Gets all takeoff items for the project
    2. Applies company labor rates
    3. Calculates equipment costs
    4. Adds overhead and profit margins
    5. Generates a complete estimate

    **Prerequisites:**
    - Project must have takeoff items (parse a plan first)
    - Company should have rates configured (optional but recommended)

    **Parameters:**
    - **overhead_percentage**: Override overhead percentage (optional)
    - **profit_percentage**: Override profit percentage (optional)
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

    # Generate estimate
    result = await estimation_engine.generate_estimate(
        project_id=project_id,
        user_id=str(current_user.id),
        db=db,
        overhead_percentage=request.overhead_percentage,
        profit_percentage=request.profit_percentage
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to generate estimate")
        )

    # Format response
    estimate = result["estimate"]

    return {
        "estimate": {
            "id": str(estimate.id),
            "project_id": str(estimate.project_id),
            "created_by": str(estimate.created_by),
            "created_at": estimate.created_at,
            "materials_cost": float(estimate.materials_cost),
            "labor_cost": float(estimate.labor_cost),
            "equipment_cost": float(estimate.equipment_cost),
            "subcontractor_cost": float(estimate.subcontractor_cost),
            "overhead": float(estimate.overhead),
            "profit": float(estimate.profit),
            "total_cost": float(estimate.total_cost),
            "confidence_score": float(estimate.confidence_score) if estimate.confidence_score else None
        },
        "breakdown": result["breakdown"],
        "items": result["items"],
        "summary": result["summary"]
    }


@router.get("/projects/{project_id}/estimates", response_model=EstimateListResponse)
async def list_project_estimates(
    project_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all estimates for a project
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

    # Get estimates
    query = db.query(Estimate).filter(Estimate.project_id == project_id)
    total = query.count()
    estimates = query.order_by(Estimate.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "total": total,
        "estimates": [
            {
                "id": str(est.id),
                "project_id": str(est.project_id),
                "created_by": str(est.created_by),
                "created_at": est.created_at,
                "materials_cost": float(est.materials_cost),
                "labor_cost": float(est.labor_cost),
                "equipment_cost": float(est.equipment_cost),
                "subcontractor_cost": float(est.subcontractor_cost),
                "overhead": float(est.overhead),
                "profit": float(est.profit),
                "total_cost": float(est.total_cost),
                "confidence_score": float(est.confidence_score) if est.confidence_score else None
            }
            for est in estimates
        ]
    }


@router.get("/projects/{project_id}/estimates/{estimate_id}", response_model=EstimateDetailResponse)
async def get_estimate_detail(
    project_id: str,
    estimate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed estimate information
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

    # Get estimate
    estimate = db.query(Estimate).filter(
        Estimate.id == estimate_id,
        Estimate.project_id == project_id
    ).first()

    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )

    # Get takeoff items for this project
    takeoff_items = db.query(TakeoffItem).filter(
        TakeoffItem.project_id == project_id
    ).all()

    # Build item details
    items = [
        {
            "item_id": str(item.id),
            "description": item.label,
            "quantity": float(item.qty),
            "unit": item.unit,
            "unit_cost": 0,  # Would calculate from estimate
            "total_cost": 0,
            "labor_hours": None,
            "category": "material"
        }
        for item in takeoff_items
    ]

    # Calculate breakdown
    direct_costs = (
        float(estimate.materials_cost) +
        float(estimate.labor_cost) +
        float(estimate.equipment_cost) +
        float(estimate.subcontractor_cost)
    )

    breakdown = {
        "materials": float(estimate.materials_cost),
        "labor": float(estimate.labor_cost),
        "equipment": float(estimate.equipment_cost),
        "subcontractors": float(estimate.subcontractor_cost),
        "subtotal": direct_costs,
        "overhead": float(estimate.overhead),
        "profit": float(estimate.profit),
        "total": float(estimate.total_cost)
    }

    return {
        "estimate": {
            "id": str(estimate.id),
            "project_id": str(estimate.project_id),
            "created_by": str(estimate.created_by),
            "created_at": estimate.created_at,
            "materials_cost": float(estimate.materials_cost),
            "labor_cost": float(estimate.labor_cost),
            "equipment_cost": float(estimate.equipment_cost),
            "subcontractor_cost": float(estimate.subcontractor_cost),
            "overhead": float(estimate.overhead),
            "profit": float(estimate.profit),
            "total_cost": float(estimate.total_cost),
            "confidence_score": float(estimate.confidence_score) if estimate.confidence_score else None
        },
        "breakdown": breakdown,
        "items": items,
        "summary": {
            "total_items": len(takeoff_items),
            "confidence_score": float(estimate.confidence_score) if estimate.confidence_score else 0
        }
    }


@router.delete("/projects/{project_id}/estimates/{estimate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_estimate(
    project_id: str,
    estimate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an estimate
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

    # Get estimate
    estimate = db.query(Estimate).filter(
        Estimate.id == estimate_id,
        Estimate.project_id == project_id
    ).first()

    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )

    db.delete(estimate)
    db.commit()

    return None
