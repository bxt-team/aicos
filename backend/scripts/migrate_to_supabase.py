#!/usr/bin/env python3
"""
Migration script to move data from JSON files to Supabase
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.storage import StorageFactory, JSONAdapter, SupabaseAdapter
from app.core.storage.migration import StorageMigrator, DualWriteAdapter


async def test_supabase_connection():
    """Test that Supabase connection is working"""
    print("Testing Supabase connection...")
    
    try:
        adapter = StorageFactory.create_adapter("supabase")
        # Try to count items in a collection
        count = await adapter.count("affirmations")
        print(f"✅ Supabase connection successful! Found {count} affirmations.")
        return True
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return False


async def migrate_collection(collection_name: str, dry_run: bool = False):
    """Migrate a single collection"""
    print(f"\nMigrating {collection_name}...")
    
    # Create adapters
    json_adapter = JSONAdapter(base_path=str(backend_dir / "static"))
    supabase_adapter = StorageFactory.create_adapter("supabase")
    
    # Create migrator
    migrator = StorageMigrator(
        source_adapter=json_adapter,
        target_adapter=supabase_adapter
    )
    
    if dry_run:
        # Just count items
        count = await json_adapter.count(collection_name)
        print(f"[DRY RUN] Would migrate {count} items from {collection_name}")
        return {"total": count, "dry_run": True}
    else:
        # Perform actual migration
        stats = await migrator.migrate_collection(collection_name)
        return stats


async def main():
    """Main migration function"""
    # Load environment variables
    env_file = backend_dir.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Loaded environment from {env_file}")
    else:
        # Try regular .env
        env_file = backend_dir.parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            print(f"Loaded environment from {env_file}")
    
    # Check if Supabase credentials are set
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_KEY"):
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment")
        print("Please create a .env file with your Supabase credentials")
        return
    
    # Test connection
    if not await test_supabase_connection():
        return
    
    # Collections to migrate
    collections = [
        "affirmations",
        "visual_posts",
        "instagram_posts",
        "instagram_analyses",
        "workflows",
        "video_items",
        "voice_overs",
        "feedback"
    ]
    
    # Ask user for migration mode
    print("\nMigration Options:")
    print("1. Dry run (show what would be migrated)")
    print("2. Migrate all collections")
    print("3. Migrate specific collection")
    print("4. Set up dual-write mode")
    
    choice = input("\nSelect option (1-4): ").strip()
    
    if choice == "1":
        # Dry run
        print("\n=== DRY RUN MODE ===")
        for collection in collections:
            try:
                await migrate_collection(collection, dry_run=True)
            except Exception as e:
                print(f"Error checking {collection}: {e}")
    
    elif choice == "2":
        # Migrate all
        confirm = input("\nThis will migrate all data to Supabase. Continue? (y/n): ")
        if confirm.lower() == 'y':
            results = {}
            for collection in collections:
                try:
                    stats = await migrate_collection(collection, dry_run=False)
                    results[collection] = stats
                except Exception as e:
                    print(f"Error migrating {collection}: {e}")
                    results[collection] = {"error": str(e)}
            
            # Print summary
            print("\n=== MIGRATION SUMMARY ===")
            for collection, stats in results.items():
                if "error" in stats:
                    print(f"{collection}: ❌ Error - {stats['error']}")
                else:
                    print(f"{collection}: ✅ {stats['success']}/{stats['total']} migrated")
    
    elif choice == "3":
        # Migrate specific collection
        print("\nAvailable collections:")
        for i, collection in enumerate(collections, 1):
            print(f"{i}. {collection}")
        
        coll_choice = input("\nSelect collection number: ").strip()
        try:
            collection = collections[int(coll_choice) - 1]
            stats = await migrate_collection(collection, dry_run=False)
            print(f"\n✅ Migration complete: {stats['success']}/{stats['total']} items migrated")
        except (ValueError, IndexError):
            print("Invalid selection")
        except Exception as e:
            print(f"Error: {e}")
    
    elif choice == "4":
        # Set up dual-write mode
        print("\n=== DUAL-WRITE MODE SETUP ===")
        print("This will configure the system to write to both JSON and Supabase")
        print("but continue reading from JSON files for safety.")
        print("\nTo enable dual-write mode, add this to your .env file:")
        print("STORAGE_ADAPTER=dual")
        print("DUAL_WRITE_READ_FROM=json")
        print("\nThen restart your application.")
        
        # Create example dual-write configuration
        config_path = backend_dir / "dual_write_config.py"
        with open(config_path, 'w') as f:
            f.write('''"""
Dual-write configuration for gradual migration
"""

from app.core.storage import JSONAdapter, SupabaseAdapter
from app.core.storage.migration import DualWriteAdapter
from app.core.storage.factory import StorageFactory


def setup_dual_write():
    """Set up dual-write adapter"""
    json_adapter = JSONAdapter()
    supabase_adapter = SupabaseAdapter(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_SERVICE_KEY")
    )
    
    dual_adapter = DualWriteAdapter(
        primary=json_adapter,
        secondary=supabase_adapter,
        read_from_primary=True  # Still read from JSON
    )
    
    # Replace factory instance
    StorageFactory._instance = dual_adapter
    
    print("✅ Dual-write mode enabled")
    print("   - Writing to: JSON (primary) and Supabase (secondary)")
    print("   - Reading from: JSON")
''')
        print(f"\n✅ Created dual-write configuration at: {config_path}")
    
    else:
        print("Invalid option")


if __name__ == "__main__":
    asyncio.run(main())