from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from decimal import Decimal
from pydantic import BaseModel, UUID4
import logging

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.estimation import TakeoffItem, Estimate
from app.models.company import Company, CompanyRates
from app.models.material import Material
from app.services.material_matcher import match_takeoff_to_materials
from app.services.quote_pdf_generator import generate_quote_pdf

router = APIRouter()
logger = logging.getLogger(__name__)


# Schemas
class EstimateGenerationRequest(BaseModel):
    project_id: UUID4
    match_threshold: int = 70
    auto_accept_high_confidence: bool = True  # Auto-accept matches >= 0.8
    apply_overhead: bool = True
    apply_profit: bool = True


class LineItemResponse(BaseModel):
    takeoff_item_id: str
    label: str
    quantity: float
    unit: str
    matched_material_code: Optional[str]
    matched_material_desc: Optional[str]
    unit_price: float
    line_total: float
    match_confidence: Optional[float]


class EstimateBreakdown(BaseModel):
    line_items: List[LineItemResponse]
    materials_cost: float
    labor_cost: float
    equipment_cost: float
    subcontractor_cost: float
    subtotal: float
    overhead: float
    overhead_percentage: float
    profit: float
    profit_percentage: float
    total_cost: float
    tax_rate: float
    tax_amount: float
    grand_total: float


class EstimateResponse(BaseModel):
    success: bool
    estimate_id: Optional[str]
    project_id: str
    breakdown: Optional[EstimateBreakdown]
    summary: Dict
    errors: List[str]


@router.post("/generate", response_model=EstimateResponse)
async def generate_estimate(
    request: EstimateGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate estimate for a project

    Process:
    1. Get all takeoff items for project
    2. Match items to material catalog
    3. Calculate material costs
    4. Apply overhead and profit margins
    5. Save estimate to database
    6. Return complete breakdown

    This is the core estimation engine!
    """
    errors = []
    project_id_str = str(request.project_id)

    try:
        # Verify project exists and user has access
        project = db.query(Project).filter(
            Project.id == project_id_str,
            Project.company_id == current_user.company_id
        ).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Get all takeoff items
        takeoff_items = db.query(TakeoffItem).filter(
            TakeoffItem.project_id == project_id_str
        ).all()

        if not takeoff_items:
            return EstimateResponse(
                success=False,
                estimate_id=None,
                project_id=project_id_str,
                breakdown=None,
                summary={"message": "No takeoff items found for project"},
                errors=["No takeoff items to estimate"]
            )

        # Match takeoff items to materials
        logger.info(f"Matching {len(takeoff_items)} takeoff items to materials...")
        matches_dict = match_takeoff_to_materials(
            db=db,
            company_id=str(current_user.company_id),
            takeoff_items=takeoff_items,
            threshold=request.match_threshold
        )

        # Calculate costs
        line_items = []
        total_materials_cost = Decimal("0")
        matched_count = 0
        unmatched_items = []

        for item in takeoff_items:
            item_id = str(item.id)
            matches = matches_dict.get(item_id, [])

            # Get best match
            best_match = None
            if matches:
                if request.auto_accept_high_confidence and matches[0]["confidence"] >= 0.8:
                    best_match = matches[0]
                elif len(matches) == 1:
                    # Only one match, use it
                    best_match = matches[0]
                else:
                    # Multiple matches, use highest confidence if > threshold
                    if matches[0]["confidence"] >= 0.7:
                        best_match = matches[0]

            if best_match:
                material = best_match["material"]
                quantity = float(item.qty) if item.qty else 0
                unit_price = float(material.unit_price)
                line_total = Decimal(str(quantity)) * Decimal(str(unit_price))

                line_items.append(LineItemResponse(
                    takeoff_item_id=item_id,
                    label=item.label,
                    quantity=quantity,
                    unit=item.unit,
                    matched_material_code=material.product_code,
                    matched_material_desc=material.description,
                    unit_price=unit_price,
                    line_total=float(line_total),
                    match_confidence=best_match["confidence"]
                ))

                total_materials_cost += line_total
                matched_count += 1
            else:
                # No match found
                unmatched_items.append(item.label)
                line_items.append(LineItemResponse(
                    takeoff_item_id=item_id,
                    label=item.label,
                    quantity=float(item.qty) if item.qty else 0,
                    unit=item.unit,
                    matched_material_code=None,
                    matched_material_desc=None,
                    unit_price=0.0,
                    line_total=0.0,
                    match_confidence=None
                ))

        # Get company rates
        company_rates = db.query(CompanyRates).filter(
            CompanyRates.company_id == current_user.company_id
        ).first()

        # Calculate overhead and profit
        labor_cost = Decimal("0")  # STINE is materials-only
        equipment_cost = Decimal("0")
        subcontractor_cost = Decimal("0")

        subtotal = total_materials_cost + labor_cost + equipment_cost + subcontractor_cost

        # Apply overhead
        if request.apply_overhead and company_rates:
            overhead_config = company_rates.overhead_json or {}
            overhead_percent = Decimal(str(overhead_config.get("base_overhead_percent", 12.0)))
            overhead = (subtotal * overhead_percent / Decimal("100"))
        else:
            overhead_percent = Decimal("0")
            overhead = Decimal("0")

        # Apply profit
        if request.apply_profit and company_rates:
            margin_config = company_rates.margin_json or {}
            profit_percent = Decimal(str(margin_config.get("profit_margin_target", 10.0)))

            # Apply volume discounts
            volume_tiers = margin_config.get("volume_discount_tiers", {})
            subtotal_with_overhead = subtotal + overhead

            for tier_amount, discount in sorted(volume_tiers.items(), key=lambda x: float(x[0]), reverse=True):
                if float(subtotal_with_overhead) >= float(tier_amount):
                    discount_amount = Decimal(str(discount))
                    profit_percent = profit_percent - discount_amount
                    logger.info(f"Applied volume discount: {discount}% off profit margin")
                    break

            profit = (subtotal_with_overhead * profit_percent / Decimal("100"))
        else:
            profit_percent = Decimal("0")
            profit = Decimal("0")

        total_cost = subtotal + overhead + profit

        # Tax (9% for Louisiana - from Quote 684107)
        tax_rate = Decimal("9.0")
        tax_amount = total_cost * tax_rate / Decimal("100")
        grand_total = total_cost + tax_amount

        # Create estimate record
        estimate = Estimate(
            project_id=project_id_str,
            created_by=str(current_user.id),
            materials_cost=total_materials_cost,
            labor_cost=labor_cost,
            equipment_cost=equipment_cost,
            subcontractor_cost=subcontractor_cost,
            overhead=overhead,
            profit=profit,
            total_cost=grand_total,
            confidence_score=Decimal(str(matched_count / len(takeoff_items) if takeoff_items else 0)),
            notes=f"Generated from {len(takeoff_items)} takeoff items. {matched_count} matched, {len(unmatched_items)} unmatched."
        )

        db.add(estimate)
        db.commit()
        db.refresh(estimate)

        # Build response
        breakdown = EstimateBreakdown(
            line_items=line_items,
            materials_cost=float(total_materials_cost),
            labor_cost=float(labor_cost),
            equipment_cost=float(equipment_cost),
            subcontractor_cost=float(subcontractor_cost),
            subtotal=float(subtotal),
            overhead=float(overhead),
            overhead_percentage=float(overhead_percent),
            profit=float(profit),
            profit_percentage=float(profit_percent),
            total_cost=float(total_cost),
            tax_rate=float(tax_rate),
            tax_amount=float(tax_amount),
            grand_total=float(grand_total)
        )

        if unmatched_items:
            errors.append(f"{len(unmatched_items)} items could not be matched: {', '.join(unmatched_items[:5])}")

        return EstimateResponse(
            success=True,
            estimate_id=str(estimate.id),
            project_id=project_id_str,
            breakdown=breakdown,
            summary={
                "total_items": len(takeoff_items),
                "matched_items": matched_count,
                "unmatched_items": len(unmatched_items),
                "grand_total": float(grand_total),
                "confidence": float(estimate.confidence_score)
            },
            errors=errors
        )

    except Exception as e:
        logger.error(f"Failed to generate estimate: {str(e)}", exc_info=True)
        return EstimateResponse(
            success=False,
            estimate_id=None,
            project_id=project_id_str,
            breakdown=None,
            summary={},
            errors=[str(e)]
        )


@router.get("/{estimate_id}")
async def get_estimate(
    estimate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get an existing estimate by ID"""
    estimate = db.query(Estimate).filter(
        Estimate.id == estimate_id
    ).first()

    if not estimate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estimate not found"
        )

    # Verify user has access to this estimate's project
    project = db.query(Project).filter(
        Project.id == estimate.project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return {
        "id": str(estimate.id),
        "project_id": str(estimate.project_id),
        "materials_cost": float(estimate.materials_cost),
        "labor_cost": float(estimate.labor_cost),
        "equipment_cost": float(estimate.equipment_cost),
        "subcontractor_cost": float(estimate.subcontractor_cost),
        "overhead": float(estimate.overhead),
        "profit": float(estimate.profit),
        "total_cost": float(estimate.total_cost),
        "confidence_score": float(estimate.confidence_score) if estimate.confidence_score else None,
        "notes": estimate.notes,
        "created_at": estimate.created_at.isoformat() if estimate.created_at else None
    }


@router.get("/project/{project_id}")
async def list_project_estimates(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all estimates for a project"""
    # Verify access
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    estimates = db.query(Estimate).filter(
        Estimate.project_id == project_id
    ).order_by(Estimate.created_at.desc()).all()

    return {
        "project_id": project_id,
        "total_estimates": len(estimates),
        "estimates": [
            {
                "id": str(est.id),
                "total_cost": float(est.total_cost),
                "confidence_score": float(est.confidence_score) if est.confidence_score else None,
                "created_at": est.created_at.isoformat() if est.created_at else None,
                "notes": est.notes
            }
            for est in estimates
        ]
    }


@router.get("/{estimate_id}/pdf")
async def export_estimate_pdf(
    estimate_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export estimate as professional PDF quote

    Returns a formatted PDF matching STINE's quote style with:
    - Company branding and contact info
    - Project details
    - Line items organized by category
    - Subtotals per section
    - Overhead, profit, tax breakdown
    - Terms and conditions
    - Signature line
    """
    try:
        # Get estimate
        estimate = db.query(Estimate).filter(
            Estimate.id == estimate_id
        ).first()

        if not estimate:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Estimate not found"
            )

        # Get project and verify access
        project = db.query(Project).filter(
            Project.id == estimate.project_id,
            Project.company_id == current_user.company_id
        ).first()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Get company info
        company = db.query(Company).filter(
            Company.id == current_user.company_id
        ).first()

        # Get company rates
        company_rates = db.query(CompanyRates).filter(
            CompanyRates.company_id == current_user.company_id
        ).first()

        # Get all takeoff items with materials
        takeoff_items = db.query(TakeoffItem).filter(
            TakeoffItem.project_id == str(estimate.project_id)
        ).all()

        # Match items to materials and build line items
        matches_dict = match_takeoff_to_materials(
            db=db,
            company_id=str(current_user.company_id),
            takeoff_items=takeoff_items,
            threshold=70
        )

        line_items = []
        for item in takeoff_items:
            item_id = str(item.id)
            matches = matches_dict.get(item_id, [])

            if matches and matches[0]["confidence"] >= 0.7:
                material = matches[0]["material"]
                quantity = float(item.qty) if item.qty else 0
                unit_price = float(material.unit_price)
                line_total = quantity * unit_price

                line_items.append({
                    "product_code": material.product_code,
                    "description": material.description,
                    "category": material.category,
                    "quantity": quantity,
                    "unit": item.unit or material.unit,
                    "unit_price": unit_price,
                    "line_total": line_total
                })

        # Calculate pricing breakdown
        overhead_config = company_rates.overhead_json or {} if company_rates else {}
        margin_config = company_rates.margin_json or {} if company_rates else {}

        overhead_percent = Decimal(str(overhead_config.get("base_overhead_percent", 12.0)))
        profit_percent = Decimal(str(margin_config.get("profit_margin_target", 10.0)))

        # Build quote data
        quote_data = {
            "quote_number": f"Q-{str(estimate.id)[:8].upper()}",
            "created_at": estimate.created_at.strftime("%Y-%m-%d") if estimate.created_at else None
        }

        estimate_data = {
            "materials_cost": float(estimate.materials_cost),
            "labor_cost": float(estimate.labor_cost),
            "equipment_cost": float(estimate.equipment_cost),
            "subcontractor_cost": float(estimate.subcontractor_cost),
            "overhead": float(estimate.overhead),
            "overhead_percentage": float(overhead_percent),
            "profit": float(estimate.profit),
            "profit_percentage": float(profit_percent),
            "tax_rate": 9.0,
            "tax_amount": float(estimate.total_cost * Decimal("0.09") / Decimal("1.09")),
            "total_cost": float(estimate.total_cost)
        }

        company_info = {
            "name": company.name if company else "Company Name",
            "address": "123 Business St, Lafayette, LA 70508",
            "phone": "(337) 555-1234",
            "email": company.email if company else "info@company.com",
            "website": "www.stinehome.com"
        }

        project_info = {
            "name": project.name,
            "location": project.location or "",
            "job_number": project.job_number or "",
            "customer_name": "Customer Name",
            "customer_address": "",
            "customer_phone": "",
            "customer_email": ""
        }

        # Generate PDF
        pdf_path = generate_quote_pdf(
            quote_data=quote_data,
            estimate_data=estimate_data,
            line_items=line_items,
            company_info=company_info,
            project_info=project_info
        )

        # Return PDF file
        filename = f"Quote_{quote_data['quote_number']}_{project.job_number or project.name}.pdf"
        return FileResponse(
            path=pdf_path,
            media_type="application/pdf",
            filename=filename
        )

    except Exception as e:
        logger.error(f"Failed to generate PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )
