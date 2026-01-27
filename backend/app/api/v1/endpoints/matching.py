from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from pydantic import BaseModel, UUID4

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.estimation import TakeoffItem
from app.services.material_matcher import MaterialMatcher, match_takeoff_to_materials

router = APIRouter()


# Schemas
class MatchRequest(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    category_hint: Optional[str] = None
    threshold: int = 70


class MaterialMatchResponse(BaseModel):
    material_id: UUID4
    product_code: str
    description: str
    unit_price: float
    unit: str
    category: str
    confidence: float
    match_type: str
    reasoning: str


class MatchResponse(BaseModel):
    matches: List[MaterialMatchResponse]
    total_matches: int


class ProjectMatchRequest(BaseModel):
    project_id: UUID4
    threshold: int = 70


@router.post("/match", response_model=MatchResponse)
def match_description_to_materials(
    request: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Match a single description to materials in catalog

    Use this to test matching or get suggestions for manual entry.
    """
    matcher = MaterialMatcher(db, str(current_user.company_id))

    matches = matcher.match_item(
        description=request.description,
        quantity=request.quantity,
        unit=request.unit,
        category_hint=request.category_hint,
        threshold=request.threshold
    )

    # Convert to response format
    match_responses = []
    for match in matches:
        material = match["material"]
        match_responses.append(MaterialMatchResponse(
            material_id=material.id,
            product_code=material.product_code,
            description=material.description,
            unit_price=float(material.unit_price),
            unit=material.unit,
            category=material.category,
            confidence=match["confidence"],
            match_type=match["match_type"],
            reasoning=match["reasoning"]
        ))

    return MatchResponse(
        matches=match_responses,
        total_matches=len(match_responses)
    )


@router.post("/match/project", response_model=Dict)
def match_project_takeoffs(
    request: ProjectMatchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Match all takeoff items in a project to materials

    Returns suggested matches for each takeoff item.
    """
    # Get all takeoff items for the project
    takeoff_items = db.query(TakeoffItem).filter(
        TakeoffItem.project_id == str(request.project_id)
    ).all()

    if not takeoff_items:
        return {
            "project_id": str(request.project_id),
            "total_items": 0,
            "matches": {},
            "summary": {
                "matched": 0,
                "unmatched": 0,
                "high_confidence": 0,
                "medium_confidence": 0,
                "low_confidence": 0
            }
        }

    # Match all items
    matches_dict = match_takeoff_to_materials(
        db=db,
        company_id=str(current_user.company_id),
        takeoff_items=takeoff_items,
        threshold=request.threshold
    )

    # Calculate summary statistics
    matched_count = sum(1 for matches in matches_dict.values() if matches)
    high_conf = sum(1 for matches in matches_dict.values() if matches and matches[0]["confidence"] >= 0.8)
    med_conf = sum(1 for matches in matches_dict.values() if matches and 0.6 <= matches[0]["confidence"] < 0.8)
    low_conf = sum(1 for matches in matches_dict.values() if matches and matches[0]["confidence"] < 0.6)

    # Format matches for response
    formatted_matches = {}
    for item_id, matches in matches_dict.items():
        # Find the takeoff item
        item = next((i for i in takeoff_items if str(i.id) == item_id), None)
        if not item:
            continue

        formatted_matches[item_id] = {
            "takeoff_item": {
                "id": str(item.id),
                "label": item.label,
                "qty": float(item.qty) if item.qty else 0,
                "unit": item.unit,
                "notes": item.notes
            },
            "matches": [
                {
                    "material_id": str(match["material"].id),
                    "product_code": match["material"].product_code,
                    "description": match["material"].description,
                    "unit_price": float(match["material"].unit_price),
                    "unit": match["material"].unit,
                    "category": match["material"].category,
                    "confidence": match["confidence"],
                    "match_type": match["match_type"],
                    "reasoning": match["reasoning"]
                }
                for match in matches
            ]
        }

    return {
        "project_id": str(request.project_id),
        "total_items": len(takeoff_items),
        "matches": formatted_matches,
        "summary": {
            "matched": matched_count,
            "unmatched": len(takeoff_items) - matched_count,
            "high_confidence": high_conf,
            "medium_confidence": med_conf,
            "low_confidence": low_conf
        }
    }


@router.get("/categories")
def get_matching_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of available categories for category hints"""
    from app.models.material import Material

    categories = db.query(Material.category).filter(
        Material.company_id == current_user.company_id,
        Material.is_active == True
    ).distinct().all()

    return {
        "categories": [cat[0] for cat in categories]
    }


@router.post("/match/project/{project_id}/apply")
def apply_matches_to_project(
    project_id: str,
    threshold: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Match all takeoff items in a project to materials and APPLY the matches.
    
    This updates each takeoff item with:
    - matched_material_id
    - unit_price (from matched material)
    - total_price (qty * unit_price)
    
    Returns summary with total estimated cost.
    """
    from app.models.material import Material
    from decimal import Decimal
    
    # Verify project ownership
    from app.models.project import Project
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.company_id == current_user.company_id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all takeoff items for the project
    takeoff_items = db.query(TakeoffItem).filter(
        TakeoffItem.project_id == project_id
    ).all()

    if not takeoff_items:
        return {
            "project_id": project_id,
            "total_items": 0,
            "matched": 0,
            "unmatched": 0,
            "subtotal": 0,
            "items": []
        }

    # Match all items
    matches_dict = match_takeoff_to_materials(
        db=db,
        company_id=str(current_user.company_id),
        takeoff_items=takeoff_items,
        threshold=threshold
    )

    # Apply matches and calculate totals
    matched_count = 0
    unmatched_count = 0
    subtotal = Decimal("0")
    items_result = []

    for item in takeoff_items:
        item_id = str(item.id)
        matches = matches_dict.get(item_id, [])
        
        if matches:
            # Use best match
            best_match = matches[0]
            material = best_match["material"]
            
            item.matched_material_id = material.id
            item.unit_price = material.unit_price
            item.total_price = item.qty * material.unit_price
            
            subtotal += item.total_price
            matched_count += 1
            
            items_result.append({
                "id": item_id,
                "label": item.label,
                "qty": float(item.qty),
                "unit": item.unit,
                "category": item.category,
                "matched_material": material.description,
                "product_code": material.product_code,
                "unit_price": float(material.unit_price),
                "total_price": float(item.total_price),
                "confidence": best_match["confidence"],
                "status": "matched"
            })
        else:
            # No match found
            item.matched_material_id = None
            item.unit_price = Decimal("0")
            item.total_price = Decimal("0")
            unmatched_count += 1
            
            items_result.append({
                "id": item_id,
                "label": item.label,
                "qty": float(item.qty),
                "unit": item.unit,
                "category": item.category,
                "matched_material": None,
                "product_code": None,
                "unit_price": 0,
                "total_price": 0,
                "confidence": 0,
                "status": "unmatched"
            })

    db.commit()

    return {
        "project_id": project_id,
        "project_name": project.name,
        "total_items": len(takeoff_items),
        "matched": matched_count,
        "unmatched": unmatched_count,
        "subtotal": float(subtotal),
        "items": items_result
    }
