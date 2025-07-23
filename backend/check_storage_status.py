#!/usr/bin/env python3
"""
Quick script to check storage configuration and status
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from app.core.config import settings
from app.core.storage.factory import StorageFactory


async def main():
    print("🔍 AICOS Storage Status Check")
    print("=" * 50)
    
    # Configuration
    print("\n📋 Configuration:")
    print(f"STORAGE_ADAPTER: {settings.STORAGE_ADAPTER}")
    print(f"SUPABASE_URL: {'✅ Set' if settings.SUPABASE_URL else '❌ Not set'}")
    print(f"SUPABASE_SERVICE_KEY: {'✅ Set' if settings.SUPABASE_SERVICE_KEY else '❌ Not set'}")
    
    if settings.STORAGE_ADAPTER == 'dual':
        print(f"DUAL_WRITE_READ_FROM: {settings.DUAL_WRITE_READ_FROM}")
    
    # Current adapter
    print(f"\n🔧 Current Storage Mode: {settings.STORAGE_ADAPTER.upper()}")
    
    try:
        adapter = StorageFactory.get_adapter()
        
        # Test collections
        collections = [
            'affirmations',
            'visual_posts', 
            'instagram_posts',
            'workflows'
        ]
        
        print("\n📊 Data Summary:")
        total_items = 0
        
        for collection in collections:
            try:
                count = await adapter.count(collection)
                total_items += count
                print(f"  {collection}: {count} items")
            except Exception as e:
                print(f"  {collection}: ❌ Error - {str(e)[:50]}")
        
        print(f"\n📈 Total items across all collections: {total_items}")
        
        # Mode-specific info
        if settings.STORAGE_ADAPTER == 'json':
            print("\n💾 Storage: JSON files in static/ directory")
            print("👉 Ready to migrate to Supabase when needed")
            
        elif settings.STORAGE_ADAPTER == 'supabase':
            print("\n☁️ Storage: Supabase cloud database")
            print("✅ Fully migrated!")
            
        elif settings.STORAGE_ADAPTER == 'dual':
            print("\n🔄 Storage: Dual-write mode")
            print(f"  Writing to: JSON + Supabase")
            print(f"  Reading from: {settings.DUAL_WRITE_READ_FROM.upper()}")
            print("👉 Monitor for a few days before switching reads")
        
        # Next steps
        print("\n📝 Next Steps:")
        if settings.STORAGE_ADAPTER == 'json':
            print("1. Set up Supabase credentials in .env")
            print("2. Run migration dry-run: python -m scripts.migrate_to_supabase --dry-run")
            print("3. Enable dual-write mode: STORAGE_ADAPTER=dual")
        elif settings.STORAGE_ADAPTER == 'dual':
            if settings.DUAL_WRITE_READ_FROM == 'json':
                print("1. Monitor application logs for errors")
                print("2. Verify data in Supabase dashboard")
                print("3. Switch reads to Supabase: DUAL_WRITE_READ_FROM=supabase")
            else:
                print("1. Test all features thoroughly")
                print("2. Monitor performance")
                print("3. Switch to Supabase only: STORAGE_ADAPTER=supabase")
        else:
            print("✅ Migration complete! Consider archiving JSON files.")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())