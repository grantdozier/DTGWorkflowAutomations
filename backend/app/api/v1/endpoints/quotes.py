from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from collections import defaultdict

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.estimation import Quote, TakeoffItem
from app.models.vendor import Vendor
from app.models.project import Project
from app.api.v1.schemas.quote import (
    QuoteCreate,
    QuoteUpdate,
    QuoteResponse,
    QuoteStatusUpdate,
    QuoteComparison,
    QuoteComparisonItem,
    QuoteRankingCriteria,
    QuoteRankingResult,
    QuoteListResponse,
    QuoteSummary
)

router = APIRouter()


@router.post("/projects/{project_id}/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    project_id: UUID,
    quote_data: QuoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create new quote (manual entry)"""
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

    # If vendor_id provided, verify and populate vendor info
    if quote_data.vendor_id:
        vendor = db.query(Vendor).filter(
            Vendor.id == quote_data.vendor_id,
            Vendor.company_id == current_user.company_id
        ).first()
        if vendor:
            quote_data.vendor_name = vendor.name
            quote_data.vendor_email = vendor.email
            quote_data.vendor_phone = vendor.phone

    # Calculate total_price if not provided
    if not quote_data.total_price:
        quote_data.total_price = quote_data.quantity * quote_data.unit_price

    quote = Quote(
        **quote_data.dict(),
        project_id=project_id
    )
    db.add(quote)
    db.commit()
    db.refresh(quote)
    return quote


@router.get("/projects/{project_id}/quotes", response_model=QuoteListResponse)
async def list_quotes(
    project_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status"),
    vendor_id: Optional[UUID] = Query(None),
    takeoff_item_id: Optional[UUID] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all quotes for a project with optional filters"""
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

    query = db.query(Quote).filter(Quote.project_id == project_id)

    if status_filter:
        query = query.filter(Quote.status == status_filter)
    if vendor_id:
        query = query.filter(Quote.vendor_id == vendor_id)
    if takeoff_item_id:
        query = query.filter(Quote.takeoff_item_id == takeoff_item_id)

    total = query.count()
    quotes = query.order_by(Quote.created_at.desc()).offset(skip).limit(limit).all()

    return QuoteListResponse(total=total, quotes=quotes)


@router.get("/projects/{project_id}/quotes/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    project_id: UUID,
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quote details"""
    quote = db.query(Quote).join(Project).filter(
        Quote.id == quote_id,
        Quote.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    return quote


@router.put("/projects/{project_id}/quotes/{quote_id}", response_model=QuoteResponse)
async def update_quote(
    project_id: UUID,
    quote_id: UUID,
    quote_data: QuoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update quote"""
    quote = db.query(Quote).join(Project).filter(
        Quote.id == quote_id,
        Quote.project_id == project_id,
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

    # Recalculate total_price if quantity or unit_price changed
    if 'quantity' in update_data or 'unit_price' in update_data:
        quote.total_price = quote.quantity * quote.unit_price

    db.commit()
    db.refresh(quote)
    return quote


@router.delete("/projects/{project_id}/quotes/{quote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quote(
    project_id: UUID,
    quote_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete quote"""
    quote = db.query(Quote).join(Project).filter(
        Quote.id == quote_id,
        Quote.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    db.delete(quote)
    db.commit()
    return None


@router.patch("/projects/{project_id}/quotes/{quote_id}/status", response_model=QuoteResponse)
async def update_quote_status(
    project_id: UUID,
    quote_id: UUID,
    status_data: QuoteStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update quote status (accept/reject)"""
    quote = db.query(Quote).join(Project).filter(
        Quote.id == quote_id,
        Quote.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not quote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote not found"
        )

    quote.status = status_data.status

    # If accepting, reject other quotes for the same item
    if status_data.status == "accepted" and quote.takeoff_item_id:
        db.query(Quote).filter(
            Quote.project_id == project_id,
            Quote.takeoff_item_id == quote.takeoff_item_id,
            Quote.id != quote_id,
            Quote.status == "pending"
        ).update({"status": "rejected"})

    db.commit()
    db.refresh(quote)
    return quote


@router.get("/projects/{project_id}/quotes/compare", response_model=List[QuoteComparison])
async def compare_quotes(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Compare quotes grouped by item"""
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

    # Get all quotes for the project
    quotes = db.query(Quote).filter(Quote.project_id == project_id).all()

    # Group quotes by item description
    grouped_quotes = defaultdict(list)
    for quote in quotes:
        # Use takeoff_item_id if available, otherwise group by description
        key = quote.takeoff_item_id if quote.takeoff_item_id else quote.item_description
        grouped_quotes[key].append(quote)

    comparisons = []

    for key, item_quotes in grouped_quotes.items():
        if len(item_quotes) < 1:
            continue

        # Get vendor ratings
        quote_items = []
        prices = []

        for quote in item_quotes:
            vendor_rating = None
            if quote.vendor_id:
                vendor = db.query(Vendor).filter(Vendor.id == quote.vendor_id).first()
                if vendor:
                    vendor_rating = vendor.rating

            quote_items.append(QuoteComparisonItem(
                quote_id=quote.id,
                vendor_name=quote.vendor_name,
                unit_price=quote.unit_price,
                total_price=quote.total_price,
                lead_time_days=quote.lead_time_days,
                vendor_rating=vendor_rating,
                notes=quote.notes,
                status=quote.status
            ))
            prices.append(float(quote.total_price))

        # Calculate statistics
        lowest_price = Decimal(str(min(prices)))
        highest_price = Decimal(str(max(prices)))
        average_price = Decimal(str(sum(prices) / len(prices)))

        # Determine recommended quote
        recommended_id, reason = _determine_recommended_quote(quote_items)

        # Use first quote as reference for description
        first_quote = item_quotes[0]

        comparisons.append(QuoteComparison(
            item_description=first_quote.item_description,
            quantity=first_quote.quantity,
            unit=first_quote.unit,
            quotes=quote_items,
            lowest_price=lowest_price,
            highest_price=highest_price,
            average_price=average_price,
            recommended_quote_id=recommended_id,
            recommendation_reason=reason
        ))

    return comparisons


@router.post("/projects/{project_id}/quotes/rank", response_model=List[QuoteRankingResult])
async def rank_quotes(
    project_id: UUID,
    criteria: QuoteRankingCriteria = QuoteRankingCriteria(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rank quotes using weighted criteria"""
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

    # Validate weights sum to 1
    total_weight = criteria.price_weight + criteria.rating_weight + criteria.lead_time_weight
    if abs(total_weight - 1.0) > 0.01:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Criteria weights must sum to 1.0"
        )

    # Get all quotes for the project
    quotes = db.query(Quote).filter(
        Quote.project_id == project_id,
        Quote.status == "pending"
    ).all()

    if not quotes:
        return []

    # Calculate scores
    rankings = []
    prices = [float(q.total_price) for q in quotes]
    max_price = max(prices)
    min_price = min(prices)
    price_range = max_price - min_price if max_price > min_price else 1

    for quote in quotes:
        # Price score (lower is better, so invert)
        price_score = 1.0 - ((float(quote.total_price) - min_price) / price_range) if price_range > 0 else 1.0

        # Rating score
        rating_score = 0.0
        if quote.vendor_id:
            vendor = db.query(Vendor).filter(Vendor.id == quote.vendor_id).first()
            if vendor and vendor.rating:
                rating_score = float(vendor.rating) / 5.0  # Normalize to 0-1

        # Lead time score (shorter is better, so invert)
        lead_time_score = 0.5  # Default if no lead time
        if quote.lead_time_days is not None:
            max_lead_time = 90  # Assume 90 days as maximum reasonable lead time
            lead_time_score = 1.0 - (min(quote.lead_time_days, max_lead_time) / max_lead_time)

        # Calculate weighted total score
        total_score = (
            price_score * criteria.price_weight +
            rating_score * criteria.rating_weight +
            lead_time_score * criteria.lead_time_weight
        )

        rankings.append(QuoteRankingResult(
            quote_id=quote.id,
            vendor_name=quote.vendor_name,
            total_score=round(total_score, 4),
            price_score=round(price_score, 4),
            rating_score=round(rating_score, 4),
            lead_time_score=round(lead_time_score, 4),
            rank=0  # Will be assigned after sorting
        ))

    # Sort by total score (descending) and assign ranks
    rankings.sort(key=lambda x: x.total_score, reverse=True)
    for i, ranking in enumerate(rankings):
        ranking.rank = i + 1

    return rankings


@router.get("/projects/{project_id}/quotes/summary", response_model=QuoteSummary)
async def get_quote_summary(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quote summary statistics for a project"""
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

    # Get quote counts by status
    total_quotes = db.query(func.count(Quote.id)).filter(Quote.project_id == project_id).scalar()
    pending_quotes = db.query(func.count(Quote.id)).filter(
        Quote.project_id == project_id,
        Quote.status == "pending"
    ).scalar()
    accepted_quotes = db.query(func.count(Quote.id)).filter(
        Quote.project_id == project_id,
        Quote.status == "accepted"
    ).scalar()
    rejected_quotes = db.query(func.count(Quote.id)).filter(
        Quote.project_id == project_id,
        Quote.status == "rejected"
    ).scalar()

    # Get total values
    total_value_pending = db.query(func.sum(Quote.total_price)).filter(
        Quote.project_id == project_id,
        Quote.status == "pending"
    ).scalar() or Decimal(0)

    total_value_accepted = db.query(func.sum(Quote.total_price)).filter(
        Quote.project_id == project_id,
        Quote.status == "accepted"
    ).scalar() or Decimal(0)

    # Get items with/without quotes
    takeoff_items = db.query(TakeoffItem).filter(TakeoffItem.project_id == project_id).all()
    items_with_quotes = len(set(q.takeoff_item_id for q in db.query(Quote).filter(
        Quote.project_id == project_id
    ).all() if q.takeoff_item_id))
    items_without_quotes = len(takeoff_items) - items_with_quotes

    return QuoteSummary(
        total_quotes=total_quotes,
        pending_quotes=pending_quotes,
        accepted_quotes=accepted_quotes,
        rejected_quotes=rejected_quotes,
        total_value_pending=total_value_pending,
        total_value_accepted=total_value_accepted,
        items_with_quotes=items_with_quotes,
        items_without_quotes=items_without_quotes
    )


def _determine_recommended_quote(quotes: List[QuoteComparisonItem]) -> tuple:
    """Determine recommended quote based on simple algorithm"""
    if not quotes:
        return None, None

    # Default weights
    PRICE_WEIGHT = 0.7
    RATING_WEIGHT = 0.2
    LEAD_TIME_WEIGHT = 0.1

    best_score = -1
    best_quote_id = None

    prices = [float(q.total_price) for q in quotes]
    max_price = max(prices)
    min_price = min(prices)
    price_range = max_price - min_price if max_price > min_price else 1

    for quote in quotes:
        # Price score (lower is better)
        price_score = 1.0 - ((float(quote.total_price) - min_price) / price_range) if price_range > 0 else 1.0

        # Rating score
        rating_score = float(quote.vendor_rating) / 5.0 if quote.vendor_rating else 0.5

        # Lead time score (shorter is better)
        lead_time_score = 0.5
        if quote.lead_time_days is not None:
            lead_time_score = 1.0 - (min(quote.lead_time_days, 90) / 90)

        # Calculate weighted score
        total_score = (
            price_score * PRICE_WEIGHT +
            rating_score * RATING_WEIGHT +
            lead_time_score * LEAD_TIME_WEIGHT
        )

        if total_score > best_score:
            best_score = total_score
            best_quote_id = quote.quote_id

    reason = f"Best overall value (Score: {best_score:.2f})"
    return best_quote_id, reason
