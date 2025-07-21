#!/usr/bin/env python3
"""
Migration runner for multi-tenant database setup
"""
import os
import asyncio
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MigrationRunner:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.client: Client = create_client(url, key)
        self.migrations_dir = Path(__file__).parent
        
    def get_migration_files(self) -> List[Path]:
        """Get all SQL migration files in order"""
        files = sorted(self.migrations_dir.glob("*.sql"))
        return [f for f in files if f.name[0].isdigit()]
    
    async def create_migrations_table(self):
        """Create migrations tracking table if it doesn't exist"""
        query = """
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            filename TEXT UNIQUE NOT NULL,
            executed_at TIMESTAMP DEFAULT NOW(),
            checksum TEXT
        );
        """
        try:
            self.client.rpc("execute_sql", {"query": query}).execute()
        except Exception as e:
            # Table might already exist
            print(f"Note: {e}")
    
    async def get_executed_migrations(self) -> List[str]:
        """Get list of already executed migrations"""
        try:
            result = self.client.table("migrations").select("filename").execute()
            return [row["filename"] for row in result.data]
        except Exception:
            return []
    
    async def execute_migration(self, filepath: Path):
        """Execute a single migration file"""
        filename = filepath.name
        print(f"\nExecuting migration: {filename}")
        
        # Read SQL content
        with open(filepath, 'r') as f:
            sql_content = f.read()
        
        # Split into individual statements (simple approach)
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        try:
            # Execute each statement
            for i, statement in enumerate(statements):
                if statement:
                    print(f"  Executing statement {i+1}/{len(statements)}...")
                    self.client.rpc("execute_sql", {"query": statement + ";"}).execute()
            
            # Record migration as executed
            self.client.table("migrations").insert({
                "filename": filename,
                "checksum": str(hash(sql_content))
            }).execute()
            
            print(f"✓ Migration {filename} completed successfully")
            
        except Exception as e:
            print(f"✗ Error executing migration {filename}: {e}")
            raise
    
    async def run_migrations(self, force: bool = False):
        """Run all pending migrations"""
        print("Starting database migrations...")
        
        # Create migrations table
        await self.create_migrations_table()
        
        # Get migration files
        migration_files = self.get_migration_files()
        if not migration_files:
            print("No migration files found")
            return
        
        # Get already executed migrations
        executed = await self.get_executed_migrations() if not force else []
        
        # Execute pending migrations
        pending = [f for f in migration_files if f.name not in executed]
        
        if not pending:
            print("All migrations already executed")
            return
        
        print(f"\nFound {len(pending)} pending migrations:")
        for f in pending:
            print(f"  - {f.name}")
        
        # Confirm execution
        if not force and not self.is_non_interactive():
            response = input("\nProceed with migrations? (y/N): ")
            if response.lower() != 'y':
                print("Migrations cancelled")
                return
        
        # Execute migrations
        for filepath in pending:
            await self.execute_migration(filepath)
        
        print(f"\n✓ All migrations completed successfully!")
    
    async def rollback_migration(self, filename: Optional[str] = None):
        """Rollback migrations (requires rollback scripts)"""
        print("Rollback functionality not yet implemented")
        print("Please manually rollback using your database client")
    
    def is_non_interactive(self) -> bool:
        """Check if running in non-interactive mode"""
        import sys
        return not sys.stdin.isatty()

async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Run database migrations")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts")
    parser.add_argument("--rollback", type=str, help="Rollback specific migration")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be executed without running")
    
    args = parser.parse_args()
    
    runner = MigrationRunner()
    
    if args.rollback:
        await runner.rollback_migration(args.rollback)
    else:
        await runner.run_migrations(force=args.force)

if __name__ == "__main__":
    asyncio.run(main())