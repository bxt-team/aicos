#!/usr/bin/env python3
"""
Direct migration runner for multi-tenant database setup
Uses direct database connection instead of RPC
"""
import os
import sys
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DirectMigrationRunner:
    def __init__(self):
        # Get database URL
        db_url = os.getenv("DATABASE_URL") or self._construct_db_url()
        
        if not db_url:
            raise ValueError("DATABASE_URL must be set or SUPABASE_URL/SUPABASE_DB_PASSWORD must be provided")
        
        self.db_url = db_url
        self.migrations_dir = Path(__file__).parent
        
    def _construct_db_url(self) -> Optional[str]:
        """Construct database URL from Supabase credentials"""
        supabase_url = os.getenv("SUPABASE_URL")
        db_password = os.getenv("SUPABASE_DB_PASSWORD")
        
        if not supabase_url or not db_password:
            return None
        
        # Extract project ref from Supabase URL
        # Format: https://PROJECT_REF.supabase.co
        import re
        from urllib.parse import quote_plus
        
        match = re.match(r'https://([^.]+)\.supabase\.co', supabase_url)
        if not match:
            return None
        
        project_ref = match.group(1)
        # URL encode the password to handle special characters
        encoded_password = quote_plus(db_password)
        return f"postgresql://postgres:{encoded_password}@db.{project_ref}.supabase.co:5432/postgres"
    
    def get_migration_files(self) -> List[Path]:
        """Get all SQL migration files in order"""
        files = sorted(self.migrations_dir.glob("*.sql"))
        return [f for f in files if f.name[0].isdigit()]
    
    def create_migrations_table(self, conn):
        """Create migrations tracking table if it doesn't exist"""
        query = """
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            filename TEXT UNIQUE NOT NULL,
            executed_at TIMESTAMP DEFAULT NOW(),
            checksum TEXT
        );
        """
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
    
    def get_executed_migrations(self, conn) -> List[str]:
        """Get list of already executed migrations"""
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT filename FROM migrations")
                return [row[0] for row in cur.fetchall()]
        except psycopg2.errors.UndefinedTable:
            return []
    
    def execute_migration(self, conn, filepath: Path):
        """Execute a single migration file"""
        filename = filepath.name
        print(f"\nExecuting migration: {filename}")
        
        # Read SQL content
        with open(filepath, 'r') as f:
            sql_content = f.read()
        
        try:
            with conn.cursor() as cur:
                # Execute the entire migration as one transaction
                cur.execute(sql_content)
                
                # Record migration as executed
                cur.execute(
                    "INSERT INTO migrations (filename, checksum) VALUES (%s, %s)",
                    (filename, str(hash(sql_content)))
                )
                
            conn.commit()
            print(f"✓ Migration {filename} completed successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"✗ Error executing migration {filename}: {e}")
            raise
    
    def run_migrations(self, force: bool = False):
        """Run all pending migrations"""
        print("Starting database migrations...")
        
        # Connect to database
        conn = psycopg2.connect(self.db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        try:
            # Create migrations table
            self.create_migrations_table(conn)
            
            # Get migration files
            migration_files = self.get_migration_files()
            if not migration_files:
                print("No migration files found")
                return
            
            # Get already executed migrations
            executed = self.get_executed_migrations(conn) if not force else []
            
            # Execute pending migrations
            pending = [f for f in migration_files if f.name not in executed]
            
            if not pending:
                print("All migrations already executed")
                return
            
            print(f"\nFound {len(pending)} pending migrations:")
            for f in pending:
                print(f"  - {f.name}")
            
            # Confirm execution
            if not force and sys.stdin.isatty():
                response = input("\nProceed with migrations? (y/N): ")
                if response.lower() != 'y':
                    print("Migrations cancelled")
                    return
            
            # Execute migrations
            for filepath in pending:
                self.execute_migration(conn, filepath)
            
            print(f"\n✓ All migrations completed successfully!")
            
        finally:
            conn.close()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run database migrations directly")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    parser.add_argument("--check", action="store_true", help="Check pending migrations without running")
    
    args = parser.parse_args()
    
    runner = DirectMigrationRunner()
    
    if args.check:
        # Just check what would be run
        conn = psycopg2.connect(runner.db_url)
        try:
            runner.create_migrations_table(conn)
            migration_files = runner.get_migration_files()
            executed = runner.get_executed_migrations(conn)
            pending = [f for f in migration_files if f.name not in executed]
            
            print(f"Total migrations: {len(migration_files)}")
            print(f"Executed: {len(executed)}")
            print(f"Pending: {len(pending)}")
            
            if pending:
                print("\nPending migrations:")
                for f in pending:
                    print(f"  - {f.name}")
        finally:
            conn.close()
    else:
        runner.run_migrations(force=args.force)

if __name__ == "__main__":
    main()