#!/usr/bin/env python3
"""
Simple migration script to move existing JSON data to Supabase
"""

import asyncio
import json
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
env_file = Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

# Add backend to path
import sys
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.storage import JSONAdapter, SupabaseAdapter
from app.core.storage.migration import StorageMigrator


# Mapping of JSON files to collection names
FILE_MAPPINGS = {
    "affirmations_storage.json": "affirmations",
    "visual_posts_storage.json": "visual_posts",
    "instagram_posts_history.json": "instagram_posts",
    "instagram_analysis_storage.json": "instagram_analyses",
    "workflows_storage.json": "workflows",
    "voice_overs_storage.json": "voice_overs",
    "videos_storage.json": "video_items",
    "feedback_storage.json": "feedback"
}


async def check_json_files():
    """Check which JSON files exist and have data"""
    static_dir = backend_dir / "static"
    print(f"\nChecking JSON files in: {static_dir}")
    
    file_info = {}
    for json_file, collection in FILE_MAPPINGS.items():
        file_path = static_dir / json_file
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                # Count items based on structure
                if isinstance(data, dict):
                    if "items" in data:
                        count = len(data["items"])
                    elif "affirmations" in data:
                        count = len(data["affirmations"])
                    else:
                        # Assume dict keys are IDs
                        count = len([k for k in data.keys() if not k.startswith("_")])
                elif isinstance(data, list):
                    count = len(data)
                else:
                    count = 0
                    
                file_info[json_file] = {
                    "exists": True,
                    "collection": collection,
                    "count": count,
                    "size": file_path.stat().st_size
                }
                print(f"✅ {json_file}: {count} items ({file_path.stat().st_size} bytes)")
            except Exception as e:
                file_info[json_file] = {
                    "exists": True,
                    "collection": collection,
                    "error": str(e)
                }
                print(f"❌ {json_file}: Error reading - {e}")
        else:
            file_info[json_file] = {"exists": False, "collection": collection}
            print(f"⚠️  {json_file}: Not found")
    
    return file_info


async def migrate_data(dry_run=True):
    """Migrate data from JSON to Supabase"""
    # Check Supabase configuration
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_KEY"):
        print("\n❌ Error: Supabase credentials not configured")
        print("Please set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env")
        return
    
    # Check JSON files
    file_info = await check_json_files()
    
    # Filter files with data
    files_to_migrate = {
        f: info for f, info in file_info.items() 
        if info.get("exists") and info.get("count", 0) > 0
    }
    
    if not files_to_migrate:
        print("\n⚠️  No JSON files with data found to migrate")
        return
    
    print(f"\n{'DRY RUN: ' if dry_run else ''}Ready to migrate {len(files_to_migrate)} files")
    
    if not dry_run:
        confirm = input("\nProceed with migration? (y/n): ")
        if confirm.lower() != 'y':
            print("Migration cancelled")
            return
    
    # Create adapters
    json_adapter = JSONAdapter(base_path=str(backend_dir / "static"))
    supabase_adapter = SupabaseAdapter(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    # Create migrator
    migrator = StorageMigrator(
        source_adapter=json_adapter,
        target_adapter=supabase_adapter
    )
    
    # Migrate each collection
    results = {}
    for json_file, info in files_to_migrate.items():
        collection = info["collection"]
        print(f"\nMigrating {collection} from {json_file}...")
        
        if dry_run:
            results[collection] = {
                "total": info["count"],
                "dry_run": True
            }
            print(f"[DRY RUN] Would migrate {info['count']} items")
        else:
            try:
                stats = await migrator.migrate_collection(collection)
                results[collection] = stats
                print(f"✅ Migrated {stats['success']}/{stats['total']} items")
            except Exception as e:
                results[collection] = {"error": str(e)}
                print(f"❌ Error: {e}")
    
    # Print summary
    print("\n=== MIGRATION SUMMARY ===")
    for collection, result in results.items():
        if "error" in result:
            print(f"{collection}: ❌ {result['error']}")
        elif result.get("dry_run"):
            print(f"{collection}: 📋 {result['total']} items (dry run)")
        else:
            print(f"{collection}: ✅ {result.get('success', 0)}/{result.get('total', 0)} migrated")


async def main():
    """Main function"""
    print("Supabase Migration Tool")
    print("======================")
    
    # Check environment
    if os.getenv("SUPABASE_URL"):
        print(f"✅ Supabase URL: {os.getenv('SUPABASE_URL')[:30]}...")
        print(f"✅ Service Key: {'*' * 20}")
    else:
        print("❌ Supabase not configured")
    
    # Menu
    print("\nOptions:")
    print("1. Check JSON files (what would be migrated)")
    print("2. Dry run (simulate migration)")
    print("3. Migrate data to Supabase")
    print("4. Exit")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        await check_json_files()
    elif choice == "2":
        await migrate_data(dry_run=True)
    elif choice == "3":
        await migrate_data(dry_run=False)
    elif choice == "4":
        print("Exiting...")
    else:
        print("Invalid option")


if __name__ == "__main__":
    asyncio.run(main())