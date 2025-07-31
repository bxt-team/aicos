#!/usr/bin/env python3
"""
Apply the goal suggestion feedback migration to Supabase
"""
import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase() -> Client:
    """Get Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)

def apply_migration():
    """Apply the feedback table migration"""
    supabase = get_supabase()
    
    # Read the migration file
    migration_path = os.path.join(os.path.dirname(__file__), 'migrations', '019_create_goal_suggestion_feedback.sql')
    
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    try:
        # Execute the migration
        # Note: Supabase Python client doesn't have a direct SQL execution method
        # You'll need to run this through the Supabase dashboard or CLI
        print("Migration SQL generated successfully!")
        print("\nPlease run the following SQL in your Supabase SQL Editor:")
        print("=" * 80)
        print(migration_sql)
        print("=" * 80)
        print("\nOr save the above SQL and run it using the Supabase CLI:")
        print("supabase db push --file backend/migrations/019_create_goal_suggestion_feedback.sql")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Goal Suggestion Feedback Migration")
    print("-" * 40)
    
    if apply_migration():
        print("\n✅ Migration instructions generated successfully!")
    else:
        print("\n❌ Migration failed!")