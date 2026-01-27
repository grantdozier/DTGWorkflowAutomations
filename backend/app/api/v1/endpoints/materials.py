from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.material import Material
from pydantic import BaseModel, UUID4

router = APIRouter()


# Schemas
class MaterialBase(BaseModel):
    product_code: str
    description: str
    category: str
    unit_price: Decimal
    unit: str
    manufacturer: Optional[str] = None
    specifications: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    lead_time_days: Optional[Decimal] = None
    minimum_order: Optional[Decimal] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    product_code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    unit_price: Optional[Decimal] = None
    unit: Optional[str] = None
    manufacturer: Optional[str] = None
    specifications: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None
    lead_time_days: Optional[Decimal] = None
    minimum_order: Optional[Decimal] = None


class MaterialResponse(MaterialBase):
    id: UUID4
    company_id: UUID4

    class Config:
        from_attributes = True


@router.get("/", response_model=List[MaterialResponse])
def list_materials(
    category: Optional[str] = None,
    search: Optional[str] = None,
    is_active: bool = True,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all materials for the current company

    Filters:
    - category: Filter by category (Foundation, Walls, Roofing, etc.)
    - search: Search in product_code or description
    - is_active: Show only active materials (default: true)
    """
    query = db.query(Material).filter(
        Material.company_id == current_user.company_id
    )

    if category:
        query = query.filter(Material.category == category)

    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Material.product_code.ilike(search_term)) |
            (Material.description.ilike(search_term))
        )

    if is_active is not None:
        query = query.filter(Material.is_active == is_active)

    materials = query.offset(skip).limit(limit).all()
    return materials


@router.get("/categories")
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all material categories for the company"""
    categories = db.query(Material.category).filter(
        Material.company_id == current_user.company_id
    ).distinct().all()

    return {
        "categories": [cat[0] for cat in categories]
    }


@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific material by ID"""
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.company_id == current_user.company_id
    ).first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    return material


@router.post("/", response_model=MaterialResponse, status_code=status.HTTP_201_CREATED)
def create_material(
    material_data: MaterialCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new material"""
    # Check if product code already exists
    existing = db.query(Material).filter(
        Material.company_id == current_user.company_id,
        Material.product_code == material_data.product_code
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Material with product code '{material_data.product_code}' already exists"
        )

    material = Material(
        company_id=current_user.company_id,
        **material_data.dict()
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    return material


@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(
    material_id: str,
    material_data: MaterialUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a material"""
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.company_id == current_user.company_id
    ).first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    # Update only provided fields
    update_data = material_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(material, field, value)

    db.commit()
    db.refresh(material)

    return material


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_material(
    material_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a material (soft delete - marks as inactive)"""
    material = db.query(Material).filter(
        Material.id == material_id,
        Material.company_id == current_user.company_id
    ).first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )

    # Soft delete
    material.is_active = False
    db.commit()

    return None


@router.get("/by-code/{product_code}", response_model=MaterialResponse)
def get_material_by_code(
    product_code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a material by product code"""
    material = db.query(Material).filter(
        Material.product_code == product_code,
        Material.company_id == current_user.company_id,
        Material.is_active == True
    ).first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Material with code '{product_code}' not found"
        )

    return material
