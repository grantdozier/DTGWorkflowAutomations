from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.company import Company, CompanyRates
from app.api.v1.schemas.company import (
    CompanyResponse,
    CompanyUpdate,
    CompanyRatesCreate,
    CompanyRatesUpdate,
    CompanyRatesResponse,
    LaborRateExample,
    EquipmentRateExample,
    OverheadExample,
    MarginExample
)

router = APIRouter()


@router.get("/me", response_model=CompanyResponse)
async def get_my_company(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's company information
    """
    company = db.query(Company).filter(Company.id == current_user.company_id).first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Get company rates if they exist
    rates = db.query(CompanyRates).filter(
        CompanyRates.company_id == company.id
    ).first()

    return {
        **company.__dict__,
        "rates": rates
    }


@router.put("/me", response_model=CompanyResponse)
async def update_my_company(
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's company information
    """
    company = db.query(Company).filter(Company.id == current_user.company_id).first()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Update fields
    if company_data.name is not None:
        company.name = company_data.name

    db.commit()
    db.refresh(company)

    # Get company rates
    rates = db.query(CompanyRates).filter(
        CompanyRates.company_id == company.id
    ).first()

    return {
        **company.__dict__,
        "rates": rates
    }


@router.get("/rates", response_model=CompanyRatesResponse)
async def get_company_rates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current company's rates configuration
    """
    rates = db.query(CompanyRates).filter(
        CompanyRates.company_id == current_user.company_id
    ).first()

    if not rates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company rates not found. Create them first with POST /rates"
        )

    return rates


@router.post("/rates", response_model=CompanyRatesResponse, status_code=status.HTTP_201_CREATED)
async def create_company_rates(
    rates_data: CompanyRatesCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create company rates configuration

    Example labor_rate_json:
    {
        "foreman": 45.00,
        "operator": 35.00,
        "laborer": 25.00
    }

    Example equipment_rate_json:
    {
        "excavator": 125.00,
        "bulldozer": 150.00,
        "dump_truck": 85.00
    }

    Example overhead_json:
    {
        "percentage": 15.0,
        "fixed_costs": 10000.00
    }

    Example margin_json:
    {
        "default_percentage": 10.0,
        "minimum_percentage": 5.0
    }
    """
    # Check if rates already exist
    existing_rates = db.query(CompanyRates).filter(
        CompanyRates.company_id == current_user.company_id
    ).first()

    if existing_rates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company rates already exist. Use PUT /rates to update."
        )

    # Create new rates
    rates = CompanyRates(
        company_id=current_user.company_id,
        labor_rate_json=rates_data.labor_rate_json,
        equipment_rate_json=rates_data.equipment_rate_json,
        overhead_json=rates_data.overhead_json,
        margin_json=rates_data.margin_json
    )

    db.add(rates)
    db.commit()
    db.refresh(rates)

    return rates


@router.put("/rates", response_model=CompanyRatesResponse)
async def update_company_rates(
    rates_data: CompanyRatesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update company rates configuration
    """
    rates = db.query(CompanyRates).filter(
        CompanyRates.company_id == current_user.company_id
    ).first()

    if not rates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company rates not found. Create them first with POST /rates"
        )

    # Update fields (only if provided)
    if rates_data.labor_rate_json is not None:
        rates.labor_rate_json = rates_data.labor_rate_json
    if rates_data.equipment_rate_json is not None:
        rates.equipment_rate_json = rates_data.equipment_rate_json
    if rates_data.overhead_json is not None:
        rates.overhead_json = rates_data.overhead_json
    if rates_data.margin_json is not None:
        rates.margin_json = rates_data.margin_json

    db.commit()
    db.refresh(rates)

    return rates


@router.post("/rates/bulk-update", response_model=CompanyRatesResponse)
async def bulk_update_company_rates(
    rates_data: CompanyRatesCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update all company rates in a single call (wizard-friendly)

    This endpoint is idempotent and will:
    - Create rates if they don't exist
    - Update rates if they already exist

    Perfect for onboarding wizard where you want to save all rates at once.

    Example request body:
    {
        "labor_rate_json": {"foreman": 45.00, "operator": 35.00, "laborer": 25.00},
        "equipment_rate_json": {"excavator": {"hourly": 125.00, "daily": 900.00}},
        "overhead_json": {"percentage": 15.0},
        "margin_json": {"profit": 10.0, "bond": 2.0, "contingency": 5.0}
    }
    """
    # Check if rates already exist
    rates = db.query(CompanyRates).filter(
        CompanyRates.company_id == current_user.company_id
    ).first()

    if rates:
        # Update existing rates
        rates.labor_rate_json = rates_data.labor_rate_json
        rates.equipment_rate_json = rates_data.equipment_rate_json
        rates.overhead_json = rates_data.overhead_json
        rates.margin_json = rates_data.margin_json
    else:
        # Create new rates
        rates = CompanyRates(
            company_id=current_user.company_id,
            labor_rate_json=rates_data.labor_rate_json,
            equipment_rate_json=rates_data.equipment_rate_json,
            overhead_json=rates_data.overhead_json,
            margin_json=rates_data.margin_json
        )
        db.add(rates)

    db.commit()
    db.refresh(rates)

    return rates


@router.get("/rates/examples")
async def get_rate_examples(
    current_user: User = Depends(get_current_user)
):
    """
    Get example rate structures for reference
    """
    return {
        "labor_rate_json": LaborRateExample().model_dump(),
        "equipment_rate_json": EquipmentRateExample().model_dump(),
        "overhead_json": OverheadExample().model_dump(),
        "margin_json": MarginExample().model_dump()
    }
