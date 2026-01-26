from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Tuple
from fuzzywuzzy import fuzz
from decimal import Decimal
from uuid import UUID

from app.models.project import ProjectBidItem
from app.models.estimation import TakeoffItem, BidItemDiscrepancy


class DiscrepancyDetector:
    """Service for detecting discrepancies between bid items and takeoff quantities"""

    # Matching threshold for fuzzy text matching (0-100)
    MATCH_THRESHOLD = 70

    # Tolerance for quantity differences (percentage)
    QUANTITY_TOLERANCE = 5.0

    @staticmethod
    def detect_discrepancies(project_id: UUID, db: Session) -> List[BidItemDiscrepancy]:
        """
        Detect discrepancies between bid items and takeoff items for a project

        Args:
            project_id: Project UUID
            db: Database session

        Returns:
            List of detected discrepancies
        """
        # Clear existing discrepancies for this project
        db.query(BidItemDiscrepancy).filter(
            BidItemDiscrepancy.project_id == project_id
        ).delete()

        # Get all bid items for the project
        bid_items = db.query(ProjectBidItem).filter(
            ProjectBidItem.project_id == project_id
        ).all()

        # Get all takeoff items for the project
        takeoff_items = db.query(TakeoffItem).filter(
            TakeoffItem.project_id == project_id
        ).all()

        discrepancies = []

        # Match bid items to takeoff items and check quantities
        for bid_item in bid_items:
            # Find matching takeoff items
            matched_takeoffs = DiscrepancyDetector._find_matching_takeoffs(
                bid_item, takeoff_items
            )

            if not matched_takeoffs:
                # Missing item: Bid item not found in plans
                discrepancy = BidItemDiscrepancy(
                    project_id=project_id,
                    project_bid_item_id=bid_item.id,
                    discrepancy_type="missing_item",
                    severity="high",
                    bid_quantity=bid_item.bid_qty,
                    plan_quantity=None,
                    difference_percentage=None,
                    description=f"Bid item '{DiscrepancyDetector._get_bid_item_description(bid_item, db)}' not found in takeoff/plans",
                    recommendation="Verify that this item is actually required and included in plans"
                )
                db.add(discrepancy)
                discrepancies.append(discrepancy)
            else:
                # Check for quantity mismatches
                for matched_takeoff, similarity_score in matched_takeoffs:
                    discrepancy = DiscrepancyDetector._check_quantity_mismatch(
                        project_id, bid_item, matched_takeoff, db
                    )
                    if discrepancy:
                        db.add(discrepancy)
                        discrepancies.append(discrepancy)

        # Check for extra items: Takeoff items not in bid
        for takeoff_item in takeoff_items:
            matched_bid = DiscrepancyDetector._find_matching_bid_item(
                takeoff_item, bid_items, db
            )

            if not matched_bid:
                discrepancy = BidItemDiscrepancy(
                    project_id=project_id,
                    takeoff_item_id=takeoff_item.id,
                    discrepancy_type="extra_item",
                    severity="medium",
                    bid_quantity=None,
                    plan_quantity=takeoff_item.qty,
                    difference_percentage=None,
                    description=f"Takeoff item '{takeoff_item.label}' not found in bid items",
                    recommendation="Consider if this item needs to be added to the bid"
                )
                db.add(discrepancy)
                discrepancies.append(discrepancy)

        db.commit()
        return discrepancies

    @staticmethod
    def _find_matching_takeoffs(
        bid_item: ProjectBidItem,
        takeoff_items: List[TakeoffItem]
    ) -> List[Tuple[TakeoffItem, int]]:
        """
        Find takeoff items that match a bid item using fuzzy text matching

        Returns list of (takeoff_item, similarity_score) tuples
        """
        matches = []

        # Get bid item description (would need to join with BidItem table)
        bid_description = "unknown"  # Placeholder - need to get from BidItem

        for takeoff in takeoff_items:
            # Compare descriptions
            similarity = fuzz.token_sort_ratio(bid_description.lower(), takeoff.label.lower())

            if similarity >= DiscrepancyDetector.MATCH_THRESHOLD:
                matches.append((takeoff, similarity))

        # Sort by similarity score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    @staticmethod
    def _find_matching_bid_item(
        takeoff_item: TakeoffItem,
        bid_items: List[ProjectBidItem],
        db: Session
    ) -> Optional[ProjectBidItem]:
        """Find bid item that matches a takeoff item"""
        for bid_item in bid_items:
            bid_description = DiscrepancyDetector._get_bid_item_description(bid_item, db)
            similarity = fuzz.token_sort_ratio(bid_description.lower(), takeoff_item.label.lower())

            if similarity >= DiscrepancyDetector.MATCH_THRESHOLD:
                return bid_item

        return None

    @staticmethod
    def _get_bid_item_description(bid_item: ProjectBidItem, db: Session) -> str:
        """Get bid item description from BidItem table"""
        from app.models.project import BidItem
        bid = db.query(BidItem).filter(BidItem.id == bid_item.bid_item_id).first()
        return bid.name if bid else "Unknown"

    @staticmethod
    def _check_quantity_mismatch(
        project_id: UUID,
        bid_item: ProjectBidItem,
        takeoff_item: TakeoffItem,
        db: Session
    ) -> Optional[BidItemDiscrepancy]:
        """Check if quantities match within tolerance"""
        if not bid_item.bid_qty or not takeoff_item.qty:
            return None

        bid_qty = float(bid_item.bid_qty)
        takeoff_qty = float(takeoff_item.qty)

        # Calculate difference percentage
        if bid_qty > 0:
            diff_percentage = abs(((takeoff_qty - bid_qty) / bid_qty) * 100)
        else:
            diff_percentage = 100 if takeoff_qty > 0 else 0

        # Check if difference exceeds tolerance
        if diff_percentage > DiscrepancyDetector.QUANTITY_TOLERANCE:
            # Determine severity based on difference
            if diff_percentage >= 20:
                severity = "critical"
            elif diff_percentage >= 10:
                severity = "high"
            else:
                severity = "medium"

            description = DiscrepancyDetector._get_bid_item_description(bid_item, db)

            return BidItemDiscrepancy(
                project_id=project_id,
                project_bid_item_id=bid_item.id,
                takeoff_item_id=takeoff_item.id,
                discrepancy_type="quantity_mismatch",
                severity=severity,
                bid_quantity=bid_item.bid_qty,
                plan_quantity=takeoff_item.qty,
                difference_percentage=Decimal(str(round(diff_percentage, 2))),
                description=f"Quantity mismatch for '{description}': Bid={bid_qty}, Plan={takeoff_qty}",
                recommendation="Verify quantities with plans and adjust bid if necessary"
            )

        return None

    @staticmethod
    def get_discrepancy_summary(project_id: UUID, db: Session) -> Dict:
        """Get summary statistics of discrepancies for a project"""
        discrepancies = db.query(BidItemDiscrepancy).filter(
            BidItemDiscrepancy.project_id == project_id,
            BidItemDiscrepancy.status == "open"
        ).all()

        summary = {
            "total": len(discrepancies),
            "by_severity": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "by_type": {
                "quantity_mismatch": 0,
                "missing_item": 0,
                "extra_item": 0
            }
        }

        for disc in discrepancies:
            summary["by_severity"][disc.severity] += 1
            summary["by_type"][disc.discrepancy_type] += 1

        return summary
