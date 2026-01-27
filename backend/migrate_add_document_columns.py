"""
Migration script to add file_name and is_parsed columns to project_documents table.
Run this script once to update the database schema.
"""
import os
import sys

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine

def migrate():
    """Add file_name and is_parsed columns to project_documents table"""
    
    with engine.connect() as conn:
        # Check if columns exist first
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'project_documents' 
            AND column_name IN ('file_name', 'is_parsed')
        """))
        existing_columns = [row[0] for row in result.fetchall()]
        
        # Add file_name column if it doesn't exist
        if 'file_name' not in existing_columns:
            print("Adding file_name column...")
            conn.execute(text("ALTER TABLE project_documents ADD COLUMN file_name VARCHAR"))
            print("  ✓ file_name column added")
        else:
            print("  - file_name column already exists")
        
        # Add is_parsed column if it doesn't exist
        if 'is_parsed' not in existing_columns:
            print("Adding is_parsed column...")
            conn.execute(text("ALTER TABLE project_documents ADD COLUMN is_parsed VARCHAR DEFAULT 'false'"))
            print("  ✓ is_parsed column added")
        else:
            print("  - is_parsed column already exists")
        
        conn.commit()
        print("\nMigration complete!")

if __name__ == "__main__":
    print("Running migration: Add file_name and is_parsed to project_documents")
    print("=" * 60)
    migrate()
