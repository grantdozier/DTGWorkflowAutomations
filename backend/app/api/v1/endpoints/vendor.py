from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import csv
import io

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.vendor import Vendor
from app.api.v1.schemas.vendor import (
    VendorCreate,
    VendorUpdate,
    VendorResponse,
    VendorBulkImportResponse
)

router = APIRouter()


@router.post("", response_model=VendorResponse, status_code=status.HTTP_201_CREATED)
async def create_vendor(
    vendor_data: VendorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new vendor"""
    vendor = Vendor(
        **vendor_data.dict(),
        company_id=current_user.company_id
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    return vendor


@router.get("", response_model=List[VendorResponse])
async def list_vendors(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_preferred: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all company vendors with optional filters"""
    query = db.query(Vendor).filter(
        Vendor.company_id == current_user.company_id
    )

    if category:
        query = query.filter(Vendor.category == category)
    if is_active is not None:
        query = query.filter(Vendor.is_active == is_active)
    if is_preferred is not None:
        query = query.filter(Vendor.is_preferred == is_preferred)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Vendor.name.ilike(search_term)) |
            (Vendor.contact_name.ilike(search_term)) |
            (Vendor.email.ilike(search_term))
        )

    vendors = query.order_by(Vendor.name).offset(skip).limit(limit).all()
    return vendors


@router.get("/{vendor_id}", response_model=VendorResponse)
async def get_vendor(
    vendor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get vendor details"""
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.company_id == current_user.company_id
    ).first()

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )

    return vendor


@router.put("/{vendor_id}", response_model=VendorResponse)
async def update_vendor(
    vendor_id: UUID,
    vendor_data: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update vendor"""
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.company_id == current_user.company_id
    ).first()

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )

    # Update fields
    update_data = vendor_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)

    db.commit()
    db.refresh(vendor)
    return vendor


@router.delete("/{vendor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vendor(
    vendor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft delete vendor (mark as inactive)"""
    vendor = db.query(Vendor).filter(
        Vendor.id == vendor_id,
        Vendor.company_id == current_user.company_id
    ).first()

    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )

    vendor.is_active = False
    db.commit()
    return None


@router.post("/bulk-import", response_model=VendorBulkImportResponse)
async def bulk_import_vendors(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Import vendors from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    # Read CSV content
    content = await file.read()
    csv_content = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(csv_content))

    success_count = 0
    error_count = 0
    errors = []

    for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
        try:
            # Validate required fields
            if not row.get('name') or not row.get('category'):
                errors.append({
                    "row": row_num,
                    "error": "Missing required fields: name and category"
                })
                error_count += 1
                continue

            # Validate category
            valid_categories = ['rental', 'subcontractor', 'outside_service', 'material_supplier']
            if row.get('category') not in valid_categories:
                errors.append({
                    "row": row_num,
                    "error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"
                })
                error_count += 1
                continue

            # Create vendor
            vendor = Vendor(
                company_id=current_user.company_id,
                name=row['name'],
                category=row['category'],
                contact_name=row.get('contact_name'),
                email=row.get('email'),
                phone=row.get('phone'),
                address_line1=row.get('address_line1'),
                city=row.get('city'),
                state=row.get('state'),
                zip_code=row.get('zip_code'),
                license_number=row.get('license_number'),
                rating=float(row['rating']) if row.get('rating') else None,
                notes=row.get('notes')
            )
            db.add(vendor)
            success_count += 1

        except Exception as e:
            errors.append({
                "row": row_num,
                "error": str(e)
            })
            error_count += 1

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save vendors: {str(e)}"
        )

    return VendorBulkImportResponse(
        success_count=success_count,
        error_count=error_count,
        errors=errors
    )
