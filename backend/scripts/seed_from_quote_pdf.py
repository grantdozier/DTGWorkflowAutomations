"""
Seed Stine materials from Quote 684107 PDF with EXACT data.
Parses the actual quote PDF to get accurate product codes, descriptions, and prices.
"""
import sys
import re
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

import pdfplumber
from app.core.database import SessionLocal
from app.models.user import User
from app.models.material import Material


def parse_quote_pdf(pdf_path: str) -> list:
    """Parse the Stine quote PDF and extract all materials"""
    materials = []
    current_category = "Miscellaneous"
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            
            lines = text.split('\n')
            
            for line in lines:
                # Detect category headers
                if line.strip() in ['Foundation', '1st Floor Walls', 'Ceiling Joists', 
                                    'Roof', 'Rafters', 'Eaves/soffit', 'Roof Decking',
                                    'Wall Sheathing', 'Exterior Siding', 'Doors', 
                                    'Insulation', 'Drywall', 'Trim', 'Hardware',
                                    'Interior Doors', 'Exterior Doors', 'Windows']:
                    current_category = line.strip()
                    continue
                
                # Skip headers and footers
                if 'STINE' in line or 'Quote' in line or 'Page' in line:
                    continue
                if 'Subject to' in line or 'Qty/Footage' in line:
                    continue
                if 'End of' in line:
                    continue
                
                # Parse material lines - format: QTY UOM CODE DESCRIPTION PRICE UOM TOTAL
                # Example: 16 ea 23142P Pine #2 (2x12-14 Nominal) 11.83 ea 189.28
                
                # Try to match the pattern
                match = re.match(
                    r'^(\d+)\s+(ea|EA|RL|BDL|BOX|LF|SF)\s+(\S+)\s+(.+?)\s+(\d+\.?\d*)\s+(ea|EA|RL|BDL|BOX|LF|SF)\s+[\d,]+\.?\d*$',
                    line.strip()
                )
                
                if match:
                    qty, unit1, code, desc, price, unit2 = match.groups()
                    materials.append({
                        'product_code': code,
                        'description': desc.strip(),
                        'unit_price': Decimal(price),
                        'unit': unit2.upper(),
                        'category': current_category
                    })
                    continue
                
                # Alternative pattern for multi-line descriptions
                # Try simpler pattern: starts with number, has product code
                simple_match = re.match(
                    r'^(\d+)\s+(ea|EA|RL|BDL|BOX|LF|SF)\s+(\S+)\s+(.+)',
                    line.strip()
                )
                
                if simple_match:
                    qty, unit, code, rest = simple_match.groups()
                    # Try to extract price from the rest
                    price_match = re.search(r'(\d+\.?\d*)\s+(ea|EA|RL|BDL|BOX|LF|SF)\s+[\d,]+\.?\d*$', rest)
                    if price_match:
                        price = price_match.group(1)
                        desc = rest[:price_match.start()].strip()
                        materials.append({
                            'product_code': code,
                            'description': desc,
                            'unit_price': Decimal(price),
                            'unit': unit.upper(),
                            'category': current_category
                        })
    
    return materials


def dedupe_materials(materials: list) -> list:
    """Deduplicate materials by product code, keeping the first occurrence"""
    seen = {}
    for mat in materials:
        code = mat['product_code']
        if code not in seen:
            seen[code] = mat
    return list(seen.values())


def seed_materials(materials: list, company_id: str):
    """Seed materials into database"""
    db = SessionLocal()
    try:
        # Clear existing materials for this company
        deleted = db.query(Material).filter(Material.company_id == company_id).delete()
        print(f"Deleted {deleted} existing materials")
        
        # Add new materials
        for mat in materials:
            material = Material(
                company_id=company_id,
                product_code=mat['product_code'],
                description=mat['description'],
                category=mat['category'],
                unit_price=mat['unit_price'],
                unit=mat['unit'],
                is_active=True
            )
            db.add(material)
        
        db.commit()
        print(f"Seeded {len(materials)} materials")
        
    finally:
        db.close()


def main():
    print("=" * 60)
    print("PARSING STINE QUOTE 684107 FOR ACCURATE MATERIAL DATA")
    print("=" * 60)
    
    pdf_path = Path(__file__).parent.parent / "uploads" / "stine" / "Quote 684107.pdf"
    
    if not pdf_path.exists():
        print(f"ERROR: Quote PDF not found at {pdf_path}")
        return
    
    print(f"\nParsing: {pdf_path}")
    materials = parse_quote_pdf(str(pdf_path))
    print(f"Found {len(materials)} material entries")
    
    # Deduplicate
    materials = dedupe_materials(materials)
    print(f"After deduplication: {len(materials)} unique materials")
    
    # Show sample
    print("\nSample materials:")
    for mat in materials[:15]:
        print(f"  {mat['product_code']}: {mat['description'][:50]} - ${mat['unit_price']} {mat['unit']} [{mat['category']}]")
    
    # Get Stine company
    db = SessionLocal()
    try:
        stine_user = db.query(User).filter(User.email == "stine@gmail.com").first()
        if not stine_user:
            print("\nERROR: Stine user not found")
            return
        
        print(f"\nSeeding materials for company: {stine_user.company_id}")
        seed_materials(materials, str(stine_user.company_id))
        
        # Show category breakdown
        categories = {}
        for mat in materials:
            cat = mat['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nMaterials by category:")
        for cat, count in sorted(categories.items()):
            print(f"  {cat}: {count}")
        
    finally:
        db.close()
    
    print("\n" + "=" * 60)
    print("DONE - Materials seeded from actual quote data")
    print("=" * 60)


if __name__ == "__main__":
    main()
