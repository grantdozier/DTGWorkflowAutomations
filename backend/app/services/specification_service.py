from sqlalchemy.orm import Session
from typing import List, Optional, Tuple
from fuzzywuzzy import fuzz
from uuid import UUID

from app.models.specification import SpecificationLibrary, ProjectSpecification


class SpecificationService:
    """Service for specification search, matching, and management"""

    # Matching threshold for fuzzy text matching (0-100)
    MATCH_THRESHOLD = 75
    HIGH_CONFIDENCE = 90
    MEDIUM_CONFIDENCE = 75

    @staticmethod
    def search_specifications(
        query: str,
        category: Optional[str],
        source: Optional[str],
        db: Session,
        limit: int = 20
    ) -> List[SpecificationLibrary]:
        """
        Search specification library

        Args:
            query: Search term
            category: Optional category filter
            source: Optional source filter (ASTM, AASHTO, etc.)
            db: Database session
            limit: Maximum results

        Returns:
            List of matching specifications
        """
        db_query = db.query(SpecificationLibrary)

        if category:
            db_query = db_query.filter(SpecificationLibrary.category == category)
        if source:
            db_query = db_query.filter(SpecificationLibrary.source == source)

        # Get all potential matches
        specs = db_query.all()

        if not query:
            return specs[:limit]

        # Score specifications by relevance
        scored_specs = []
        query_lower = query.lower()

        for spec in specs:
            # Check for exact code match first
            if query.upper() == spec.spec_code:
                scored_specs.append((100, spec))
                continue

            # Score based on multiple fields
            code_score = fuzz.partial_ratio(query_lower, spec.spec_code.lower())
            title_score = fuzz.token_set_ratio(query_lower, spec.title.lower())
            desc_score = 0
            if spec.description:
                desc_score = fuzz.partial_ratio(query_lower, spec.description.lower())

            # Weighted score
            total_score = (code_score * 0.5) + (title_score * 0.3) + (desc_score * 0.2)

            if total_score >= SpecificationService.MATCH_THRESHOLD:
                scored_specs.append((total_score, spec))

        # Sort by score (descending)
        scored_specs.sort(key=lambda x: x[0], reverse=True)

        return [spec for score, spec in scored_specs[:limit]]

    @staticmethod
    def match_specification_code(
        code: str,
        context: Optional[str],
        db: Session
    ) -> Tuple[Optional[SpecificationLibrary], float]:
        """
        Match a specification code to the library

        Args:
            code: Specification code (e.g., "ASTM-C150")
            context: Optional context text
            db: Database session

        Returns:
            Tuple of (matched_spec, confidence_score)
        """
        # Try exact match first
        spec = db.query(SpecificationLibrary).filter(
            SpecificationLibrary.spec_code == code.upper()
        ).first()

        if spec:
            return spec, 100.0

        # Try fuzzy matching
        all_specs = db.query(SpecificationLibrary).all()
        best_match = None
        best_score = 0.0

        code_upper = code.upper()

        for spec in all_specs:
            # Compare codes
            code_score = fuzz.ratio(code_upper, spec.spec_code)

            # If context provided, also match against title/description
            context_score = 0
            if context:
                title_score = fuzz.partial_ratio(context.lower(), spec.title.lower())
                desc_score = 0
                if spec.description:
                    desc_score = fuzz.partial_ratio(context.lower(), spec.description.lower())
                context_score = max(title_score, desc_score)

            # Weighted score (code is more important)
            if context:
                total_score = (code_score * 0.7) + (context_score * 0.3)
            else:
                total_score = code_score

            if total_score > best_score:
                best_score = total_score
                best_match = spec

        if best_score >= SpecificationService.MATCH_THRESHOLD:
            return best_match, best_score

        return None, 0.0

    @staticmethod
    def link_specification_to_project(
        project_id: UUID,
        extracted_code: str,
        context: Optional[str],
        source_page: Optional[int],
        db: Session
    ) -> ProjectSpecification:
        """
        Link a specification to a project

        Args:
            project_id: Project UUID
            extracted_code: Code extracted from document
            context: Surrounding text context
            source_page: Page number
            db: Database session

        Returns:
            Created ProjectSpecification
        """
        # Try to match to library
        matched_spec, confidence = SpecificationService.match_specification_code(
            extracted_code, context, db
        )

        # Create project specification
        project_spec = ProjectSpecification(
            project_id=project_id,
            specification_id=matched_spec.id if matched_spec else None,
            extracted_code=extracted_code,
            context=context,
            source_page=source_page,
            confidence_score=confidence
        )

        db.add(project_spec)
        db.commit()
        db.refresh(project_spec)

        return project_spec

    @staticmethod
    def get_confidence_level(score: float) -> str:
        """Get confidence level string from score"""
        if score >= SpecificationService.HIGH_CONFIDENCE:
            return "high"
        elif score >= SpecificationService.MEDIUM_CONFIDENCE:
            return "medium"
        else:
            return "low"

    @staticmethod
    def bulk_match_specifications(
        codes: List[str],
        db: Session
    ) -> List[dict]:
        """
        Match multiple specification codes at once

        Args:
            codes: List of specification codes
            db: Database session

        Returns:
            List of match results
        """
        results = []

        for code in codes:
            matched_spec, confidence = SpecificationService.match_specification_code(
                code, None, db
            )

            result = {
                "input_code": code,
                "matched": matched_spec is not None,
                "confidence": confidence,
                "confidence_level": SpecificationService.get_confidence_level(confidence)
            }

            if matched_spec:
                result.update({
                    "spec_id": str(matched_spec.id),
                    "spec_code": matched_spec.spec_code,
                    "title": matched_spec.title,
                    "source": matched_spec.source
                })

            results.append(result)

        return results

    @staticmethod
    def get_project_specifications(
        project_id: UUID,
        verified_only: bool,
        db: Session
    ) -> List[ProjectSpecification]:
        """
        Get all specifications linked to a project

        Args:
            project_id: Project UUID
            verified_only: Only return verified specs
            db: Database session

        Returns:
            List of project specifications
        """
        query = db.query(ProjectSpecification).filter(
            ProjectSpecification.project_id == project_id
        )

        if verified_only:
            query = query.filter(ProjectSpecification.is_verified == "verified")

        return query.order_by(ProjectSpecification.source_page).all()

    @staticmethod
    def verify_project_specification(
        project_spec_id: UUID,
        is_verified: str,
        notes: Optional[str],
        db: Session
    ) -> ProjectSpecification:
        """
        Verify or reject a project specification

        Args:
            project_spec_id: ProjectSpecification UUID
            is_verified: "verified", "rejected", or "pending"
            notes: Optional notes
            db: Database session

        Returns:
            Updated ProjectSpecification
        """
        project_spec = db.query(ProjectSpecification).filter(
            ProjectSpecification.id == project_spec_id
        ).first()

        if not project_spec:
            raise ValueError("Project specification not found")

        project_spec.is_verified = is_verified
        if notes:
            project_spec.notes = notes

        db.commit()
        db.refresh(project_spec)

        return project_spec
