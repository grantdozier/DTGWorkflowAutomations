import logging
from decimal import Decimal
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.estimation import TakeoffItem, Quote, Estimate
from app.models.company import CompanyRates

logger = logging.getLogger(__name__)


class EstimationEngine:
    """
    Generate cost estimates from takeoff items and company rates
    """

    def __init__(self):
        pass

    async def generate_estimate(
        self,
        project_id: str,
        user_id: str,
        db: Session,
        overhead_percentage: Optional[float] = None,
        profit_percentage: Optional[float] = None
    ) -> Dict:
        """
        Generate a complete project estimate

        Args:
            project_id: Project ID
            user_id: User creating the estimate
            db: Database session
            overhead_percentage: Override overhead percentage
            profit_percentage: Override profit percentage

        Returns:
            Dictionary with estimate data and breakdown
        """
        try:
            # Get project
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {"success": False, "error": "Project not found"}

            # Get company rates
            company_rates = db.query(CompanyRates).filter(
                CompanyRates.company_id == project.company_id
            ).first()

            # Get takeoff items
            takeoff_items = db.query(TakeoffItem).filter(
                TakeoffItem.project_id == project_id
            ).all()

            if not takeoff_items:
                return {
                    "success": False,
                    "error": "No takeoff items found. Parse a plan document first."
                }

            # Initialize cost components
            materials_cost = Decimal("0")
            labor_cost = Decimal("0")
            equipment_cost = Decimal("0")
            subcontractor_cost = Decimal("0")

            # Calculate costs for each takeoff item
            item_details = []
            for item in takeoff_items:
                # Estimate material cost (simplified - could integrate with quotes)
                item_material_cost = await self._estimate_material_cost(item, db)
                materials_cost += item_material_cost

                # Estimate labor cost
                item_labor_cost, labor_hours = await self._estimate_labor_cost(
                    item, company_rates
                )
                labor_cost += item_labor_cost

                # Estimate equipment cost
                item_equipment_cost = await self._estimate_equipment_cost(
                    item, company_rates, labor_hours
                )
                equipment_cost += item_equipment_cost

                # Add item detail
                item_details.append({
                    "item_id": str(item.id),
                    "description": item.label,
                    "quantity": float(item.qty),
                    "unit": item.unit,
                    "unit_cost": float(item_material_cost / item.qty) if item.qty > 0 else 0,
                    "total_cost": float(item_material_cost),
                    "labor_hours": labor_hours,
                    "category": "material"
                })

            # Calculate overhead
            direct_costs = materials_cost + labor_cost + equipment_cost + subcontractor_cost

            if overhead_percentage is not None:
                overhead = direct_costs * Decimal(str(overhead_percentage / 100))
            else:
                overhead = await self._calculate_overhead(company_rates, direct_costs)

            # Calculate profit
            subtotal = direct_costs + overhead

            if profit_percentage is not None:
                profit = subtotal * Decimal(str(profit_percentage / 100))
            else:
                profit = await self._calculate_profit(company_rates, subtotal)

            # Calculate total
            total_cost = subtotal + profit

            # Calculate confidence score based on data quality
            confidence_score = self._calculate_confidence(
                len(takeoff_items),
                bool(company_rates)
            )

            # Create estimate record
            estimate = Estimate(
                project_id=project_id,
                created_by=user_id,
                materials_cost=materials_cost,
                labor_cost=labor_cost,
                equipment_cost=equipment_cost,
                subcontractor_cost=subcontractor_cost,
                overhead=overhead,
                profit=profit,
                total_cost=total_cost,
                confidence_score=Decimal(str(confidence_score))
            )

            db.add(estimate)
            db.commit()
            db.refresh(estimate)

            return {
                "success": True,
                "estimate": estimate,
                "breakdown": {
                    "materials": float(materials_cost),
                    "labor": float(labor_cost),
                    "equipment": float(equipment_cost),
                    "subcontractors": float(subcontractor_cost),
                    "subtotal": float(direct_costs),
                    "overhead": float(overhead),
                    "profit": float(profit),
                    "total": float(total_cost)
                },
                "items": item_details,
                "summary": {
                    "total_items": len(takeoff_items),
                    "confidence_score": confidence_score
                }
            }

        except Exception as e:
            logger.error(f"Failed to generate estimate: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _estimate_material_cost(
        self,
        item: TakeoffItem,
        db: Session
    ) -> Decimal:
        """
        Estimate material cost for a takeoff item

        In a full system, this would:
        1. Look up accepted quotes
        2. Use historical pricing data
        3. Apply unit cost databases

        For now, using simplified estimation
        """
        # Check for accepted quotes
        quote = db.query(Quote).filter(
            Quote.project_id == item.project_id,
            Quote.item_description.ilike(f"%{item.label}%"),
            Quote.status == "accepted"
        ).first()

        if quote and quote.total_price:
            return Decimal(str(quote.total_price))

        # Fallback: use simplified unit cost estimation
        unit_costs = {
            "CY": Decimal("50.00"),   # Cubic yards (excavation, concrete)
            "SY": Decimal("30.00"),   # Square yards (paving, surfacing)
            "LF": Decimal("15.00"),   # Linear feet (curb, pipe)
            "EA": Decimal("100.00"),  # Each (signs, fixtures)
            "LS": Decimal("5000.00"), # Lump sum
            "TON": Decimal("40.00"),  # Tons (asphalt, aggregate)
        }

        unit_cost = unit_costs.get(item.unit.upper(), Decimal("25.00"))
        return unit_cost * Decimal(str(item.qty))

    async def _estimate_labor_cost(
        self,
        item: TakeoffItem,
        company_rates: Optional[CompanyRates]
    ) -> tuple[Decimal, float]:
        """
        Estimate labor cost and hours

        Returns:
            (labor_cost, labor_hours)
        """
        # Simplified productivity rates (hours per unit)
        productivity_rates = {
            "CY": 0.5,   # 0.5 hours per cubic yard
            "SY": 0.2,   # 0.2 hours per square yard
            "LF": 0.1,   # 0.1 hours per linear foot
            "EA": 2.0,   # 2 hours per item
            "LS": 40.0,  # 40 hours per lump sum
            "TON": 0.3,  # 0.3 hours per ton
        }

        # Calculate labor hours
        productivity = productivity_rates.get(item.unit.upper(), 0.5)
        labor_hours = float(item.qty) * productivity

        # Get labor rate
        if company_rates and company_rates.labor_rate_json:
            # Use average of configured labor rates
            rates = company_rates.labor_rate_json.values()
            avg_rate = sum(rates) / len(rates) if rates else 35.0
        else:
            avg_rate = 35.0  # Default rate

        labor_cost = Decimal(str(labor_hours * avg_rate))

        return labor_cost, labor_hours

    async def _estimate_equipment_cost(
        self,
        item: TakeoffItem,
        company_rates: Optional[CompanyRates],
        labor_hours: float
    ) -> Decimal:
        """
        Estimate equipment cost based on labor hours
        """
        # Equipment typically costs 20-30% of labor
        equipment_factor = Decimal("0.25")

        if company_rates and company_rates.equipment_rate_json:
            # Could use specific equipment rates here
            pass

        # Simplified: 25% of labor hours at $75/hour
        equipment_hours = labor_hours * float(equipment_factor)
        equipment_rate = Decimal("75.00")

        return Decimal(str(equipment_hours)) * equipment_rate

    async def _calculate_overhead(
        self,
        company_rates: Optional[CompanyRates],
        direct_costs: Decimal
    ) -> Decimal:
        """
        Calculate overhead costs
        """
        if company_rates and company_rates.overhead_json:
            overhead_pct = company_rates.overhead_json.get("percentage", 15.0)
        else:
            overhead_pct = 15.0  # Default 15%

        return direct_costs * Decimal(str(overhead_pct / 100))

    async def _calculate_profit(
        self,
        company_rates: Optional[CompanyRates],
        subtotal: Decimal
    ) -> Decimal:
        """
        Calculate profit margin
        """
        if company_rates and company_rates.margin_json:
            profit_pct = company_rates.margin_json.get("default_percentage", 10.0)
        else:
            profit_pct = 10.0  # Default 10%

        return subtotal * Decimal(str(profit_pct / 100))

    def _calculate_confidence(
        self,
        item_count: int,
        has_rates: bool
    ) -> float:
        """
        Calculate confidence score (0-100)
        """
        score = 50.0  # Base score

        # More items = higher confidence
        if item_count > 10:
            score += 20
        elif item_count > 5:
            score += 10
        elif item_count > 0:
            score += 5

        # Company rates configured = higher confidence
        if has_rates:
            score += 20

        # Cap at 100
        return min(score, 100.0)


# Singleton instance
estimation_engine = EstimationEngine()
