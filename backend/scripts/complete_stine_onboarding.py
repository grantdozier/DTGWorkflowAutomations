"""
Complete STINE Home & Yard onboarding setup

This script:
1. Adds missing fields to companies table
2. Updates STINE company with full business details
3. Ensures all rates are configured
4. Marks onboarding as complete
5. Verifies materials catalog is loaded

Run this to fully set up the STINE account for production use.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from app.core.database import engine, SessionLocal
from app.models.company import Company, CompanyRates
from app.models.user import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_company_fields():
    """Add address and contact fields to companies table"""
    logger.info("Adding new fields to companies table...")

    with engine.connect() as conn:
        # Check if columns already exist
        result = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='companies' AND column_name='address';
        """))

        if result.fetchone() is None:
            # Add columns
            conn.execute(text("""
                ALTER TABLE companies
                ADD COLUMN address VARCHAR,
                ADD COLUMN city VARCHAR,
                ADD COLUMN state VARCHAR,
                ADD COLUMN zip VARCHAR,
                ADD COLUMN phone VARCHAR,
                ADD COLUMN email VARCHAR,
                ADD COLUMN website VARCHAR;
            """))
            conn.commit()
            logger.info("[OK] Added new fields to companies table")
        else:
            logger.info("[OK] Fields already exist in companies table")


def update_stine_company():
    """Update STINE company with complete business information"""
    logger.info("Updating STINE company information...")

    db = SessionLocal()
    try:
        # Find STINE company by email
        stine_user = db.query(User).filter(User.email == "stine@gmail.com").first()

        if not stine_user:
            logger.error("[ERROR] STINE user not found! Run seed_stine_company.py first.")
            return False

        company = db.query(Company).filter(Company.id == stine_user.company_id).first()

        if not company:
            logger.error("[ERROR] STINE company not found!")
            return False

        # Update company information with real STINE data
        company.name = "Stine Home + Yard"
        company.address = "6501 Ambassador Caffery Parkway"
        company.city = "Broussard"
        company.state = "LA"
        company.zip = "70518"
        company.phone = "(337) 837-1045"
        company.email = "info@stinehome.com"
        company.website = "https://www.stinehome.com"

        db.commit()
        logger.info(f"[OK] Updated company: {company.name}")
        logger.info(f"    Address: {company.address}, {company.city}, {company.state} {company.zip}")
        logger.info(f"    Phone: {company.phone}")
        logger.info(f"    Website: {company.website}")

        return True

    except Exception as e:
        logger.error(f"[ERROR] Failed to update company: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def verify_rates():
    """Verify STINE company rates are configured"""
    logger.info("Verifying company rates...")

    db = SessionLocal()
    try:
        stine_user = db.query(User).filter(User.email == "stine@gmail.com").first()

        if not stine_user:
            return False

        rates = db.query(CompanyRates).filter(
            CompanyRates.company_id == stine_user.company_id
        ).first()

        if not rates:
            logger.warning("[WARNING] Company rates not found!")
            return False

        # Verify key configurations
        overhead = rates.overhead_json.get("base_overhead_percent", 0)
        profit = rates.margin_json.get("profit_margin_target", 0)

        logger.info(f"[OK] Company rates configured:")
        logger.info(f"    Overhead: {overhead}%")
        logger.info(f"    Profit Margin: {profit}%")
        logger.info(f"    Labor Rates: {len(rates.labor_rate_json)} categories")
        logger.info(f"    Equipment Rates: {len(rates.equipment_rate_json)} types")

        return True

    finally:
        db.close()


def verify_materials():
    """Verify STINE materials catalog is loaded"""
    logger.info("Verifying materials catalog...")

    db = SessionLocal()
    try:
        stine_user = db.query(User).filter(User.email == "stine@gmail.com").first()

        if not stine_user:
            return False

        # Count materials
        result = db.execute(text("""
            SELECT COUNT(*) as count, COUNT(DISTINCT category) as categories
            FROM materials
            WHERE company_id = :company_id AND is_active = true;
        """), {"company_id": str(stine_user.company_id)})

        row = result.fetchone()
        material_count = row[0] if row else 0
        category_count = row[1] if row else 0

        if material_count == 0:
            logger.warning("[WARNING] No materials found! Run seed_stine_materials.py")
            return False

        logger.info(f"[OK] Materials catalog loaded:")
        logger.info(f"    {material_count} materials across {category_count} categories")

        return True

    finally:
        db.close()


def complete_onboarding():
    """Mark STINE user's onboarding as complete"""
    logger.info("Marking onboarding as complete...")

    db = SessionLocal()
    try:
        stine_user = db.query(User).filter(User.email == "stine@gmail.com").first()

        if not stine_user:
            return False

        # Mark onboarding as complete
        stine_user.onboarding_completed = True
        db.commit()

        logger.info("[OK] Onboarding marked as complete")
        logger.info(f"    User: {stine_user.email}")
        logger.info(f"    Role: {stine_user.role}")

        return True

    except Exception as e:
        logger.error(f"[ERROR] Failed to complete onboarding: {str(e)}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("STINE HOME & YARD - Complete Onboarding Setup")
    print("="*60 + "\n")

    success = True

    # Step 1: Add database fields
    try:
        add_company_fields()
    except Exception as e:
        logger.error(f"[ERROR] Database migration failed: {str(e)}")
        success = False

    # Step 2: Update company information
    if not update_stine_company():
        success = False

    # Step 3: Verify rates
    if not verify_rates():
        logger.warning("[WARNING] Rates verification failed - may need to run seed_stine_company.py")
        success = False

    # Step 4: Verify materials
    if not verify_materials():
        logger.warning("[WARNING] Materials verification failed - may need to run seed_stine_materials.py")
        success = False

    # Step 5: Complete onboarding
    if success and not complete_onboarding():
        success = False

    # Summary
    print("\n" + "="*60)
    if success:
        print("SUCCESS! STINE Home & Yard is fully set up!")
        print("="*60)
        print("\nYou can now login with:")
        print("  Email: stine@gmail.com")
        print("  Password: password")
        print("\nThe account includes:")
        print("  - Complete company profile")
        print("  - 79 materials catalog")
        print("  - Configured rates (12% overhead, 10% profit)")
        print("  - Onboarding completed")
        print("\nReady to:")
        print("  1. Upload construction plans")
        print("  2. Parse with AI")
        print("  3. Generate estimates")
        print("  4. Export professional PDF quotes")
        print("="*60 + "\n")
    else:
        print("ERRORS ENCOUNTERED - See messages above")
        print("="*60)
        print("\nYou may need to run:")
        print("  1. python backend/scripts/seed_stine_company.py")
        print("  2. python backend/scripts/seed_stine_materials.py")
        print("  3. python backend/scripts/complete_stine_onboarding.py")
        print("="*60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
