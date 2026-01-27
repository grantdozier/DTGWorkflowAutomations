"""
Seed STINE Materials from Quote 684107

Populates the materials table with all 47 materials from STINE's quote.
"""

import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.company import Company
from app.models.material import Material


def seed_stine_materials():
    """Seed all STINE materials from Quote 684107"""
    db = SessionLocal()

    try:
        # Get STINE company (updated name)
        company = db.query(Company).filter(
            Company.name.like("%Stine%")
        ).first()

        if not company:
            print("[ERROR] STINE company not found. Run seed_stine_company.py first.")
            return False

        print(f"[OK] Found STINE company: {company.id}")

        # Check if materials already exist
        existing_count = db.query(Material).filter(
            Material.company_id == company.id
        ).count()

        if existing_count > 0:
            print(f"[WARNING] {existing_count} materials already exist for STINE")
            response = input("Delete and re-seed? (yes/no): ")
            if response.lower() == 'yes':
                db.query(Material).filter(
                    Material.company_id == company.id
                ).delete()
                db.commit()
                print("[OK] Deleted existing materials")
            else:
                print("[SKIP] Keeping existing materials")
                return True

        # Materials from Quote 684107
        materials_data = [
            # Foundation
            {"code": "71579", "desc": "Ace 18# X 1050 ft. L White Twisted Nylon Twine", "price": 13.43, "unit": "ea", "category": "Foundation"},
            {"code": "23142P", "desc": "Pine #2 (2x12-14 Nominal)", "price": 11.83, "unit": "ea", "category": "Foundation"},
            {"code": "26142P", "desc": "Pine #2 (2x6-14 Nominal) Actual: 1.5\"x5.5\"x14'", "price": 5.25, "unit": "ea", "category": "Foundation"},
            {"code": "2336PS", "desc": "Stakes Pine 2x3-36 (25/BDL)", "price": 2.84, "unit": "EA", "category": "Foundation"},
            {"code": "2324PS", "desc": "Stakes Pine 2x3-24 (25/BDL)", "price": 1.43, "unit": "EA", "category": "Foundation"},
            {"code": "14162P", "desc": "Pine #2 (1x4-16 Nominal)", "price": 6.25, "unit": "ea", "category": "Foundation"},
            {"code": "12R", "desc": "Rebar No4 1/2\"x20'", "price": 7.50, "unit": "ea", "category": "Foundation"},
            {"code": "00447", "desc": "Bar Ties 6\" 1000/PK", "price": 22.99, "unit": "ea", "category": "Foundation"},
            {"code": "47889", "desc": "Tape Duct Pro 1.88\"x55Yd", "price": 5.46, "unit": "ea", "category": "Foundation"},
            {"code": "32V", "desc": "Visqueen Clear 6Mil 32'x100'", "price": 118.99, "unit": "RL", "category": "Foundation"},
            {"code": "8X2010M", "desc": "Mesh 8'x20' 10Ga Matts", "price": 22.37, "unit": "ea", "category": "Foundation"},
            {"code": "8X206M", "desc": "Mesh 8'x20' 6Ga Matts", "price": 46.50, "unit": "ea", "category": "Foundation"},
            {"code": "5810AB3", "desc": "Anchor Bolt HDG 5/8 10\" 3x3 washer", "price": 1.99, "unit": "ea", "category": "Foundation"},
            {"code": "16DBPAIL", "desc": "Grip-Rite 16D 3 in. Duplex Bright Steel Nail Double Head 30 lb", "price": 72.95, "unit": "ea", "category": "Foundation"},

            # Wall Framing
            {"code": "2414TP", "desc": "Pine #2 PRIME TREATED (2x4-14 Nominal)", "price": 10.16, "unit": "ea", "category": "Walls"},
            {"code": "24142P", "desc": "Pine #2 (2x4-14 Nominal)", "price": 3.73, "unit": "ea", "category": "Walls"},
            {"code": "2614TP", "desc": "Pine #2 PRIME TREATED (2x6-14 Nominal) Actual: 1.5\"x5.5\"x14'", "price": 12.92, "unit": "ea", "category": "Walls"},
            {"code": "2410SPF", "desc": "Stud Spruce Pine Fir (2x4-116-5/8 Nominal) Actual: 1.5x3.5x116.625", "price": 4.61, "unit": "ea", "category": "Walls"},
            {"code": "2412SPF", "desc": "Stud Spruce, Pine, Fir (2x4-140-5/8 Nominal)", "price": 6.53, "unit": "ea", "category": "Walls"},
            {"code": "2610SS", "desc": "Stud Spruce (2x6-116-5/8 Nominal)", "price": 7.75, "unit": "ea", "category": "Walls"},
            {"code": "2612SS", "desc": "Stud Spruce (2x6-140-5/8 Nominal) Actual: 1.5\"x5.5\"x140.625", "price": 10.05, "unit": "ea", "category": "Walls"},
            {"code": "18LB", "desc": "Beam Lam 3-1/8x13-3/4-18'", "price": 223.62, "unit": "ea", "category": "Walls"},
            {"code": "20LB", "desc": "Beam Lam 3-1/8x13-3/4-20'", "price": 248.46, "unit": "ea", "category": "Walls"},
            {"code": "22LB", "desc": "Beam Lam 3-1/8x13-3/4-22'", "price": 273.31, "unit": "ea", "category": "Walls"},
            {"code": "23082P", "desc": "Pine #2 (2x12-8 Nominal)", "price": 6.86, "unit": "ea", "category": "Walls"},
            {"code": "23102P", "desc": "Pine #2 (2x12-10 Nominal)", "price": 9.36, "unit": "ea", "category": "Walls"},
            {"code": "26082P", "desc": "Pine #2 (2x6-8 Nominal)", "price": 2.88, "unit": "ea", "category": "Walls"},
            {"code": "26102P", "desc": "Pine #2 (2x6-10 Nominal)", "price": 3.72, "unit": "ea", "category": "Walls"},
            {"code": "26122P", "desc": "Pine #2 (2x6-12 Nominal) Actual: 1.5\"x5.5\"x12'", "price": 4.45, "unit": "ea", "category": "Walls"},
            {"code": "26162P", "desc": "Pine #2 (2x6-16 Nominal) Actual: 1.5\"x5.5\"x16'", "price": 6.24, "unit": "ea", "category": "Walls"},
            {"code": "26182P", "desc": "Pine #2 (2x6-18 Nominal) Actual: 1.5\"x5.5\"x18'", "price": 6.58, "unit": "ea", "category": "Walls"},
            {"code": "26202P", "desc": "Pine #2 (2x6-20 Nominal) Actual: 1.5\"x5.5\"x20'", "price": 7.07, "unit": "ea", "category": "Walls"},
            {"code": "24122P", "desc": "Pine #2 (2x4-12 Nominal)", "price": 3.00, "unit": "ea", "category": "Walls"},

            # Sheathing
            {"code": "48716TS", "desc": "OSB 7/16\" Radiant Barrier (48x96x7/16)", "price": 11.99, "unit": "ea", "category": "Sheathing"},
            {"code": "4812OSB", "desc": "OSB 7/16\" Rated Sheathing (48x96x7/16)", "price": 9.05, "unit": "ea", "category": "Sheathing"},
            {"code": "010086", "desc": "OSB 10' Wind (48x121-1/8x7/16)", "price": 11.99, "unit": "ea", "category": "Sheathing"},

            # Roofing
            {"code": "THWW", "desc": "Roof Tamko Hert Wthrwd .33PU", "price": 36.88, "unit": "BDL", "category": "Roofing"},
            {"code": "THWWHR", "desc": "Roof Tamko H/R WeatherWood (Class 3)", "price": 68.59, "unit": "BDL", "category": "Roofing"},
            {"code": "012373", "desc": "Roof Starter 100lf Coverage OC BRAND", "price": 76.43, "unit": "BDL", "category": "Roofing"},
            {"code": "0376", "desc": "Vent Ridge Shngle Over BlkSlt 4' OR-4N", "price": 11.03, "unit": "ea", "category": "Roofing"},
            {"code": "WESCBZ26", "desc": "Drip Edge 26ga Charcoal Bronze ED261760CBZS-C", "price": 13.43, "unit": "ea", "category": "Roofing"},
            {"code": "G1650RV", "desc": "Flashing Valley Galv 16\"x50'", "price": 68.59, "unit": "RL", "category": "Roofing"},
            {"code": "0716B", "desc": "Simpson Plywood Clip Galv Steel 7/16\" Box/250", "price": 25.90, "unit": "BOX", "category": "Roofing"},
            {"code": "00928", "desc": "Stine ProFelt Plus Synthetic Felt (10sq/roll coverage)", "price": 66.63, "unit": "RL", "category": "Roofing"},

            # Siding
            {"code": "00555", "desc": "Hardie Lap Siding 6 1/4 Smooth", "price": 9.59, "unit": "ea", "category": "Siding"},
            {"code": "00781", "desc": "Hardie Trim 4/4x3.5x12 Smooth", "price": 14.09, "unit": "ea", "category": "Siding"},
            {"code": "00782", "desc": "Hardie Trim 4/4x5.5x12 Smooth", "price": 23.50, "unit": "ea", "category": "Siding"},
            {"code": "00804", "desc": "Hardie Trim 4/4x11.25x12 Smooth", "price": 41.55, "unit": "ea", "category": "Siding"},
            {"code": "012239", "desc": "Hardie Batten Board Trim 4/4x2.5x12 Smooth", "price": 12.47, "unit": "ea", "category": "Siding"},
            {"code": "00886", "desc": "Hardie Panel 4x10 Smooth No Groove", "price": 67.19, "unit": "ea", "category": "Siding"},
            {"code": "00917", "desc": "Hardie Soffit Vented 16x12 Smooth", "price": 32.99, "unit": "ea", "category": "Siding"},
            {"code": "00935", "desc": "Hardie Soffit Non-Vented 16x12 Smooth SOLID", "price": 25.43, "unit": "ea", "category": "Siding"},

            # Insulation
            {"code": "R1315", "desc": "Insul R-13 125.94 SqFt 3-1/2x15", "price": 89.27, "unit": "BAG", "category": "Insulation"},
            {"code": "R3015", "desc": "Insul R-30 58.67 Sq' 9.25x16", "price": 80.63, "unit": "ea", "category": "Insulation"},

            # Drywall
            {"code": "41212GB", "desc": "Gypsum 4'x12'x1/2\" Reg PU -.30 NON-RETURNABLE", "price": 20.41, "unit": "ea", "category": "Drywall"},
            {"code": "4812XP", "desc": "Gypsum 4'X8'X1/2\" Mold/Moist Resistant Purple PU-.30 NON-RETURNABLE", "price": 19.19, "unit": "ea", "category": "Drywall"},

            # Interior Trim
            {"code": "00961", "desc": "Crown Pm MDF 5-1/4\"DBL Rl 16' 514DRCR", "price": 24.95, "unit": "ea", "category": "Trim"},
            {"code": "00957", "desc": "Base Prmd 5-1/4\"MDF#109 16' 514B109", "price": 25.91, "unit": "ea", "category": "Trim"},
            {"code": "00964", "desc": "Qtr Rnd PFJWP 3/4\" (actual 11/16\") 16' QRPR", "price": 4.80, "unit": "ea", "category": "Trim"},
            {"code": "1216PFJRP", "desc": "Duraprime FJ 1x2x16 12FJPR", "price": 6.08, "unit": "ea", "category": "Trim"},
            {"code": "1616MDF", "desc": "1x6-16 Primed MDF 1616MDF", "price": 27.83, "unit": "ea", "category": "Trim"},
            {"code": "00654", "desc": "Casing/Base Colonial FJWP #444 3-1/4\"17' 314C444PR17", "price": 31.67, "unit": "ea", "category": "Trim"},

            # Hardware
            {"code": "500902", "desc": "Simpson ZMax LUS26Z 4.75 in. H X 1.56 in. W 18 speed Galvanized Steel Joist Hanger", "price": 1.90, "unit": "ea", "category": "Hardware"},
            {"code": "500424", "desc": "Simpson 18 Ga. Galvanized Steel Hurricane Tie H2.5A", "price": 0.65, "unit": "ea", "category": "Hardware"},
            {"code": "012224", "desc": "Attic Alum 25x54x10 Adjustable", "price": 303.35, "unit": "ea", "category": "Hardware"},
            {"code": "5038989", "desc": "Kwikset Chelsea Satin Nickel Entry Handleset 1-3/4 in.", "price": 105.59, "unit": "ea", "category": "Hardware"},
            {"code": "5422928", "desc": "Kwikset SmartKey Juno Satin Nickel Entry Lockset KW1 1-3/4 in.", "price": 30.71, "unit": "ea", "category": "Hardware"},
            {"code": "5421920", "desc": "Kwikset SmartKey Satin Nickel Metal Deadbolt", "price": 37.43, "unit": "ea", "category": "Hardware"},
            {"code": "5422860", "desc": "Kwikset Juno Satin Nickel Privacy Lockset 1-3/4 in.", "price": 23.03, "unit": "ea", "category": "Hardware"},
            {"code": "5422746", "desc": "Kwikset Juno Satin Nickel Passage Lockset 1-3/4 in.", "price": 22.07, "unit": "ea", "category": "Hardware"},
            {"code": "5422555", "desc": "Kwikset Juno Satin Nickel Dummy Knob Right or Left Handed", "price": 10.55, "unit": "ea", "category": "Hardware"},
            {"code": "500779", "desc": "Door Stop Spring 3-1/8\" Satin Nickel Prosource", "price": 2.49, "unit": "ea", "category": "Hardware"},
            {"code": "500780", "desc": "Door Stop Hinge Pin SN Prosource", "price": 3.16, "unit": "ea", "category": "Hardware"},

            # Miscellaneous
            {"code": "01020", "desc": "Sealer Sill Foam 1/4\"x3-1/2\"x50'Gran", "price": 5.99, "unit": "RL", "category": "Miscellaneous"},
            {"code": "1005578", "desc": "Adhesive Cons LN901 HvyDuty 10.5o", "price": 3.45, "unit": "ea", "category": "Miscellaneous"},
            {"code": "ZF58", "desc": "Flashing Z 5/8\"", "price": 6.71, "unit": "ea", "category": "Miscellaneous"},
            {"code": "300MS", "desc": "Visqueen Black Mstrstop 1'x300'", "price": 15.15, "unit": "ea", "category": "Miscellaneous"},
            {"code": "012263", "desc": "Tyvek Logo Wrap 10' X 150' TY010150USA", "price": 244.50, "unit": "ea", "category": "Miscellaneous"},
            {"code": "012704", "desc": "Flashing Tape PS 4\"x100' Window Wrap", "price": 28.79, "unit": "RL", "category": "Miscellaneous"},
        ]

        # Insert materials
        materials_created = 0
        for mat in materials_data:
            material = Material(
                company_id=company.id,
                product_code=mat["code"],
                description=mat["desc"],
                unit_price=Decimal(str(mat["price"])),
                unit=mat["unit"],
                category=mat["category"],
                is_active=True
            )
            db.add(material)
            materials_created += 1

        db.commit()

        print(f"\n[OK] Successfully seeded {materials_created} materials for STINE")
        print("\nMaterials by category:")
        for category in ["Foundation", "Walls", "Sheathing", "Roofing", "Siding", "Insulation", "Drywall", "Trim", "Hardware", "Miscellaneous"]:
            count = len([m for m in materials_data if m["category"] == category])
            print(f"  - {category}: {count} items")

        return True

    except Exception as e:
        print(f"[ERROR] Failed to seed materials: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding STINE materials from Quote 684107...")
    print()
    success = seed_stine_materials()
    if success:
        print("\n" + "=" * 60)
        print("MATERIALS SEEDED SUCCESSFULLY")
        print("=" * 60)
        print("\nYou can now:")
        print("  1. View materials via API: GET /api/v1/materials")
        print("  2. Match takeoff items to these materials")
        print("  3. Generate estimates using this pricing")
    else:
        sys.exit(1)
