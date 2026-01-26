from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from uuid import UUID
import json
from datetime import datetime

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.estimation import QuoteRequest, TakeoffItem
from app.models.vendor import Vendor
from app.models.project import Project
from app.services.email_service import EmailService
from app.api.v1.schemas.quote_request import (
    QuoteRequestCreate,
    QuoteRequestResponse,
    QuoteRequestDetail,
    QuoteRequestStatusUpdate,
    QuoteRequestBulkResponse,
    QuoteRequestSummary
)

router = APIRouter()


@router.post("/projects/{project_id}/quote-requests", response_model=QuoteRequestBulkResponse)
async def create_and_send_quote_requests(
    project_id: UUID,
    request_data: QuoteRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create and send quote requests to multiple vendors"""
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
    takeoff_items = db.query(TakeoffItem).filter(
        TakeoffItem.id.in_(request_data.takeoff_item_ids),
        TakeoffItem.project_id == project_id
    ).all()

    if len(takeoff_items) != len(request_data.takeoff_item_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Some takeoff items not found"
        )

    # Prepare items list for email
    items = [
        {
            "description": item.label,
            "quantity": float(item.qty),
            "unit": item.unit
        }
        for item in takeoff_items
    ]

    success_count = 0
    error_count = 0
    errors = []
    request_ids = []

    # Send to each vendor
    for vendor_id in request_data.vendor_ids:
        try:
            # Get vendor
            vendor = db.query(Vendor).filter(
                Vendor.id == vendor_id,
                Vendor.company_id == current_user.company_id
            ).first()

            if not vendor:
                errors.append({
                    "vendor_id": str(vendor_id),
                    "error": "Vendor not found"
                })
                error_count += 1
                continue

            if not vendor.email:
                errors.append({
                    "vendor_id": str(vendor_id),
                    "vendor_name": vendor.name,
                    "error": "Vendor has no email address"
                })
                error_count += 1
                continue

            # Create email subject and body
            subject = f"Quote Request: {project.name}"

            # Send email
            email_sent = EmailService.send_quote_request(
                to_email=vendor.email,
                to_name=vendor.name,
                project_name=project.name,
                items=items,
                message=request_data.message
            )

            # Create quote request record
            quote_request = QuoteRequest(
                project_id=project_id,
                vendor_id=vendor_id,
                email_subject=subject,
                email_body=request_data.message or "",
                status="sent" if email_sent else "failed",
                expected_response_date=request_data.expected_response_date,
                requested_items=json.dumps([str(id) for id in request_data.takeoff_item_ids])
            )
            db.add(quote_request)
            db.flush()

            if email_sent:
                success_count += 1
                request_ids.append(quote_request.id)
            else:
                error_count += 1
                errors.append({
                    "vendor_id": str(vendor_id),
                    "vendor_name": vendor.name,
                    "error": "Failed to send email"
                })

        except Exception as e:
            error_count += 1
            errors.append({
                "vendor_id": str(vendor_id),
                "error": str(e)
            })

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save quote requests: {str(e)}"
        )

    return QuoteRequestBulkResponse(
        success_count=success_count,
        error_count=error_count,
        errors=errors,
        request_ids=request_ids
    )


@router.get("/projects/{project_id}/quote-requests", response_model=List[QuoteRequestResponse])
async def list_quote_requests(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all quote requests for a project"""
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

    # Get quote requests with vendor info
    requests = db.query(QuoteRequest).filter(
        QuoteRequest.project_id == project_id
    ).order_by(QuoteRequest.sent_at.desc()).all()

    # Build response with vendor names
    response_list = []
    for req in requests:
        vendor = db.query(Vendor).filter(Vendor.id == req.vendor_id).first()
        vendor_name = vendor.name if vendor else "Unknown"
        vendor_email = vendor.email if vendor else None

        # Count requested items
        try:
            requested_items = json.loads(req.requested_items) if req.requested_items else []
            items_count = len(requested_items)
        except:
            items_count = 0

        response_list.append(QuoteRequestResponse(
            id=req.id,
            project_id=req.project_id,
            vendor_id=req.vendor_id,
            vendor_name=vendor_name,
            vendor_email=vendor_email,
            email_subject=req.email_subject,
            sent_at=req.sent_at,
            status=req.status,
            expected_response_date=req.expected_response_date,
            requested_items_count=items_count
        ))

    return response_list


@router.get("/projects/{project_id}/quote-requests/{request_id}", response_model=QuoteRequestDetail)
async def get_quote_request(
    project_id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quote request details"""
    request = db.query(QuoteRequest).join(Project).filter(
        QuoteRequest.id == request_id,
        QuoteRequest.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote request not found"
        )

    # Get vendor info
    vendor = db.query(Vendor).filter(Vendor.id == request.vendor_id).first()
    vendor_name = vendor.name if vendor else "Unknown"
    vendor_email = vendor.email if vendor else None

    # Parse requested items
    try:
        requested_item_ids = json.loads(request.requested_items) if request.requested_items else []
        takeoff_items = db.query(TakeoffItem).filter(
            TakeoffItem.id.in_(requested_item_ids)
        ).all()
        requested_items = [
            {
                "id": str(item.id),
                "description": item.label,
                "quantity": float(item.qty),
                "unit": item.unit
            }
            for item in takeoff_items
        ]
    except:
        requested_items = []

    return QuoteRequestDetail(
        id=request.id,
        project_id=request.project_id,
        vendor_id=request.vendor_id,
        vendor_name=vendor_name,
        vendor_email=vendor_email,
        email_subject=request.email_subject,
        email_body=request.email_body,
        sent_at=request.sent_at,
        status=request.status,
        expected_response_date=request.expected_response_date,
        requested_items=requested_items
    )


@router.patch("/projects/{project_id}/quote-requests/{request_id}/status", response_model=QuoteRequestResponse)
async def update_quote_request_status(
    project_id: UUID,
    request_id: UUID,
    status_data: QuoteRequestStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update quote request status"""
    request = db.query(QuoteRequest).join(Project).filter(
        QuoteRequest.id == request_id,
        QuoteRequest.project_id == project_id,
        Project.company_id == current_user.company_id
    ).first()

    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quote request not found"
        )

    request.status = status_data.status
    db.commit()

    # Get vendor info for response
    vendor = db.query(Vendor).filter(Vendor.id == request.vendor_id).first()
    vendor_name = vendor.name if vendor else "Unknown"
    vendor_email = vendor.email if vendor else None

    try:
        requested_items = json.loads(request.requested_items) if request.requested_items else []
        items_count = len(requested_items)
    except:
        items_count = 0

    return QuoteRequestResponse(
        id=request.id,
        project_id=request.project_id,
        vendor_id=request.vendor_id,
        vendor_name=vendor_name,
        vendor_email=vendor_email,
        email_subject=request.email_subject,
        sent_at=request.sent_at,
        status=request.status,
        expected_response_date=request.expected_response_date,
        requested_items_count=items_count
    )


@router.get("/projects/{project_id}/quote-requests/summary", response_model=QuoteRequestSummary)
async def get_quote_request_summary(
    project_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get quote request summary statistics"""
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

    total_requests = db.query(func.count(QuoteRequest.id)).filter(
        QuoteRequest.project_id == project_id
    ).scalar()

    sent_count = db.query(func.count(QuoteRequest.id)).filter(
        QuoteRequest.project_id == project_id,
        QuoteRequest.status == "sent"
    ).scalar()

    responded_count = db.query(func.count(QuoteRequest.id)).filter(
        QuoteRequest.project_id == project_id,
        QuoteRequest.status == "responded"
    ).scalar()

    expired_count = db.query(func.count(QuoteRequest.id)).filter(
        QuoteRequest.project_id == project_id,
        QuoteRequest.status == "expired"
    ).scalar()

    pending_count = total_requests - responded_count - expired_count

    return QuoteRequestSummary(
        total_requests=total_requests,
        sent_count=sent_count,
        responded_count=responded_count,
        expired_count=expired_count,
        pending_count=pending_count
    )


@router.post("/projects/{project_id}/quote-requests/bulk-send", response_model=QuoteRequestBulkResponse)
async def bulk_send_quote_requests(
    project_id: UUID,
    request_data: QuoteRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk send quote requests to multiple vendors (alias for create_and_send_quote_requests)"""
    return await create_and_send_quote_requests(project_id, request_data, db, current_user)
