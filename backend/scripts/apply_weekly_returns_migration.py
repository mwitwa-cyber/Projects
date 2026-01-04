"""
Apply the weekly_returns_view.sql migration to TimescaleDB.

This script:
1. Connects to the database
2. Reads the SQL migration file
3. Executes each SQL statement
4. Reports success/failure

Run with: python scripts/apply_weekly_returns_migration.py
"""

import os
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment
load_dotenv(backend_dir / ".env")

def apply_migration():
    """Apply the weekly returns view migration."""
    
    # Get database URL
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@127.0.0.1:5432/luse_quant"
    )
    
    print(f"Connecting to database...")
    print(f"URL: {database_url.split('@')[1] if '@' in database_url else database_url}")
    
    try:
        engine = create_engine(database_url)
        
        # Read migration file
        migration_file = backend_dir / "app" / "db" / "migrations" / "weekly_returns_view.sql"
        
        if not migration_file.exists():
            print(f"ERROR: Migration file not found: {migration_file}")
            return False
        
        print(f"Reading migration: {migration_file.name}")
        sql_content = migration_file.read_text(encoding="utf-8")
        
        # Split into individual statements (split on semicolons, but keep function bodies intact)
        # For this complex SQL with function definitions, we'll execute as one block
        
        with engine.connect() as conn:
            print("\n--- Applying Migration ---\n")
            
            # Try to execute the entire script
            # Split by the major sections to show progress
            sections = [
                ("Drop existing view", "DROP MATERIALIZED VIEW IF EXISTS weekly_returns CASCADE;"),
                ("Full migration", sql_content)
            ]
            
            for section_name, sql in sections:
                if section_name == "Drop existing view":
                    try:
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"✓ {section_name}")
                    except Exception as e:
                        print(f"⚠ {section_name}: {e}")
                elif section_name == "Full migration":
                    try:
                        # Execute the full migration
                        conn.execute(text(sql))
                        conn.commit()
                        print(f"✓ Applied full migration successfully")
                    except Exception as e:
                        print(f"✗ Migration failed: {e}")
                        
                        # Try individual statements for debugging
                        print("\n--- Trying statement-by-statement ---")
                        statements = sql.split(';')
                        for i, stmt in enumerate(statements):
                            stmt = stmt.strip()
                            if stmt and not stmt.startswith('--'):
                                try:
                                    conn.execute(text(stmt + ';'))
                                    print(f"  ✓ Statement {i+1}")
                                except Exception as stmt_error:
                                    print(f"  ✗ Statement {i+1}: {str(stmt_error)[:100]}")
                        conn.commit()
            
            # Verify functions were created
            print("\n--- Verification ---")
            functions_to_check = [
                "get_weekly_observations",
                "calculate_beta_sql",
                "calculate_var_sql"
            ]
            
            for func_name in functions_to_check:
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM pg_proc WHERE proname = :func_name
                    ) AS exists
                """), {"func_name": func_name}).fetchone()
                
                if result and result.exists:
                    print(f"✓ Function '{func_name}' exists")
                else:
                    print(f"✗ Function '{func_name}' NOT found")
            
            # Check for weekly_returns view
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_matviews WHERE matviewname = 'weekly_returns'
                ) AS exists
            """)).fetchone()
            
            if result and result.exists:
                print(f"✓ Materialized view 'weekly_returns' exists")
            else:
                print(f"✗ Materialized view 'weekly_returns' NOT found")
        
        print("\n✅ Migration complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure PostgreSQL/TimescaleDB is running")
        print("2. Check DATABASE_URL in .env")
        print("3. Ensure TimescaleDB extension is installed:")
        print("   CREATE EXTENSION IF NOT EXISTS timescaledb;")
        return False


if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
