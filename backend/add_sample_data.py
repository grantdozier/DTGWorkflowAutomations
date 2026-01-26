"""
Comprehensive Sample Data Script for DTG Workflow Automations
=============================================================
Scenario: Dozier Lumber Yard is building a custom 2,400 SF single-family home
Project: "Smith Residence - Custom Home Build"

This script populates:
1. Company Settings (labor rates, equipment rates, overhead/margins)
2. Internal Equipment (company-owned tools/equipment)
3. Vendors (material suppliers, subcontractors)
4. Project with description
5. Project Documents (REAL PDF files created on disk)
6. Takeoff Items (quantities from plans)
7. Bid Items linked to project
8. Specifications
9. Quotes from vendors
10. Estimate with full cost breakdown

Run from backend directory: .\\venv\\Scripts\\python.exe add_sample_data.py
"""
import sys
sys.path.insert(0, '.')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import (
    User, Company, CompanyRates, Project, ProjectDocument, 
    BidItem, ProjectBidItem, TakeoffItem, Quote, Estimate,
    InternalEquipment, Vendor, SpecificationLibrary, ProjectSpecification,
    BidItemDiscrepancy
)
from app.core.config import settings
from decimal import Decimal
from datetime import datetime, date, timedelta
import uuid
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Connect to database
engine = create_engine(settings.DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 60)
print("DTG Workflow Automations - Sample Data Generator")
print("Scenario: Dozier Lumber Yard - Smith Residence Custom Home")
print("=" * 60)

# ============================================================
# 1. GET USER AND COMPANY
# ============================================================
user = db.query(User).first()
if not user:
    print("ERROR: No user found. Please register a user first.")
    db.close()
    exit(1)

company = db.query(Company).filter(Company.id == user.company_id).first()
print(f"\n✓ Found user: {user.name} ({user.email})")
print(f"✓ Company: {company.name}")

# ============================================================
# 2. COMPANY RATES (Labor, Equipment, Overhead, Margins)
# ============================================================
print("\n" + "-" * 40)
print("Setting up Company Rates...")

# Delete existing rates for clean slate
db.query(CompanyRates).filter(CompanyRates.company_id == company.id).delete()

labor_rates = {
    "Foreman": 45.00,
    "Lead Carpenter": 38.00,
    "Carpenter": 32.00,
    "Apprentice": 22.00,
    "Laborer": 18.00,
    "Electrician": 55.00,
    "Plumber": 52.00,
    "HVAC Tech": 48.00,
}

equipment_rates = {
    "Skid Steer": {"hourly": 45.00, "daily": 280.00},
    "Excavator (Mini)": {"hourly": 65.00, "daily": 400.00},
    "Boom Lift": {"hourly": 35.00, "daily": 225.00},
    "Concrete Mixer": {"hourly": 15.00, "daily": 95.00},
    "Generator": {"hourly": 12.00, "daily": 75.00},
    "Compressor": {"hourly": 10.00, "daily": 60.00},
    "Nail Gun Kit": {"hourly": 5.00, "daily": 35.00},
    "Table Saw": {"hourly": 8.00, "daily": 50.00},
}

overhead_margins = {
    "overhead_percentage": 12.0,
    "profit_margin_percentage": 15.0,
    "bond_percentage": 2.5,
    "contingency_percentage": 5.0,
}

company_rates = CompanyRates(
    id=uuid.uuid4(),
    company_id=company.id,
    labor_rate_json=labor_rates,
    equipment_rate_json=equipment_rates,
    overhead_json={"percentage": overhead_margins["overhead_percentage"]},
    margin_json={
        "profit": overhead_margins["profit_margin_percentage"],
        "bond": overhead_margins["bond_percentage"],
        "contingency": overhead_margins["contingency_percentage"],
    },
)
db.add(company_rates)
print(f"  ✓ Labor rates: {len(labor_rates)} positions")
print(f"  ✓ Equipment rates: {len(equipment_rates)} items")
print(f"  ✓ Overhead: {overhead_margins['overhead_percentage']}%")
print(f"  ✓ Profit margin: {overhead_margins['profit_margin_percentage']}%")

# ============================================================
# 3. INTERNAL EQUIPMENT (Company-owned)
# ============================================================
print("\n" + "-" * 40)
print("Adding Internal Equipment...")

# Clear existing equipment
db.query(InternalEquipment).filter(InternalEquipment.company_id == company.id).delete()

internal_equipment = [
    {"name": "2022 Kubota SVL75-2", "equipment_type": "Skid Steer", "model": "SVL75-2", "serial_number": "KUB-2022-4521", "purchase_price": 65000.00, "hourly_cost": 45.00, "condition": "good"},
    {"name": "2021 Bobcat E35", "equipment_type": "Mini Excavator", "model": "E35", "serial_number": "BOB-2021-8834", "purchase_price": 52000.00, "hourly_cost": 55.00, "condition": "good"},
    {"name": "2020 Ford F-350", "equipment_type": "Truck", "model": "F-350 Super Duty", "serial_number": "1FT8W3BT0LED12345", "purchase_price": 58000.00, "hourly_cost": 25.00, "condition": "good"},
    {"name": "2019 Genie S-45", "equipment_type": "Boom Lift", "model": "S-45", "serial_number": "GEN-2019-2234", "purchase_price": 42000.00, "hourly_cost": 35.00, "condition": "fair"},
    {"name": "DeWalt Table Saw", "equipment_type": "Power Tool", "model": "DWE7491RS", "serial_number": "DW-2023-9912", "purchase_price": 650.00, "hourly_cost": 8.00, "condition": "good"},
    {"name": "Honda Generator EU7000is", "equipment_type": "Generator", "model": "EU7000is", "serial_number": "HON-2022-5567", "purchase_price": 4500.00, "hourly_cost": 12.00, "condition": "good"},
]

for eq in internal_equipment:
    equipment = InternalEquipment(
        id=uuid.uuid4(),
        company_id=company.id,
        name=eq["name"],
        equipment_type=eq["equipment_type"],
        model=eq["model"],
        serial_number=eq["serial_number"],
        purchase_price=Decimal(str(eq["purchase_price"])),
        hourly_cost=Decimal(str(eq["hourly_cost"])),
        condition=eq["condition"],
        is_available=True,
    )
    db.add(equipment)
    print(f"  ✓ {eq['name']} (${eq['hourly_cost']}/hr)")

# ============================================================
# 4. VENDORS (Suppliers, Subcontractors)
# ============================================================
print("\n" + "-" * 40)
print("Adding Vendors...")

# Clear existing vendors
db.query(Vendor).filter(Vendor.company_id == company.id).delete()

vendors_data = [
    # Material Suppliers
    {"name": "Louisiana Lumber Supply", "category": "material_supplier", "contact_name": "Mike Johnson", "email": "mike@lalumber.com", "phone": "225-555-1234", "city": "Baton Rouge", "state": "LA", "rating": 4.8, "is_preferred": True},
    {"name": "Gulf Coast Building Materials", "category": "material_supplier", "contact_name": "Sarah Williams", "email": "sarah@gulfcoastbm.com", "phone": "504-555-2345", "city": "New Orleans", "state": "LA", "rating": 4.5, "is_preferred": False},
    {"name": "Acadian Concrete & Supply", "category": "material_supplier", "contact_name": "Paul Landry", "email": "paul@acadianconcrete.com", "phone": "337-555-3456", "city": "Lafayette", "state": "LA", "rating": 4.7, "is_preferred": True},
    {"name": "Southern Roofing Distributors", "category": "material_supplier", "contact_name": "Tom Davis", "email": "tom@southernroofing.com", "phone": "225-555-4567", "city": "Baton Rouge", "state": "LA", "rating": 4.3, "is_preferred": False},
    
    # Subcontractors
    {"name": "Bayou Electric LLC", "category": "subcontractor", "contact_name": "James Boudreaux", "email": "james@bayouelectric.com", "phone": "225-555-5678", "city": "Baton Rouge", "state": "LA", "rating": 4.9, "is_preferred": True},
    {"name": "Delta Plumbing Services", "category": "subcontractor", "contact_name": "Robert Thibodaux", "email": "robert@deltaplumbing.com", "phone": "225-555-6789", "city": "Baton Rouge", "state": "LA", "rating": 4.6, "is_preferred": True},
    {"name": "Cajun HVAC Solutions", "category": "subcontractor", "contact_name": "Andre Mouton", "email": "andre@cajunhvac.com", "phone": "337-555-7890", "city": "Lafayette", "state": "LA", "rating": 4.4, "is_preferred": False},
    {"name": "Foundation Specialists Inc", "category": "subcontractor", "contact_name": "David Martin", "email": "david@foundationspec.com", "phone": "225-555-8901", "city": "Baton Rouge", "state": "LA", "rating": 4.8, "is_preferred": True},
    
    # Rental Companies
    {"name": "United Rentals", "category": "rental", "contact_name": "Lisa Brown", "email": "lisa.brown@ur.com", "phone": "225-555-9012", "city": "Baton Rouge", "state": "LA", "rating": 4.2, "is_preferred": False},
    {"name": "Sunbelt Rentals", "category": "rental", "contact_name": "Chris Taylor", "email": "ctaylor@sunbeltrentals.com", "phone": "225-555-0123", "city": "Baton Rouge", "state": "LA", "rating": 4.5, "is_preferred": True},
]

vendor_objects = {}
for v in vendors_data:
    vendor = Vendor(
        id=uuid.uuid4(),
        company_id=company.id,
        name=v["name"],
        category=v["category"],
        contact_name=v["contact_name"],
        email=v["email"],
        phone=v["phone"],
        city=v["city"],
        state=v["state"],
        rating=Decimal(str(v["rating"])),
        is_preferred=v["is_preferred"],
        is_active=True,
    )
    db.add(vendor)
    vendor_objects[v["name"]] = vendor
    print(f"  ✓ {v['name']} ({v['category']})")

db.flush()

# ============================================================
# 5. CREATE PROJECT
# ============================================================
print("\n" + "-" * 40)
print("Creating Project...")

# Delete existing sample project if exists
existing_project = db.query(Project).filter(Project.job_number == "2024-001").first()
if existing_project:
    # Clean up related data (order matters due to foreign keys)
    # Delete discrepancies first (references takeoff_items and project_bid_items)
    db.query(BidItemDiscrepancy).filter(BidItemDiscrepancy.project_id == existing_project.id).delete()
    db.query(Quote).filter(Quote.project_id == existing_project.id).delete()
    db.query(Estimate).filter(Estimate.project_id == existing_project.id).delete()
    db.query(TakeoffItem).filter(TakeoffItem.project_id == existing_project.id).delete()
    db.query(ProjectBidItem).filter(ProjectBidItem.project_id == existing_project.id).delete()
    db.query(ProjectSpecification).filter(ProjectSpecification.project_id == existing_project.id).delete()
    db.query(ProjectDocument).filter(ProjectDocument.project_id == existing_project.id).delete()
    db.delete(existing_project)
    db.flush()
    print("  (Cleaned up existing project data)")

project = Project(
    id=uuid.uuid4(),
    company_id=company.id,
    name="Smith Residence - Custom Home Build",
    job_number="2024-001",
    location="1847 Oak Grove Lane, Baton Rouge, LA 70810",
    type="private",
)
db.add(project)
db.flush()
print(f"  ✓ Project: {project.name}")
print(f"  ✓ Job #: {project.job_number}")
print(f"  ✓ Location: {project.location}")

# ============================================================
# 6. PROJECT DOCUMENTS (Real PDF files)
# ============================================================
print("\n" + "-" * 40)
print("Creating Project Documents (Real PDF files)...")

# Setup upload directories (same structure as file_storage.py)
upload_dir = Path(settings.UPLOAD_DIR)
plans_dir = upload_dir / "plans" / str(project.id)
specs_dir = upload_dir / "specs" / str(project.id)
plans_dir.mkdir(parents=True, exist_ok=True)
specs_dir.mkdir(parents=True, exist_ok=True)

def create_sample_pdf(filepath: Path, title: str, content_lines: list):
    """Create a simple PDF with title and content"""
    c = canvas.Canvas(str(filepath), pagesize=letter)
    width, height = letter
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(1*inch, height - 1*inch, title)
    
    # Subtitle
    c.setFont("Helvetica", 14)
    c.drawString(1*inch, height - 1.5*inch, "Smith Residence - Custom Home Build")
    c.drawString(1*inch, height - 1.8*inch, "Job #2024-001")
    c.drawString(1*inch, height - 2.1*inch, "1847 Oak Grove Lane, Baton Rouge, LA 70810")
    
    # Content
    c.setFont("Helvetica", 11)
    y_position = height - 3*inch
    for line in content_lines:
        if y_position < 1*inch:
            c.showPage()
            c.setFont("Helvetica", 11)
            y_position = height - 1*inch
        c.drawString(1*inch, y_position, line)
        y_position -= 0.3*inch
    
    # Footer
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(1*inch, 0.5*inch, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Dozier Lumber Yard | SAMPLE DOCUMENT")
    
    c.save()

documents_data = [
    {
        "doc_type": "plan",
        "filename": "architectural_plans.pdf",
        "title": "Architectural Plans",
        "content": [
            "SHEET INDEX:",
            "A1.0 - Site Plan",
            "A1.1 - Foundation Plan",
            "A2.0 - Floor Plan - First Floor",
            "A2.1 - Floor Plan - Second Floor",
            "A3.0 - Exterior Elevations - Front/Rear",
            "A3.1 - Exterior Elevations - Left/Right",
            "A4.0 - Building Sections",
            "A5.0 - Interior Elevations",
            "",
            "PROJECT SUMMARY:",
            "Total Living Area: 2,400 SF",
            "Bedrooms: 4",
            "Bathrooms: 3",
            "Garage: 2-car attached (480 SF)",
            "Stories: 2",
            "Foundation: Slab on Grade",
            "Roof Pitch: 6/12",
        ]
    },
    {
        "doc_type": "plan",
        "filename": "structural_plans.pdf",
        "title": "Structural Plans",
        "content": [
            "SHEET INDEX:",
            "S1.0 - Foundation Plan",
            "S1.1 - Foundation Details",
            "S2.0 - Framing Plan - First Floor",
            "S2.1 - Framing Plan - Second Floor",
            "S3.0 - Roof Framing Plan",
            "S4.0 - Structural Details",
            "",
            "STRUCTURAL NOTES:",
            "Foundation: 4\" slab on grade with #4 rebar @ 18\" O.C.",
            "Footings: 24\" wide x 12\" deep continuous",
            "Wall Framing: 2x6 exterior, 2x4 interior @ 16\" O.C.",
            "Floor Joists: 2x10 @ 16\" O.C.",
            "Roof Trusses: Engineered wood @ 24\" O.C.",
            "Design Load: 20 PSF live, 10 PSF dead",
        ]
    },
    {
        "doc_type": "plan",
        "filename": "electrical_plans.pdf",
        "title": "Electrical Plans",
        "content": [
            "SHEET INDEX:",
            "E1.0 - Electrical Site Plan",
            "E2.0 - First Floor Electrical Plan",
            "E2.1 - Second Floor Electrical Plan",
            "E3.0 - Panel Schedule",
            "",
            "ELECTRICAL NOTES:",
            "Service: 200A, 120/240V, Single Phase",
            "Main Panel: Square D QO Series",
            "Circuits: 42 spaces",
            "GFCI: All kitchen, bath, garage, exterior",
            "AFCI: All bedrooms per NEC 2023",
            "Smoke/CO Detectors: Interconnected, hardwired",
        ]
    },
    {
        "doc_type": "plan",
        "filename": "plumbing_plans.pdf",
        "title": "Plumbing Plans",
        "content": [
            "SHEET INDEX:",
            "P1.0 - Plumbing Site Plan",
            "P2.0 - First Floor Plumbing Plan",
            "P2.1 - Second Floor Plumbing Plan",
            "P3.0 - Plumbing Riser Diagram",
            "",
            "PLUMBING NOTES:",
            "Water Service: 1\" copper from main",
            "Water Heater: 50 gallon gas tankless",
            "Drain/Waste/Vent: PVC Schedule 40",
            "Fixtures: 3 full baths, kitchen, laundry",
            "Gas Line: 1\" black iron to appliances",
        ]
    },
    {
        "doc_type": "plan",
        "filename": "hvac_plans.pdf",
        "title": "HVAC Plans",
        "content": [
            "SHEET INDEX:",
            "M1.0 - HVAC Equipment Schedule",
            "M2.0 - First Floor HVAC Plan",
            "M2.1 - Second Floor HVAC Plan",
            "M3.0 - Duct Layout Details",
            "",
            "HVAC NOTES:",
            "System: 4-ton split system heat pump",
            "SEER Rating: 16",
            "Ductwork: R-8 insulated flex duct",
            "Thermostat: Programmable smart thermostat",
            "Ventilation: ERV for fresh air",
            "Zoning: 2 zones (upstairs/downstairs)",
        ]
    },
    {
        "doc_type": "spec",
        "filename": "specifications_book.pdf",
        "title": "Project Specifications",
        "content": [
            "DIVISION 03 - CONCRETE",
            "03 30 00 - Cast-in-Place Concrete",
            "  - Concrete: 3000 PSI min, Type I/II cement per ASTM C150",
            "  - Reinforcement: Grade 60 per ASTM A615",
            "",
            "DIVISION 06 - WOOD AND PLASTICS",
            "06 10 00 - Rough Carpentry",
            "  - Lumber: #2 or better SPF, kiln dried",
            "  - Sheathing: APA rated OSB",
            "  - Fasteners: Hot-dip galvanized per code",
            "",
            "DIVISION 07 - THERMAL AND MOISTURE",
            "07 21 00 - Thermal Insulation",
            "  - Walls: R-19 fiberglass batt",
            "  - Attic: R-38 blown cellulose",
            "07 31 00 - Asphalt Shingles",
            "  - 30-year architectural shingles",
            "  - Wind rating: 130 mph per ASTM D3161",
            "",
            "DIVISION 08 - OPENINGS",
            "08 50 00 - Windows",
            "  - Vinyl double-hung, Low-E glass",
            "  - U-factor: 0.30 max",
            "08 10 00 - Doors",
            "  - Exterior: Fiberglass insulated",
            "  - Interior: 6-panel hollow core",
            "",
            "DIVISION 09 - FINISHES",
            "09 29 00 - Gypsum Board",
            "  - 1/2\" regular, 5/8\" Type X at garage",
            "09 91 00 - Painting",
            "  - Interior: 2 coats latex",
            "  - Exterior: 2 coats acrylic latex",
        ]
    },
    {
        "doc_type": "addendum",
        "filename": "addendum_01.pdf",
        "title": "Addendum #1",
        "content": [
            "ADDENDUM NO. 1",
            f"Date: {datetime.now().strftime('%B %d, %Y')}",
            "",
            "This addendum modifies the original contract documents.",
            "",
            "CHANGES:",
            "",
            "1. ELECTRICAL (Sheet E2.0):",
            "   - Add (2) 240V outlets in garage for EV charging",
            "   - Upgrade panel to 225A service",
            "",
            "2. PLUMBING (Sheet P2.1):",
            "   - Add rough-in for future bathroom in bonus room",
            "",
            "3. SPECIFICATIONS:",
            "   - Upgrade windows to triple-pane in master bedroom",
            "   - Change exterior paint color from 'Agreeable Gray' to 'Repose Gray'",
            "",
            "All other terms and conditions remain unchanged.",
        ]
    },
]

documents = []
for doc_data in documents_data:
    # Determine directory based on doc type
    if doc_data["doc_type"] == "plan":
        target_dir = plans_dir
    else:
        target_dir = specs_dir
    
    # Create unique filename
    file_id = uuid.uuid4()
    pdf_filename = f"{file_id}.pdf"
    pdf_path = target_dir / pdf_filename
    
    # Create the actual PDF file
    create_sample_pdf(pdf_path, doc_data["title"], doc_data["content"])
    
    # Calculate relative path (same format as file_storage.py)
    if doc_data["doc_type"] == "plan":
        relative_path = f"plans/{project.id}/{pdf_filename}"
    else:
        relative_path = f"specs/{project.id}/{pdf_filename}"
    
    # Create database record
    project_doc = ProjectDocument(
        id=file_id,
        project_id=project.id,
        doc_type=doc_data["doc_type"],
        file_path=relative_path,
    )
    db.add(project_doc)
    documents.append(doc_data)
    print(f"  ✓ {doc_data['doc_type'].upper()}: {doc_data['filename']} -> {relative_path}")

# ============================================================
# 7. TAKEOFF ITEMS (Quantities from Plans)
# ============================================================
print("\n" + "-" * 40)
print("Adding Takeoff Items...")

takeoff_items_data = [
    # Foundation
    {"label": "Concrete Foundation - Slab on Grade", "qty": 2400, "unit": "SF", "source_page": 3, "notes": "4\" thick with vapor barrier"},
    {"label": "Foundation Footings", "qty": 185, "unit": "LF", "source_page": 3, "notes": "24\" wide x 12\" deep"},
    {"label": "Rebar #4", "qty": 2800, "unit": "LF", "source_page": 4, "notes": "Foundation reinforcement"},
    
    # Framing
    {"label": "2x4 Studs - Wall Framing", "qty": 850, "unit": "EA", "source_page": 8, "notes": "Exterior and interior walls"},
    {"label": "2x6 Studs - Exterior Walls", "qty": 420, "unit": "EA", "source_page": 8, "notes": "Energy code compliance"},
    {"label": "2x10 Floor Joists", "qty": 145, "unit": "EA", "source_page": 9, "notes": "16\" OC"},
    {"label": "2x12 Ridge Beam", "qty": 48, "unit": "LF", "source_page": 10, "notes": "Main roof ridge"},
    {"label": "Engineered Roof Trusses", "qty": 32, "unit": "EA", "source_page": 10, "notes": "24\" OC, 6/12 pitch"},
    {"label": "3/4\" OSB Sheathing - Roof", "qty": 3200, "unit": "SF", "source_page": 10, "notes": ""},
    {"label": "1/2\" OSB Sheathing - Walls", "qty": 4800, "unit": "SF", "source_page": 8, "notes": ""},
    {"label": "3/4\" Plywood Subfloor", "qty": 2400, "unit": "SF", "source_page": 9, "notes": "Tongue and groove"},
    
    # Exterior
    {"label": "Hardie Board Siding", "qty": 2800, "unit": "SF", "source_page": 12, "notes": "Fiber cement"},
    {"label": "Architectural Shingles", "qty": 32, "unit": "SQ", "source_page": 11, "notes": "30-year warranty"},
    {"label": "Exterior Windows - Standard", "qty": 14, "unit": "EA", "source_page": 13, "notes": "Double-hung, vinyl"},
    {"label": "Exterior Windows - Large", "qty": 4, "unit": "EA", "source_page": 13, "notes": "Picture windows"},
    {"label": "Exterior Doors", "qty": 3, "unit": "EA", "source_page": 14, "notes": "Fiberglass, insulated"},
    {"label": "Garage Door - 16x7", "qty": 1, "unit": "EA", "source_page": 14, "notes": "Insulated steel"},
    
    # Interior
    {"label": "Interior Doors - Standard", "qty": 18, "unit": "EA", "source_page": 15, "notes": "6-panel, hollow core"},
    {"label": "Interior Doors - Solid Core", "qty": 4, "unit": "EA", "source_page": 15, "notes": "Bedrooms and bathrooms"},
    {"label": "1/2\" Drywall", "qty": 9600, "unit": "SF", "source_page": 16, "notes": "Walls and ceilings"},
    {"label": "5/8\" Drywall - Garage", "qty": 1200, "unit": "SF", "source_page": 16, "notes": "Fire-rated"},
    {"label": "R-19 Batt Insulation - Walls", "qty": 2400, "unit": "SF", "source_page": 17, "notes": "Exterior walls"},
    {"label": "R-38 Blown Insulation - Attic", "qty": 2400, "unit": "SF", "source_page": 17, "notes": ""},
    
    # MEP Allowances
    {"label": "Electrical Rough-In", "qty": 1, "unit": "LS", "source_page": 20, "notes": "200A service, per plan"},
    {"label": "Plumbing Rough-In", "qty": 1, "unit": "LS", "source_page": 22, "notes": "3 bath, kitchen, laundry"},
    {"label": "HVAC System", "qty": 1, "unit": "LS", "source_page": 24, "notes": "4-ton split system"},
    
    # Finishes
    {"label": "Interior Paint", "qty": 9600, "unit": "SF", "source_page": 26, "notes": "2 coats"},
    {"label": "Exterior Paint", "qty": 2800, "unit": "SF", "source_page": 26, "notes": "Siding and trim"},
    {"label": "Hardwood Flooring", "qty": 1200, "unit": "SF", "source_page": 27, "notes": "Living areas"},
    {"label": "Tile Flooring", "qty": 450, "unit": "SF", "source_page": 27, "notes": "Bathrooms and laundry"},
    {"label": "Carpet", "qty": 750, "unit": "SF", "source_page": 27, "notes": "Bedrooms"},
]

takeoff_objects = {}
for item in takeoff_items_data:
    takeoff = TakeoffItem(
        id=uuid.uuid4(),
        project_id=project.id,
        label=item["label"],
        qty=Decimal(str(item["qty"])),
        unit=item["unit"],
        source_page=item["source_page"],
        notes=item["notes"],
    )
    db.add(takeoff)
    takeoff_objects[item["label"]] = takeoff
    print(f"  ✓ {item['label']}: {item['qty']} {item['unit']}")

db.flush()

# ============================================================
# 8. BID ITEMS (Reference + Project Link)
# ============================================================
print("\n" + "-" * 40)
print("Adding Bid Items...")

bid_items_data = [
    {"code": "01-100", "name": "General Conditions", "unit": "LS", "qty": 1, "price": 8500.00},
    {"code": "02-100", "name": "Site Preparation & Clearing", "unit": "LS", "qty": 1, "price": 3500.00},
    {"code": "03-100", "name": "Concrete Foundation", "unit": "SF", "qty": 2400, "price": 8.50},
    {"code": "03-200", "name": "Foundation Footings", "unit": "LF", "qty": 185, "price": 28.00},
    {"code": "06-100", "name": "Rough Framing - Walls", "unit": "SF", "qty": 4800, "price": 4.25},
    {"code": "06-200", "name": "Rough Framing - Roof", "unit": "SF", "qty": 3200, "price": 5.50},
    {"code": "06-300", "name": "Subfloor Installation", "unit": "SF", "qty": 2400, "price": 3.75},
    {"code": "07-100", "name": "Roofing - Shingles", "unit": "SQ", "qty": 32, "price": 385.00},
    {"code": "07-200", "name": "Siding - Hardie Board", "unit": "SF", "qty": 2800, "price": 6.50},
    {"code": "08-100", "name": "Windows - Standard", "unit": "EA", "qty": 14, "price": 425.00},
    {"code": "08-200", "name": "Windows - Large", "unit": "EA", "qty": 4, "price": 850.00},
    {"code": "08-300", "name": "Exterior Doors", "unit": "EA", "qty": 3, "price": 1200.00},
    {"code": "08-400", "name": "Interior Doors", "unit": "EA", "qty": 22, "price": 185.00},
    {"code": "08-500", "name": "Garage Door", "unit": "EA", "qty": 1, "price": 1850.00},
    {"code": "09-100", "name": "Drywall - Install & Finish", "unit": "SF", "qty": 10800, "price": 2.85},
    {"code": "09-200", "name": "Interior Paint", "unit": "SF", "qty": 9600, "price": 1.25},
    {"code": "09-300", "name": "Exterior Paint", "unit": "SF", "qty": 2800, "price": 1.75},
    {"code": "09-400", "name": "Hardwood Flooring", "unit": "SF", "qty": 1200, "price": 8.50},
    {"code": "09-500", "name": "Tile Flooring", "unit": "SF", "qty": 450, "price": 12.00},
    {"code": "09-600", "name": "Carpet", "unit": "SF", "qty": 750, "price": 4.50},
    {"code": "07-300", "name": "Insulation - Walls", "unit": "SF", "qty": 2400, "price": 1.85},
    {"code": "07-400", "name": "Insulation - Attic", "unit": "SF", "qty": 2400, "price": 1.45},
    {"code": "26-100", "name": "Electrical - Complete", "unit": "LS", "qty": 1, "price": 18500.00},
    {"code": "22-100", "name": "Plumbing - Complete", "unit": "LS", "qty": 1, "price": 16500.00},
    {"code": "23-100", "name": "HVAC - Complete", "unit": "LS", "qty": 1, "price": 14500.00},
]

for item in bid_items_data:
    # Create or get bid item reference
    existing = db.query(BidItem).filter(BidItem.code == item["code"]).first()
    if not existing:
        bid_item = BidItem(
            id=uuid.uuid4(),
            code=item["code"],
            name=item["name"],
            unit=item["unit"],
        )
        db.add(bid_item)
        db.flush()
    else:
        bid_item = existing
    
    # Link to project
    project_bid_item = ProjectBidItem(
        id=uuid.uuid4(),
        project_id=project.id,
        bid_item_id=bid_item.id,
        bid_qty=Decimal(str(item["qty"])),
        bid_unit_price=Decimal(str(item["price"])),
    )
    db.add(project_bid_item)
    total = item["qty"] * item["price"]
    print(f"  ✓ {item['code']} {item['name']}: {item['qty']} {item['unit']} @ ${item['price']:.2f} = ${total:,.2f}")

# ============================================================
# 9. SPECIFICATIONS
# ============================================================
print("\n" + "-" * 40)
print("Adding Specifications...")

specs_data = [
    {"code": "ASTM C150", "context": "Type I/II Portland Cement for foundation concrete"},
    {"code": "ASTM C33", "context": "Concrete aggregates specification"},
    {"code": "ACI 318", "context": "Building Code Requirements for Structural Concrete"},
    {"code": "AWC NDS", "context": "National Design Specification for Wood Construction"},
    {"code": "IRC 2021", "context": "International Residential Code compliance"},
    {"code": "ASTM D3161", "context": "Wind resistance of asphalt shingles"},
    {"code": "ASTM E2112", "context": "Window and door installation"},
    {"code": "ASTM C1396", "context": "Gypsum board (drywall) specification"},
    {"code": "IECC 2021", "context": "International Energy Conservation Code - insulation requirements"},
    {"code": "NEC 2023", "context": "National Electrical Code"},
    {"code": "IPC 2021", "context": "International Plumbing Code"},
    {"code": "IMC 2021", "context": "International Mechanical Code - HVAC"},
]

for spec in specs_data:
    project_spec = ProjectSpecification(
        id=uuid.uuid4(),
        project_id=project.id,
        extracted_code=spec["code"],
        context=spec["context"],
        confidence_score=Decimal("0.92"),
        is_verified="verified",
    )
    db.add(project_spec)
    print(f"  ✓ {spec['code']}: {spec['context'][:50]}...")

# ============================================================
# 10. QUOTES FROM VENDORS (Skipped - DB schema needs migration)
# ============================================================
print("\n" + "-" * 40)
print("Skipping Vendor Quotes (DB schema needs migration for quotes table)...")
print("  Note: Run database migrations to add vendor_id/takeoff_item_id columns")

quotes_data = []  # Skipped for now

# ============================================================
# 11. CREATE ESTIMATE
# ============================================================
print("\n" + "-" * 40)
print("Generating Estimate...")

# Calculate costs from bid items
materials_cost = Decimal("0")
labor_cost = Decimal("0")
equipment_cost = Decimal("0")
subcontractor_cost = Decimal("0")

# Materials (lumber, concrete, roofing, windows, doors, drywall, flooring, insulation, paint)
materials_items = ["03-100", "03-200", "06-100", "06-200", "06-300", "07-100", "07-200", 
                   "08-100", "08-200", "08-300", "08-400", "08-500", "09-100", "09-200", 
                   "09-300", "09-400", "09-500", "09-600", "07-300", "07-400"]

for item in bid_items_data:
    total = Decimal(str(item["qty"])) * Decimal(str(item["price"]))
    if item["code"] in materials_items:
        materials_cost += total * Decimal("0.6")  # 60% materials
        labor_cost += total * Decimal("0.35")     # 35% labor
        equipment_cost += total * Decimal("0.05") # 5% equipment
    elif item["code"] in ["26-100", "22-100", "23-100"]:
        subcontractor_cost += total
    elif item["code"] == "01-100":
        labor_cost += total * Decimal("0.7")
        equipment_cost += total * Decimal("0.3")
    else:
        materials_cost += total * Decimal("0.5")
        labor_cost += total * Decimal("0.4")
        equipment_cost += total * Decimal("0.1")

subtotal = materials_cost + labor_cost + equipment_cost + subcontractor_cost
overhead = subtotal * Decimal("0.12")  # 12%
profit = (subtotal + overhead) * Decimal("0.15")  # 15%
total_cost = subtotal + overhead + profit

estimate = Estimate(
    id=uuid.uuid4(),
    project_id=project.id,
    created_by=user.id,
    materials_cost=materials_cost,
    labor_cost=labor_cost,
    equipment_cost=equipment_cost,
    subcontractor_cost=subcontractor_cost,
    overhead=overhead,
    profit=profit,
    total_cost=total_cost,
    confidence_score=Decimal("87.5"),
    notes="Initial estimate based on plan takeoffs and current vendor quotes. Includes 12% overhead and 15% profit margin.",
)
db.add(estimate)

print(f"\n  ESTIMATE SUMMARY")
print(f"  " + "=" * 40)
print(f"  Materials:      ${materials_cost:>12,.2f}")
print(f"  Labor:          ${labor_cost:>12,.2f}")
print(f"  Equipment:      ${equipment_cost:>12,.2f}")
print(f"  Subcontractors: ${subcontractor_cost:>12,.2f}")
print(f"  " + "-" * 40)
print(f"  Subtotal:       ${subtotal:>12,.2f}")
print(f"  Overhead (12%): ${overhead:>12,.2f}")
print(f"  Profit (15%):   ${profit:>12,.2f}")
print(f"  " + "=" * 40)
print(f"  TOTAL:          ${total_cost:>12,.2f}")

# ============================================================
# 12. ADD A DISCREPANCY FOR DEMO
# ============================================================
print("\n" + "-" * 40)
print("Adding Sample Discrepancy...")

# Find a project bid item to link
sample_pbi = db.query(ProjectBidItem).filter(ProjectBidItem.project_id == project.id).first()
sample_takeoff = db.query(TakeoffItem).filter(TakeoffItem.project_id == project.id).first()

if sample_pbi and sample_takeoff:
    discrepancy = BidItemDiscrepancy(
        id=uuid.uuid4(),
        project_id=project.id,
        project_bid_item_id=sample_pbi.id,
        takeoff_item_id=sample_takeoff.id,
        discrepancy_type="quantity_mismatch",
        severity="medium",
        bid_quantity=Decimal("2400"),
        plan_quantity=Decimal("2450"),
        difference_percentage=Decimal("2.08"),
        description="Foundation slab quantity in bid (2,400 SF) is slightly less than plan takeoff (2,450 SF)",
        recommendation="Verify foundation dimensions with architect. Consider adding 50 SF to bid quantity for safety.",
        status="open",
    )
    db.add(discrepancy)
    print(f"  ✓ Added quantity mismatch discrepancy for review")

# ============================================================
# COMMIT ALL CHANGES
# ============================================================
db.commit()

print("\n" + "=" * 60)
print("✓ SAMPLE DATA GENERATION COMPLETE!")
print("=" * 60)
print(f"""
Summary:
  • Company Rates: Labor ({len(labor_rates)} positions), Equipment ({len(equipment_rates)} items)
  • Internal Equipment: {len(internal_equipment)} items
  • Vendors: {len(vendors_data)} (suppliers, subcontractors, rentals)
  • Project: {project.name} (Job #{project.job_number})
  • Documents: {len(documents)} files
  • Takeoff Items: {len(takeoff_items_data)} line items
  • Bid Items: {len(bid_items_data)} items
  • Specifications: {len(specs_data)} specs
  • Quotes: {len(quotes_data)} vendor quotes
  • Estimate: ${total_cost:,.2f}

Navigate to the app and explore:
  1. Dashboard → Click on "{project.name}"
  2. Check each tab: Overview, Documents, Takeoffs, Specifications, Estimates
  3. Go to Settings to see labor rates, equipment rates, margins
  4. Check Equipment Management and Vendor Management
""")

db.close()
