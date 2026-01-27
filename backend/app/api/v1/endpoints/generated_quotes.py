from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import date, timedelta
import random
import string
import os

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.company import Company
from app.models.estimation import GeneratedQuote, GeneratedQuoteLineItem, TakeoffItem
from app.models.material import Material
from app.models.project import Project
from app.services.quote_pdf_generator import QuotePDFGenerator
from app.api.v1.schemas.generated_quote import (
    GeneratedQuoteCreate,
    GeneratedQuoteUpdate,
    GeneratedQuoteResponse,
    GeneratedQuoteListResponse,
    GeneratedQuoteLineItemCreate,
    GeneratedQuoteLineItemResponse,
    GeneratedQuoteLineItemUpdate,
    GenerateQuoteFromTakeoffsRequest,
)

router = APIRouter()


def generate_quote_number() -> str:
    """Generate a unique quote number"""
    timestamp = date.today().strftime("%y%m%d")
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"{timestamp}{random_suffix}"


def calculate_quote_totals(db: Session, quote_id: UUID) -> dict:
    """Calculate subtotal, tax, and total for a quote"""
    line_items = db.query(GeneratedQuoteLineItem).filter(
        GeneratedQuoteLineItem.generated_quote_id == quote_id
    ).all()
    
    subtotal = sum(item.total_price for item in line_items)
    quote = db.query(GeneratedQuote).filter(GeneratedQuote.id == quote_id).first()
    tax_rate = quote.tax_rate if quote else Decimal("0")
    tax_amount = subtotal * tax_rate
    total = subtotal + tax_amount
    
    return {
        "subtotal": subtotal,
        "tax_amount": tax_amount,
        "total": total
    }


@router.post("/projects/{project_id}/generated-quotes", response_model=GeneratedQuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_generated_quote(
    project_id: UUID,
    quote_data: GeneratedQuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new generated quote for a customer"""
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

    # Generate quote number if not provided
    quote_number = quote_data.quote_number or generate_quote_number()
    
    # Set default expiration date if not provided
    expiration_date = quote_data.expiration_date or (date.today() + timedelta(days=7))

    quote = GeneratedQuote(
        project_id=project_id,
        created_by=current_user.id,
        quote_number=quote_number,
        quote_date=quote_data.quote_date or date.today(),
        expiration_date=expiration_date,
        customer_name=quote_data.customer_name,
        customer_company=quote_data.customer_company,
        customer_email=quote_data.customer_email,
        customer_phone=quote_data.customer_phone,
        delivery_address=quote_data.delivery_address,
        job_name=quote_data.job_name or project.name,
        job_reference=quote_data.job_reference or project.job_number,
        tax_rate=quote_data.tax_rate or Decimal("0"),
        special_instructions=quote_data.special_instructions,
        notes=quote_data.notes,
        status="draft"
    )
    
    db.add(quote)
    db.commit()
    db.refresh(quote)

    # Add line items if provided
    if quote_data.line_items:
        for item_data in quote_data.line_items:
            total_price = item_data.total_price or (item_data.quantity * item_data.unit_price)
            line_item = GeneratedQuoteLineItem(
                generated_quote_id=quote.id,
                takeoff_item_id=item_data.takeoff_item_id,
                material_id=item_data.material_id,
                line_number=item_data.line_number,
                category=item_data.category,
                quantity=item_data.quantity,
                unit=item_data.unit,
                product_code=item_data.product_code,
                description=item_data.description,
                unit_price=item_data.unit_price,
                total_price=total_price,
                notes=item_data.notes
            )
            db.add(line_item)
        
        db.commit()
        
        # Recalculate totals
        totals = calculate_quote_totals(db, quote.id)
        quote.subtotal = totals["subtotal"]
        quote.tax_amount = totals["tax_amount"]
        quote.total = totals["total"]
        db.commit()
        db.refresh(quote)

    # Load line items for response
    line_items = db.query(GeneratedQuoteLineItem).filter(
        GeneratedQuoteLineItem.generated_quote_id == quote.id
    ).order_by(GeneratedQuoteLineItem.line_number).all()
    
    return GeneratedQuoteResponse(
        **{k: v for k, v in quote.__dict__.items() if not k.startswith('_')},
        line_items=[GeneratedQuoteLineItemResponse(**{k: v for k, v in li.__dict__.items() if not k.startswith('_')}) for li in line_items]
    )


@router.post("/projects/{project_id}/generated-quotes/from-takeoffs", response_model=GeneratedQuoteResponse, status_code=status.HTTP_201_CREATED)
async def generate_quote_from_takeoffs(
    project_id: UUID,
    request: GenerateQuoteFromTakeoffsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate a quote from takeoff items.
    
    This takes takeoff items extracted from plans and creates a customer-facing quote
    by matching items to the material catalog for pricing.
    """
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

    # Get takeoff items
    query = db.query(TakeoffItem).filter(TakeoffItem.project_id == project_id)
    if request.takeoff_item_ids:
        query = query.filter(TakeoffItem.id.in_(request.takeoff_item_ids))
    
    takeoff_items = query.all()
    
    if not takeoff_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No takeoff items found to generate quote from"
        )

    # Create the quote
    quote_number = generate_quote_number()
    expiration_date = date.today() + timedelta(days=request.expiration_days or 7)
    
    quote = GeneratedQuote(
        project_id=project_id,
        created_by=current_user.id,
        quote_number=quote_number,
        quote_date=date.today(),
        expiration_date=expiration_date,
        customer_name=request.customer_name,
        customer_company=request.customer_company,
        customer_email=request.customer_email,
        customer_phone=request.customer_phone,
        delivery_address=request.delivery_address,
        job_name=request.job_name or project.name,
        job_reference=request.job_reference or project.job_number,
        tax_rate=request.tax_rate or Decimal("0"),
        special_instructions=request.special_instructions,
        notes=request.notes,
        status="draft"
    )
    
    db.add(quote)
    db.commit()
    db.refresh(quote)

    # Create line items from takeoff items
    # Try to match each takeoff item to a material in the catalog for pricing
    line_number = 1
    current_category = None
    
    for takeoff in takeoff_items:
        # Try to find matching material by description
        material = db.query(Material).filter(
            Material.company_id == current_user.company_id,
            Material.is_active == True
        ).filter(
            Material.description.ilike(f"%{takeoff.label}%")
        ).first()
        
        # Use material pricing if found, otherwise use placeholder
        if material:
            unit_price = material.unit_price
            product_code = material.product_code
            unit = material.unit
            category = material.category
        else:
            unit_price = Decimal("0")  # Needs manual pricing
            product_code = None
            unit = takeoff.unit
            category = None
        
        total_price = takeoff.qty * unit_price
        
        line_item = GeneratedQuoteLineItem(
            generated_quote_id=quote.id,
            takeoff_item_id=takeoff.id,
            material_id=material.id if material else None,
            line_number=line_number,
            category=category,
            quantity=takeoff.qty,
            unit=unit,
            product_code=product_code,
            description=takeoff.label,
            unit_price=unit_price,
            total_price=total_price,
            notes=takeoff.notes
        )
        db.add(line_item)
        line_number += 1
    
    db.commit()
    
    # Recalculate totals
    totals = calculate_quote_totals(db, quote.id)
    quote.subtotal = totals["subtotal"]
    quote.tax_amount = totals["tax_amount"]
    quote.total = totals["total"]
    db.commit()
    db.refresh(quote)

    # Load line items for response
    line_items = db.query(GeneratedQuoteLineItem).filter(
        GeneratedQuoteLineItem.generated_quote_id == quote.id
    ).order_by(GeneratedQuoteLineItem.line_number).all()
    
    return GeneratedQuoteResponse(
        **{k: v for k, v in quote.__dict__.items() if not k.startswith('_')},
        line_items=[GeneratedQuoteLineItemResponse(**{k: v for k, v in li.__dict__.items() if not k.startswith('_')}) for li in line_items]
    )


@router.get("/projects/{project_id}/generated-quotes", response_model=GeneratedQuoteListResponse)
async def list_generated_quotes(
    project_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all generated quotes for a project"""
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

    query = db.query(GeneratedQuote).filter(GeneratedQuote.project_id == project_id)

    if status_filter:
        query = query.filter(GeneratedQuote.status == status_filter)

    total = query.count()
    quotes = query.order_by(GeneratedQuote.created_at.desc()).offset(skip).limit(limit).all()

    # Load line items for each quote
    result_quotes = []
    for quote in quotes:
        line_items = db.query(GeneratedQuoteLineItem).filter(
            GeneratedQuoteLineItem.generated_quote_id == quote.id
        ).order_by(GeneratedQuoteLineItem.line_number).all()
        
        result_quotes.append(GeneratedQuoteResponse(
            **{k: v for k, v in quote.__dict__.items() if not k.startswith('_')},
            line_items=[GeneratedQuoteLineItemResponse(**{k: v for k, v in li.__dict__.items() if not k.startswith('_')}) for li in line_items]
        ))

    return GeneratedQuoteListResponse(total=total, quotes=result_quotes)


@router.get("/projects/{project_id}/generated-quotes/{quote_id}", response_model=GeneratedQuoteResponse)
async def get_generated_quote(
    project_id: UUID,
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific generated quote with line items"""
    quote = db.query(GeneratedQuote).join(Project).filter(
        GeneratedQuote.id == quote_id,
        GeneratedQuote.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    line_items = db.query(GeneratedQuoteLineItem).filter(
        GeneratedQuoteLineItem.generated_quote_id == quote.id
    ).order_by(GeneratedQuoteLineItem.line_number).all()

    return GeneratedQuoteResponse(
        **{k: v for k, v in quote.__dict__.items() if not k.startswith('_')},
        line_items=[GeneratedQuoteLineItemResponse(**{k: v for k, v in li.__dict__.items() if not k.startswith('_')}) for li in line_items]
    )


@router.put("/projects/{project_id}/generated-quotes/{quote_id}", response_model=GeneratedQuoteResponse)
async def update_generated_quote(
    project_id: UUID,
    quote_id: UUID,
    quote_data: GeneratedQuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a generated quote"""
    quote = db.query(GeneratedQuote).join(Project).filter(
        GeneratedQuote.id == quote_id,
        GeneratedQuote.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Update fields
    update_data = quote_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(quote, field, value)

    # Recalculate totals if tax rate changed
    if 'tax_rate' in update_data:
        totals = calculate_quote_totals(db, quote.id)
        quote.subtotal = totals["subtotal"]
        quote.tax_amount = totals["tax_amount"]
        quote.total = totals["total"]

    db.commit()
    db.refresh(quote)

    line_items = db.query(GeneratedQuoteLineItem).filter(
        GeneratedQuoteLineItem.generated_quote_id == quote.id
    ).order_by(GeneratedQuoteLineItem.line_number).all()

    return GeneratedQuoteResponse(
        **{k: v for k, v in quote.__dict__.items() if not k.startswith('_')},
        line_items=[GeneratedQuoteLineItemResponse(**{k: v for k, v in li.__dict__.items() if not k.startswith('_')}) for li in line_items]
    )


@router.delete("/projects/{project_id}/generated-quotes/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_generated_quote(
    project_id: UUID,
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a generated quote"""
    quote = db.query(GeneratedQuote).join(Project).filter(
        GeneratedQuote.id == quote_id,
        GeneratedQuote.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    # Line items will be cascade deleted
    db.delete(quote)
    db.commit()
    return None


@router.post("/projects/{project_id}/generated-quotes/{quote_id}/line-items", response_model=GeneratedQuoteLineItemResponse, status_code=status.HTTP_201_CREATED)
async def add_line_item(
    project_id: UUID,
    quote_id: UUID,
    item_data: GeneratedQuoteLineItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a line item to a generated quote"""
    quote = db.query(GeneratedQuote).join(Project).filter(
        GeneratedQuote.id == quote_id,
        GeneratedQuote.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    total_price = item_data.total_price or (item_data.quantity * item_data.unit_price)
    
    line_item = GeneratedQuoteLineItem(
        generated_quote_id=quote.id,
        takeoff_item_id=item_data.takeoff_item_id,
        material_id=item_data.material_id,
        line_number=item_data.line_number,
        category=item_data.category,
        quantity=item_data.quantity,
        unit=item_data.unit,
        product_code=item_data.product_code,
        description=item_data.description,
        unit_price=item_data.unit_price,
        total_price=total_price,
        notes=item_data.notes
    )
    
    db.add(line_item)
    db.commit()
    
    # Recalculate quote totals
    totals = calculate_quote_totals(db, quote.id)
    quote.subtotal = totals["subtotal"]
    quote.tax_amount = totals["tax_amount"]
    quote.total = totals["total"]
    db.commit()
    
    db.refresh(line_item)
    return line_item


@router.put("/projects/{project_id}/generated-quotes/{quote_id}/line-items/{item_id}", response_model=GeneratedQuoteLineItemResponse)
async def update_line_item(
    project_id: UUID,
    quote_id: UUID,
    item_id: UUID,
    item_data: GeneratedQuoteLineItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a line item"""
    quote = db.query(GeneratedQuote).join(Project).filter(
        GeneratedQuote.id == quote_id,
        GeneratedQuote.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    line_item = db.query(GeneratedQuoteLineItem).filter(
        GeneratedQuoteLineItem.id == item_id,
        GeneratedQuoteLineItem.generated_quote_id == quote_id
    ).first()

    if not line_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line item not found"
        )

    # Update fields
    update_data = item_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(line_item, field, value)

    # Recalculate total_price if quantity or unit_price changed
    if 'quantity' in update_data or 'unit_price' in update_data:
        line_item.total_price = line_item.quantity * line_item.unit_price

    db.commit()
    
    # Recalculate quote totals
    totals = calculate_quote_totals(db, quote.id)
    quote.subtotal = totals["subtotal"]
    quote.tax_amount = totals["tax_amount"]
    quote.total = totals["total"]
    db.commit()
    
    db.refresh(line_item)
    return line_item


@router.delete("/projects/{project_id}/generated-quotes/{quote_id}/line-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_line_item(
    project_id: UUID,
    quote_id: UUID,
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a line item"""
    quote = db.query(GeneratedQuote).join(Project).filter(
        GeneratedQuote.id == quote_id,
        GeneratedQuote.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    line_item = db.query(GeneratedQuoteLineItem).filter(
        GeneratedQuoteLineItem.id == item_id,
        GeneratedQuoteLineItem.generated_quote_id == quote_id
    ).first()

    if not line_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Line item not found"
        )

    db.delete(line_item)
    db.commit()
    
    # Recalculate quote totals
    totals = calculate_quote_totals(db, quote.id)
    quote.subtotal = totals["subtotal"]
    quote.tax_amount = totals["tax_amount"]
    quote.total = totals["total"]
    db.commit()
    
    return None


@router.post("/projects/{project_id}/generate-quote-pdf")
async def generate_quote_pdf_from_takeoffs(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a professional PDF quote from matched takeoff items.
    
    This creates a PDF in the style of Stine Quote 684107 with:
    - Company branding (Dozier Tech Group)
    - Line items organized by category
    - Category subtotals
    - Grand total with tax
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
    
    # Get matched takeoff items
    takeoff_items = db.query(TakeoffItem).filter(
        TakeoffItem.project_id == project_id,
        TakeoffItem.matched_material_id.isnot(None)
    ).all()
    
    if not takeoff_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No matched takeoff items found. Please match items to catalog first."
        )
    
    # Get company info
    company = db.query(Company).filter(Company.id == current_user.company_id).first()
    
    # Build line items for PDF
    line_items = []
    subtotal = Decimal("0")
    
    for item in takeoff_items:
        # Get material info
        material = db.query(Material).filter(Material.id == item.matched_material_id).first()
        
        qty = float(item.qty) if item.qty else 0
        unit_price = float(item.unit_price) if item.unit_price else 0
        line_total = float(item.total_price) if item.total_price else 0
        
        line_items.append({
            "quantity": qty,
            "product_code": material.product_code if material else "",
            "description": item.label,
            "unit_price": unit_price,
            "unit": item.unit or "ea",
            "line_total": line_total,
            "category": item.category or "Miscellaneous"
        })
        
        subtotal += Decimal(str(line_total))
    
    # Calculate totals
    tax_rate = Decimal("0.0945")  # Louisiana sales tax
    tax_amount = subtotal * tax_rate
    grand_total = subtotal + tax_amount
    
    # Company info for PDF
    company_info = {
        "name": "Dozier Tech Group",
        "address": company.address if company else "123 Main Street",
        "city": company.city if company else "Lafayette",
        "state": company.state if company else "LA",
        "zip": company.zip if company else "70508",
        "phone": company.phone if company else "(337) 555-0100",
        "email": company.email if company else "info@doziertechgroup.com"
    }
    
    # Project info
    project_info = {
        "name": project.name,
        "location": project.location or "",
        "customer_name": company.name if company else "Customer",
        "contact_name": f"{current_user.first_name} {current_user.last_name}" if current_user.first_name else current_user.email,
        "job_number": project.job_number
    }
    
    # Quote data
    quote_number = f"Q{generate_quote_number()}"
    quote_data = {
        "quote_number": quote_number,
        "quote_date": date.today().strftime("%m/%d/%Y"),
        "expiration_date": (date.today() + timedelta(days=7)).strftime("%m/%d/%Y"),
        "delivery_date": "TBD"
    }
    
    # Estimate data for totals
    estimate_data = {
        "materials_cost": float(subtotal),
        "labor_cost": 0,
        "equipment_cost": 0,
        "subcontractor_cost": 0,
        "subtotal": float(subtotal),
        "overhead": 0,
        "overhead_percentage": 0,
        "profit": 0,
        "profit_percentage": 0,
        "total_cost": float(subtotal),
        "tax_rate": float(tax_rate) * 100,
        "tax_amount": float(tax_amount),
        "grand_total": float(grand_total)
    }
    
    # Generate PDF
    generator = QuotePDFGenerator(output_dir="uploads/quotes")
    output_filename = f"{quote_number}_{project.job_number}.pdf"
    
    pdf_path = generator.generate_quote(
        quote_data=quote_data,
        estimate_data=estimate_data,
        line_items=line_items,
        company_info=company_info,
        project_info=project_info,
        output_filename=output_filename
    )
    
    # Return the PDF file
    return FileResponse(
        path=pdf_path,
        filename=output_filename,
        media_type="application/pdf"
    )
