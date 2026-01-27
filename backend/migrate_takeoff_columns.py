"""
Migration script to add category, matched_material_id, unit_price, total_price columns to takeoff_items table.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def migrate():
    """Add new columns to takeoff_items table"""
    
    with engine.connect() as conn:
        # Check existing columns
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'takeoff_items'
        """))
        existing_columns = [row[0] for row in result.fetchall()]
        print(f"Existing columns: {existing_columns}")
        
        # Add category column
        if 'category' not in existing_columns:
            print("Adding category column...")
            conn.execute(text("ALTER TABLE takeoff_items ADD COLUMN category VARCHAR"))
            print("  ✓ category column added")
        else:
            print("  - category column already exists")
        
        # Add matched_material_id column
        if 'matched_material_id' not in existing_columns:
            print("Adding matched_material_id column...")
            conn.execute(text("ALTER TABLE takeoff_items ADD COLUMN matched_material_id UUID REFERENCES materials(id)"))
            print("  ✓ matched_material_id column added")
        else:
            print("  - matched_material_id column already exists")
        
        # Add unit_price column
        if 'unit_price' not in existing_columns:
            print("Adding unit_price column...")
            conn.execute(text("ALTER TABLE takeoff_items ADD COLUMN unit_price NUMERIC(15,2)"))
            print("  ✓ unit_price column added")
        else:
            print("  - unit_price column already exists")
        
        # Add total_price column
        if 'total_price' not in existing_columns:
            print("Adding total_price column...")
            conn.execute(text("ALTER TABLE takeoff_items ADD COLUMN total_price NUMERIC(15,2)"))
            print("  ✓ total_price column added")
        else:
            print("  - total_price column already exists")
        
        conn.commit()
        print("\nMigration complete!")

if __name__ == "__main__":
    print("Running migration: Add columns to takeoff_items")
    print("=" * 60)
    migrate()
