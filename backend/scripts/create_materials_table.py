"""
Create materials table manually

Since Alembic isn't configured yet, this script directly creates the materials table.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import engine
from app.models.material import Material

def create_materials_table():
    """Create materials table"""
    try:
        # Create table
        Material.__table__.create(engine, checkfirst=True)
        print("[OK] Materials table created successfully")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create materials table: {e}")
        return False

if __name__ == "__main__":
    print("Creating materials table...")
    success = create_materials_table()
    if success:
        print("\nTable structure:")
        print("- id: UUID (primary key)")
        print("- company_id: UUID (foreign key to companies)")
        print("- product_code: String (vendor SKU)")
        print("- description: Text")
        print("- category: String (Foundation, Walls, etc.)")
        print("- unit_price: Numeric(15, 2)")
        print("- unit: String (ea, BDL, RL, etc.)")
        print("- manufacturer: String")
        print("- specifications: Text")
        print("- notes: Text")
        print("- is_active: Boolean")
        print("- lead_time_days: Numeric(5, 1)")
        print("- minimum_order: Numeric(10, 2)")
        print("- created_at: DateTime")
        print("- updated_at: DateTime")
        print("\nReady to seed materials!")
    else:
        sys.exit(1)
