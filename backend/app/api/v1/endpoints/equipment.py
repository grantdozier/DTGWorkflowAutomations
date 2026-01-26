from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.equipment import InternalEquipment
from app.api.v1.schemas.equipment import (
    InternalEquipmentCreate,
    InternalEquipmentUpdate,
    InternalEquipmentResponse,
    InternalEquipmentAvailabilityUpdate
)

router = APIRouter()


@router.post("", response_model=InternalEquipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    equipment_data: InternalEquipmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new internal equipment"""
    equipment = InternalEquipment(
        **equipment_data.dict(),
        company_id=current_user.company_id
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    return equipment


@router.get("", response_model=List[InternalEquipmentResponse])
async def list_equipment(
    equipment_type: Optional[str] = Query(None),
    is_available: Optional[bool] = Query(None),
    condition: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all company equipment with optional filters"""
    query = db.query(InternalEquipment).filter(
        InternalEquipment.company_id == current_user.company_id
    )

    if equipment_type:
        query = query.filter(InternalEquipment.equipment_type == equipment_type)
    if is_available is not None:
        query = query.filter(InternalEquipment.is_available == is_available)
    if condition:
        query = query.filter(InternalEquipment.condition == condition)

    equipment = query.order_by(InternalEquipment.name).offset(skip).limit(limit).all()
    return equipment


@router.get("/{equipment_id}", response_model=InternalEquipmentResponse)
async def get_equipment(
    equipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get equipment details"""
    equipment = db.query(InternalEquipment).filter(
        InternalEquipment.id == equipment_id,
        InternalEquipment.company_id == current_user.company_id
    ).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )

    return equipment


@router.put("/{equipment_id}", response_model=InternalEquipmentResponse)
async def update_equipment(
    equipment_id: UUID,
    equipment_data: InternalEquipmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update equipment"""
    equipment = db.query(InternalEquipment).filter(
        InternalEquipment.id == equipment_id,
        InternalEquipment.company_id == current_user.company_id
    ).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )

    # Update fields
    update_data = equipment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(equipment, field, value)

    db.commit()
    db.refresh(equipment)
    return equipment


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    equipment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete equipment"""
    equipment = db.query(InternalEquipment).filter(
        InternalEquipment.id == equipment_id,
        InternalEquipment.company_id == current_user.company_id
    ).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )

    db.delete(equipment)
    db.commit()
    return None


@router.patch("/{equipment_id}/availability", response_model=InternalEquipmentResponse)
async def update_equipment_availability(
    equipment_id: UUID,
    availability_data: InternalEquipmentAvailabilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update equipment availability status"""
    equipment = db.query(InternalEquipment).filter(
        InternalEquipment.id == equipment_id,
        InternalEquipment.company_id == current_user.company_id
    ).first()

    if not equipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Equipment not found"
        )

    equipment.is_available = availability_data.is_available
    db.commit()
    db.refresh(equipment)
    return equipment
