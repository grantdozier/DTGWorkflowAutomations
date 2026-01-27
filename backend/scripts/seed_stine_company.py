"""
Seed STINE Company Data

This script:
1. Creates STINE company account (stine@gmail.com)
2. Populates material pricing from their quote
3. Sets up labor rates, overhead, and profit margins
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.company import Company, CompanyRates
from app.models.user import User
from app.core.security import get_password_hash
import uuid


def seed_stine_company():
    """Create STINE company and populate rates"""
    db = SessionLocal()

    try:
        # Check if company already exists
        existing_company = db.query(Company).filter(
            Company.name == "STINE Lumber"
        ).first()

        if existing_company:
            print(f"STINE company already exists: {existing_company.id}")
            company = existing_company
        else:
            # Create STINE company
            company = Company(
                id=uuid.uuid4(),
                name="STINE Lumber"
            )
            db.add(company)
            db.commit()
            print(f"Created STINE company: {company.id}")

        # Check if user already exists
        existing_user = db.query(User).filter(
            User.email == "stine@gmail.com"
        ).first()

        if existing_user:
            print(f"STINE user already exists: {existing_user.id}")
        else:
            # Create STINE user
            user = User(
                id=uuid.uuid4(),
                email="stine@gmail.com",
                hashed_password=get_password_hash("password"),
                name="STINE Lumber Admin",
                company_id=company.id,
                role="admin"
            )
            db.add(user)
            db.commit()
            print(f"Created STINE user: stine@gmail.com")

        # Check if rates already exist
        existing_rates = db.query(CompanyRates).filter(
            CompanyRates.company_id == company.id
        ).first()

        if existing_rates:
            print("Rates already exist, updating...")
            rates = existing_rates
        else:
            rates = CompanyRates(
                id=uuid.uuid4(),
                company_id=company.id
            )

        # Material pricing from Quote 684107
        # Organized by category for easy lookup
        rates.labor_rate_json = {
            "carpenter": 45.00,
            "helper": 25.00,
            "foreman": 55.00,
            "skilled_labor": 40.00,
            "general_labor": 30.00,
            # STINE specific - installation labor if they offer it
            "installation_available": False,
            "notes": "STINE provides materials only, no labor"
        }

        rates.equipment_rate_json = {
            "delivery_truck": 150.00,  # per delivery
            "forklift": 75.00,  # per day
            "boom_truck": 200.00,  # per day
            "crane": 350.00,  # per day
            "scaffolding": 50.00,  # per day
            "notes": "Equipment rates for material handling and delivery"
        }

        # Overhead and profit margins (typical for material supplier)
        rates.overhead_json = {
            "base_overhead_percent": 12.0,  # 12% overhead
            "small_order_fee": 150.00,  # Orders under $5,000
            "delivery_fee_per_mile": 2.50,
            "fuel_surcharge_percent": 3.5,
            "insurance_percent": 2.0,
            "notes": "Material supplier overhead structure"
        }

        rates.margin_json = {
            "profit_margin_min": 8.0,  # 8% minimum
            "profit_margin_target": 12.0,  # 12% target
            "profit_margin_max": 18.0,  # 18% for small orders
            "volume_discount_tiers": {
                "5000": 0.0,   # <$5k: no discount
                "25000": 2.0,  # $5k-25k: 2% discount
                "50000": 5.0,  # $25k-50k: 5% discount
                "100000": 8.0  # >$50k: 8% discount
            },
            "notes": "Profit margins with volume pricing"
        }

        # Save rates
        if not existing_rates:
            db.add(rates)

        db.commit()
        print(f"[OK] STINE company rates configured successfully")
        print(f"   Company ID: {company.id}")
        print(f"   Login: stine@gmail.com / password")

        return company.id

    except Exception as e:
        print(f"[ERROR] Error seeding STINE company: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def seed_stine_material_catalog():
    """
    Seed material catalog with prices from Quote 684107

    This creates a reference catalog that can be used for estimation.
    Materials are organized by construction phase/category.
    """
    db = SessionLocal()

    try:
        company = db.query(Company).filter(
            Company.name == "STINE Lumber"
        ).first()

        if not company:
            print("[ERROR] STINE company not found. Run seed_stine_company() first.")
            return

        # Material catalog from Quote 684107
        # Format: {product_code: {description, unit_price, unit, category}}
        materials_catalog = {
            # Foundation
            "71579": {"desc": "Ace 18# X 1050 ft. L White Twisted Nylon Twine", "price": 13.43, "unit": "ea", "category": "Foundation"},
            "23142P": {"desc": "Pine #2 (2x12-14 Nominal)", "price": 11.83, "unit": "ea", "category": "Foundation"},
            "26142P": {"desc": "Pine #2 (2x6-14 Nominal)", "price": 5.25, "unit": "ea", "category": "Foundation"},
            "2336PS": {"desc": "Stakes Pine 2x3-36 (25/BDL)", "price": 2.84, "unit": "EA", "category": "Foundation"},
            "2324PS": {"desc": "Stakes Pine 2x3-24 (25/BDL)", "price": 1.43, "unit": "EA", "category": "Foundation"},
            "14162P": {"desc": "Pine #2 (1x4-16 Nominal)", "price": 6.25, "unit": "ea", "category": "Foundation"},
            "12R": {"desc": "Rebar No4 1/2\"x20'", "price": 7.50, "unit": "ea", "category": "Foundation"},
            "00447": {"desc": "Bar Ties 6\" 1000/PK", "price": 22.99, "unit": "ea", "category": "Foundation"},
            "47889": {"desc": "Tape Duct Pro 1.88\"x55Yd", "price": 5.46, "unit": "ea", "category": "Foundation"},
            "32V": {"desc": "Visqueen Clear 6Mil 32'x100'", "price": 118.99, "unit": "RL", "category": "Foundation"},
            "8X2010M": {"desc": "Mesh 8'x20' 10Ga Matts", "price": 22.37, "unit": "ea", "category": "Foundation"},
            "8X206M": {"desc": "Mesh 8'x20' 6Ga Matts", "price": 46.50, "unit": "ea", "category": "Foundation"},
            "5810AB3": {"desc": "Anchor Bolt HDG 5/8 10\" 3x3 washer", "price": 1.99, "unit": "ea", "category": "Foundation"},
            "16DBPAIL": {"desc": "Grip-Rite 16D 3 in. Duplex Nail 30 lb", "price": 72.95, "unit": "ea", "category": "Foundation"},

            # Wall Framing
            "2414TP": {"desc": "Pine #2 PRIME TREATED (2x4-14 Nominal)", "price": 10.16, "unit": "ea", "category": "Walls"},
            "24142P": {"desc": "Pine #2 (2x4-14 Nominal)", "price": 3.73, "unit": "ea", "category": "Walls"},
            "2614TP": {"desc": "Pine #2 PRIME TREATED (2x6-14 Nominal)", "price": 12.92, "unit": "ea", "category": "Walls"},
            "2410SPF": {"desc": "Stud Spruce Pine Fir (2x4-116-5/8 Nominal)", "price": 4.61, "unit": "ea", "category": "Walls"},
            "2412SPF": {"desc": "Stud Spruce, Pine, Fir (2x4-140-5/8 Nominal)", "price": 6.53, "unit": "ea", "category": "Walls"},
            "2610SS": {"desc": "Stud Spruce (2x6-116-5/8 Nominal)", "price": 7.75, "unit": "ea", "category": "Walls"},
            "2612SS": {"desc": "Stud Spruce (2x6-140-5/8 Nominal)", "price": 10.05, "unit": "ea", "category": "Walls"},
            "18LB": {"desc": "Beam Lam 3-1/8x13-3/4-18'", "price": 223.62, "unit": "ea", "category": "Walls"},
            "20LB": {"desc": "Beam Lam 3-1/8x13-3/4-20'", "price": 248.46, "unit": "ea", "category": "Walls"},
            "22LB": {"desc": "Beam Lam 3-1/8x13-3/4-22'", "price": 273.31, "unit": "ea", "category": "Walls"},
            "48716TS": {"desc": "OSB 7/16\" Radiant Barrier (48x96x7/16)", "price": 11.99, "unit": "ea", "category": "Sheathing"},

            # Roofing
            "THWW": {"desc": "Roof Tamko Hert Wthrwd .33PU", "price": 36.88, "unit": "BDL", "category": "Roofing"},
            "THWWHR": {"desc": "Roof Tamko H/R WeatherWood (Class 3)", "price": 68.59, "unit": "BDL", "category": "Roofing"},
            "012373": {"desc": "Roof Starter 100lf Coverage OC BRAND", "price": 76.43, "unit": "BDL", "category": "Roofing"},
            "0376": {"desc": "Vent Ridge Shngle Over BlkSlt 4' OR-4N", "price": 11.03, "unit": "ea", "category": "Roofing"},
            "WESCBZ26": {"desc": "Drip Edge 26ga Charcoal Bronze", "price": 13.43, "unit": "ea", "category": "Roofing"},

            # Siding
            "00555": {"desc": "Hardie Lap Siding 6 1/4 Smooth", "price": 9.59, "unit": "ea", "category": "Siding"},
            "00781": {"desc": "Hardie Trim 4/4x3.5x12 Smooth", "price": 14.09, "unit": "ea", "category": "Siding"},
            "00782": {"desc": "Hardie Trim 4/4x5.5x12 Smooth", "price": 23.50, "unit": "ea", "category": "Siding"},
            "00804": {"desc": "Hardie Trim 4/4x11.25x12 Smooth", "price": 41.55, "unit": "ea", "category": "Siding"},
            "012239": {"desc": "Hardie Batten Board Trim 4/4x2.5x12 Smooth", "price": 12.47, "unit": "ea", "category": "Siding"},

            # Insulation/Drywall
            "R1315": {"desc": "Insul R-13 125.94 SqFt 3-1/2x15", "price": 89.27, "unit": "BAG", "category": "Insulation"},
            "R3015": {"desc": "Insul R-30 58.67 Sq' 9.25x16", "price": 80.63, "unit": "ea", "category": "Insulation"},
            "41212GB": {"desc": "Gypsum 4'x12'x1/2\" Reg", "price": 20.41, "unit": "ea", "category": "Drywall"},
            "4812XP": {"desc": "Gypsum 4'X8'X1/2\" Mold/Moist Resistant Purple", "price": 19.19, "unit": "ea", "category": "Drywall"},

            # Interior Trim
            "00961": {"desc": "Crown Primed MDF 5-1/4\" DBL RL 16'", "price": 24.95, "unit": "ea", "category": "Trim"},
            "00957": {"desc": "Base Primed 5-1/4\" MDF#109 16'", "price": 25.91, "unit": "ea", "category": "Trim"},
            "00964": {"desc": "Qtr Rnd PFJWP 3/4\" 16'", "price": 4.80, "unit": "ea", "category": "Trim"},

            # Hardware
            "500902": {"desc": "Simpson ZMax LUS26Z Joist Hanger", "price": 1.90, "unit": "ea", "category": "Hardware"},
            "500424": {"desc": "Simpson 18 Ga. Hurricane Tie H2.5A", "price": 0.65, "unit": "ea", "category": "Hardware"},
            "5038989": {"desc": "Kwikset Chelsea Entry Handleset", "price": 105.59, "unit": "ea", "category": "Hardware"},
            "5422928": {"desc": "Kwikset SmartKey Juno Entry Lockset", "price": 30.71, "unit": "ea", "category": "Hardware"},
            "5421920": {"desc": "Kwikset SmartKey Deadbolt", "price": 37.43, "unit": "ea", "category": "Hardware"},
        }

        print(f"[OK] Material catalog prepared with {len(materials_catalog)} items")
        print(f"   Categories: Foundation, Walls, Roofing, Siding, Insulation, Trim, Hardware")
        print(f"   This data can be imported into your material pricing system")

        # Store in company rates as material_catalog
        rates = db.query(CompanyRates).filter(
            CompanyRates.company_id == company.id
        ).first()

        if rates:
            # Store material catalog in a separate JSON field
            # You may want to create a dedicated materials table instead
            print(f"   Material catalog data available for import")
            print(f"   Consider creating a 'materials' table for better querying")

        return materials_catalog

    except Exception as e:
        print(f"[ERROR] Error seeding material catalog: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding STINE company data...")
    print()

    # Seed company and user
    company_id = seed_stine_company()
    print()

    # Seed material catalog
    materials = seed_stine_material_catalog()
    print()

    print("=" * 60)
    print("STINE DATA SEEDED SUCCESSFULLY")
    print("=" * 60)
    print()
    print("Login credentials:")
    print("  Email: stine@gmail.com")
    print("  Password: password")
    print()
    print("Next steps:")
    print("  1. Login to the system with STINE account")
    print("  2. Create a project for 'Lot 195'")
    print("  3. Upload the plan PDF")
    print("  4. Parse the plan to extract takeoff items")
    print("  5. System will match items to STINE's pricing")
    print("  6. Generate estimate/quote")
    print()
    print("Note: This is a materials-only quote system")
    print("Labor rates are placeholder - STINE provides materials only")
