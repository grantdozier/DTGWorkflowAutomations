# Sample Data Documentation

## Overview

This document describes the sample data generation script and the test data available in the DTG Workflow Automations system.

## Sample Data Script

**Location:** `backend/add_sample_data.py`

**Run Command:**
```bash
cd backend
.\venv\Scripts\python.exe add_sample_data.py
```

## Scenario

**Dozier Lumber Yard** is building a custom 2,400 SF single-family home for a client.

**Project:** Smith Residence - Custom Home Build  
**Job Number:** 2024-001  
**Location:** 1847 Oak Grove Lane, Baton Rouge, LA 70810

---

## Data Generated

### 1. Company Settings

#### Labor Rates (8 positions)
| Position | Hourly Rate |
|----------|-------------|
| Foreman | $45.00 |
| Lead Carpenter | $38.00 |
| Carpenter | $32.00 |
| Apprentice | $22.00 |
| Laborer | $18.00 |
| Electrician | $55.00 |
| Plumber | $52.00 |
| HVAC Tech | $48.00 |

#### Equipment Rates (8 items)
| Equipment | Hourly | Daily |
|-----------|--------|-------|
| Skid Steer | $45.00 | $280.00 |
| Excavator (Mini) | $65.00 | $400.00 |
| Boom Lift | $35.00 | $225.00 |
| Concrete Mixer | $15.00 | $95.00 |
| Generator | $12.00 | $75.00 |
| Compressor | $10.00 | $60.00 |
| Nail Gun Kit | $5.00 | $35.00 |
| Table Saw | $8.00 | $50.00 |

#### Overhead & Margins
- Overhead: 12%
- Profit Margin: 15%
- Bond: 2.5%
- Contingency: 5%

---

### 2. Internal Equipment (6 items)

| Equipment | Type | Model | Hourly Cost | Condition |
|-----------|------|-------|-------------|-----------|
| 2022 Kubota SVL75-2 | Skid Steer | SVL75-2 | $45.00 | Good |
| 2021 Bobcat E35 | Mini Excavator | E35 | $55.00 | Good |
| 2020 Ford F-350 | Truck | F-350 Super Duty | $25.00 | Good |
| 2019 Genie S-45 | Boom Lift | S-45 | $35.00 | Fair |
| DeWalt Table Saw | Power Tool | DWE7491RS | $8.00 | Good |
| Honda Generator EU7000is | Generator | EU7000is | $12.00 | Good |

---

### 3. Vendors (10 total)

#### Material Suppliers (4)
| Vendor | Contact | Phone | City | Rating | Preferred |
|--------|---------|-------|------|--------|-----------|
| Louisiana Lumber Supply | Mike Johnson | 225-555-1234 | Baton Rouge | 4.8 | ✓ |
| Gulf Coast Building Materials | Sarah Williams | 504-555-2345 | New Orleans | 4.5 | |
| Acadian Concrete & Supply | Paul Landry | 337-555-3456 | Lafayette | 4.7 | ✓ |
| Southern Roofing Distributors | Tom Davis | 225-555-4567 | Baton Rouge | 4.3 | |

#### Subcontractors (4)
| Vendor | Contact | Phone | City | Rating | Preferred |
|--------|---------|-------|------|--------|-----------|
| Bayou Electric LLC | James Boudreaux | 225-555-5678 | Baton Rouge | 4.9 | ✓ |
| Delta Plumbing Services | Robert Thibodaux | 225-555-6789 | Baton Rouge | 4.6 | ✓ |
| Cajun HVAC Solutions | Andre Mouton | 337-555-7890 | Lafayette | 4.4 | |
| Foundation Specialists Inc | David Martin | 225-555-8901 | Baton Rouge | 4.8 | ✓ |

#### Rental Companies (2)
| Vendor | Contact | Phone | City | Rating | Preferred |
|--------|---------|-------|------|--------|-----------|
| United Rentals | Lisa Brown | 225-555-9012 | Baton Rouge | 4.2 | |
| Sunbelt Rentals | Chris Taylor | 225-555-0123 | Baton Rouge | 4.5 | ✓ |

---

### 4. Project Documents (7 files)

| Document Type | File Name |
|---------------|-----------|
| Plan | architectural_plans.pdf |
| Plan | structural_plans.pdf |
| Plan | electrical_plans.pdf |
| Plan | plumbing_plans.pdf |
| Plan | hvac_plans.pdf |
| Spec | specifications_book.pdf |
| Addendum | addendum_01.pdf |

**Note:** These are simulated document records. Actual PDF files are not created.

---

### 5. Takeoff Items (31 line items)

#### Foundation
| Item | Quantity | Unit | Notes |
|------|----------|------|-------|
| Concrete Foundation - Slab on Grade | 2,400 | SF | 4" thick with vapor barrier |
| Foundation Footings | 185 | LF | 24" wide x 12" deep |
| Rebar #4 | 2,800 | LF | Foundation reinforcement |

#### Framing
| Item | Quantity | Unit | Notes |
|------|----------|------|-------|
| 2x4 Studs - Wall Framing | 850 | EA | Exterior and interior walls |
| 2x6 Studs - Exterior Walls | 420 | EA | Energy code compliance |
| 2x10 Floor Joists | 145 | EA | 16" OC |
| 2x12 Ridge Beam | 48 | LF | Main roof ridge |
| Engineered Roof Trusses | 32 | EA | 24" OC, 6/12 pitch |
| 3/4" OSB Sheathing - Roof | 3,200 | SF | |
| 1/2" OSB Sheathing - Walls | 4,800 | SF | |
| 3/4" Plywood Subfloor | 2,400 | SF | Tongue and groove |

#### Exterior
| Item | Quantity | Unit | Notes |
|------|----------|------|-------|
| Hardie Board Siding | 2,800 | SF | Fiber cement |
| Architectural Shingles | 32 | SQ | 30-year warranty |
| Exterior Windows - Standard | 14 | EA | Double-hung, vinyl |
| Exterior Windows - Large | 4 | EA | Picture windows |
| Exterior Doors | 3 | EA | Fiberglass, insulated |
| Garage Door - 16x7 | 1 | EA | Insulated steel |

#### Interior
| Item | Quantity | Unit | Notes |
|------|----------|------|-------|
| Interior Doors - Standard | 18 | EA | 6-panel, hollow core |
| Interior Doors - Solid Core | 4 | EA | Bedrooms and bathrooms |
| 1/2" Drywall | 9,600 | SF | Walls and ceilings |
| 5/8" Drywall - Garage | 1,200 | SF | Fire-rated |
| R-19 Batt Insulation - Walls | 2,400 | SF | Exterior walls |
| R-38 Blown Insulation - Attic | 2,400 | SF | |

#### MEP Allowances
| Item | Quantity | Unit | Notes |
|------|----------|------|-------|
| Electrical Rough-In | 1 | LS | 200A service, per plan |
| Plumbing Rough-In | 1 | LS | 3 bath, kitchen, laundry |
| HVAC System | 1 | LS | 4-ton split system |

#### Finishes
| Item | Quantity | Unit | Notes |
|------|----------|------|-------|
| Interior Paint | 9,600 | SF | 2 coats |
| Exterior Paint | 2,800 | SF | Siding and trim |
| Hardwood Flooring | 1,200 | SF | Living areas |
| Tile Flooring | 450 | SF | Bathrooms and laundry |
| Carpet | 750 | SF | Bedrooms |

---

### 6. Bid Items (25 items)

| Code | Description | Qty | Unit | Unit Price | Total |
|------|-------------|-----|------|------------|-------|
| 01-100 | General Conditions | 1 | LS | $8,500.00 | $8,500.00 |
| 02-100 | Site Preparation & Clearing | 1 | LS | $3,500.00 | $3,500.00 |
| 03-100 | Concrete Foundation | 2,400 | SF | $8.50 | $20,400.00 |
| 03-200 | Foundation Footings | 185 | LF | $28.00 | $5,180.00 |
| 06-100 | Rough Framing - Walls | 4,800 | SF | $4.25 | $20,400.00 |
| 06-200 | Rough Framing - Roof | 3,200 | SF | $5.50 | $17,600.00 |
| 06-300 | Subfloor Installation | 2,400 | SF | $3.75 | $9,000.00 |
| 07-100 | Roofing - Shingles | 32 | SQ | $385.00 | $12,320.00 |
| 07-200 | Siding - Hardie Board | 2,800 | SF | $6.50 | $18,200.00 |
| 07-300 | Insulation - Walls | 2,400 | SF | $1.85 | $4,440.00 |
| 07-400 | Insulation - Attic | 2,400 | SF | $1.45 | $3,480.00 |
| 08-100 | Windows - Standard | 14 | EA | $425.00 | $5,950.00 |
| 08-200 | Windows - Large | 4 | EA | $850.00 | $3,400.00 |
| 08-300 | Exterior Doors | 3 | EA | $1,200.00 | $3,600.00 |
| 08-400 | Interior Doors | 22 | EA | $185.00 | $4,070.00 |
| 08-500 | Garage Door | 1 | EA | $1,850.00 | $1,850.00 |
| 09-100 | Drywall - Install & Finish | 10,800 | SF | $2.85 | $30,780.00 |
| 09-200 | Interior Paint | 9,600 | SF | $1.25 | $12,000.00 |
| 09-300 | Exterior Paint | 2,800 | SF | $1.75 | $4,900.00 |
| 09-400 | Hardwood Flooring | 1,200 | SF | $8.50 | $10,200.00 |
| 09-500 | Tile Flooring | 450 | SF | $12.00 | $5,400.00 |
| 09-600 | Carpet | 750 | SF | $4.50 | $3,375.00 |
| 22-100 | Plumbing - Complete | 1 | LS | $16,500.00 | $16,500.00 |
| 23-100 | HVAC - Complete | 1 | LS | $14,500.00 | $14,500.00 |
| 26-100 | Electrical - Complete | 1 | LS | $18,500.00 | $18,500.00 |

---

### 7. Specifications (12 specs)

| Code | Description |
|------|-------------|
| ASTM C150 | Type I/II Portland Cement for foundation concrete |
| ASTM C33 | Concrete aggregates specification |
| ACI 318 | Building Code Requirements for Structural Concrete |
| AWC NDS | National Design Specification for Wood Construction |
| IRC 2021 | International Residential Code compliance |
| ASTM D3161 | Wind resistance of asphalt shingles |
| ASTM E2112 | Window and door installation |
| ASTM C1396 | Gypsum board (drywall) specification |
| IECC 2021 | International Energy Conservation Code - insulation requirements |
| NEC 2023 | National Electrical Code |
| IPC 2021 | International Plumbing Code |
| IMC 2021 | International Mechanical Code - HVAC |

---

### 8. Estimate Summary

| Category | Amount |
|----------|--------|
| Materials | $119,677.00 |
| Labor | $76,140.75 |
| Equipment | $12,727.25 |
| Subcontractors | $49,500.00 |
| **Subtotal** | **$258,045.00** |
| Overhead (12%) | $30,965.40 |
| Profit (15%) | $43,351.56 |
| **TOTAL** | **$332,361.96** |

---

### 9. Sample Discrepancy

A sample discrepancy has been added for demonstration:

- **Type:** Quantity Mismatch
- **Severity:** Medium
- **Issue:** Foundation slab quantity in bid (2,400 SF) is slightly less than plan takeoff (2,450 SF)
- **Recommendation:** Verify foundation dimensions with architect. Consider adding 50 SF to bid quantity for safety.

---

## API Endpoints Added

The following endpoints were added to support the sample data:

### Takeoffs (`/api/v1/projects/{project_id}/takeoffs`)
- `GET` - List all takeoff items for a project
- `POST` - Create a new takeoff item
- `PATCH /{takeoff_id}` - Update a takeoff item
- `DELETE /{takeoff_id}` - Delete a takeoff item

---

## How to Use

1. Start the backend server
2. Register/login to the application
3. Run the sample data script: `.\venv\Scripts\python.exe add_sample_data.py`
4. Refresh the browser
5. Navigate to the "Smith Residence - Custom Home Build" project
6. Explore all tabs: Documents, Takeoffs, Specifications, Estimates, Discrepancies
7. Check Settings for labor rates, equipment rates, and margins
8. Check Equipment Management and Vendor Management

---

## Notes

- The script is idempotent - running it multiple times will recreate the sample project
- Vendor quotes are currently skipped due to database schema migration requirements
- Document files are simulated records (no actual PDFs are created)
