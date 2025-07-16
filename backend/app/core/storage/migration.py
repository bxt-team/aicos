"""Storage migration utilities"""

import asyncio
from typing import Dict, List, Optional
from datetime import datetime

from .base import StorageAdapter


class StorageMigrator:
    """Utility class for migrating data between storage adapters"""
    
    def __init__(self, 
                 source_adapter: StorageAdapter,
                 target_adapter: StorageAdapter):
        self.source = source_adapter
        self.target = target_adapter
    
    async def migrate_collection(self, 
                                collection: str,
                                batch_size: int = 100,
                                transform_fn: Optional[callable] = None) -> Dict[str, int]:
        """
        Migrate a single collection from source to target
        
        Args:
            collection: Name of the collection to migrate
            batch_size: Number of items to process at once
            transform_fn: Optional function to transform data during migration
            
        Returns:
            Dict with migration statistics
        """
        print(f"Migrating collection: {collection}")
        
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Get total count
        total_count = await self.source.count(collection)
        stats['total'] = total_count
        
        print(f"Found {total_count} items to migrate")
        
        # Migrate in batches
        offset = 0
        while offset < total_count:
            # Fetch batch
            items = await self.source.list(
                collection,
                limit=batch_size,
                offset=offset
            )
            
            # Process each item
            for item in items:
                try:
                    # Apply transformation if provided
                    if transform_fn:
                        item = await transform_fn(item)
                        if item is None:
                            stats['skipped'] += 1
                            continue
                    
                    # Save to target
                    await self.target.save(
                        collection,
                        item,
                        id=item.get('id')
                    )
                    stats['success'] += 1
                    
                except Exception as e:
                    print(f"Error migrating item {item.get('id')}: {e}")
                    stats['failed'] += 1
            
            offset += batch_size
            print(f"Progress: {offset}/{total_count}")
        
        print(f"Migration complete for {collection}: {stats}")
        return stats
    
    async def migrate_all(self, 
                         collections: List[str],
                         dry_run: bool = False) -> Dict[str, Dict[str, int]]:
        """
        Migrate multiple collections
        
        Args:
            collections: List of collection names to migrate
            dry_run: If True, only simulate migration
            
        Returns:
            Dict mapping collection names to migration statistics
        """
        results = {}
        
        for collection in collections:
            if dry_run:
                count = await self.source.count(collection)
                results[collection] = {
                    'total': count,
                    'success': 0,
                    'failed': 0,
                    'skipped': 0,
                    'dry_run': True
                }
                print(f"[DRY RUN] Would migrate {count} items from {collection}")
            else:
                results[collection] = await self.migrate_collection(collection)
        
        return results


class DualWriteAdapter(StorageAdapter):
    """
    Storage adapter that writes to multiple adapters
    Useful for gradual migration
    """
    
    def __init__(self, 
                 primary: StorageAdapter,
                 secondary: StorageAdapter,
                 read_from_primary: bool = True):
        self.primary = primary
        self.secondary = secondary
        self.read_from_primary = read_from_primary
    
    async def save(self, collection: str, data: Dict, id: Optional[str] = None) -> str:
        """Save to both adapters"""
        # Save to primary first
        result_id = await self.primary.save(collection, data, id)
        
        # Then save to secondary (ignore errors)
        try:
            await self.secondary.save(collection, data, result_id)
        except Exception as e:
            print(f"Warning: Failed to save to secondary adapter: {e}")
        
        return result_id
    
    async def load(self, collection: str, id: str) -> Optional[Dict]:
        """Load from configured adapter"""
        if self.read_from_primary:
            return await self.primary.load(collection, id)
        else:
            return await self.secondary.load(collection, id)
    
    async def list(self, collection: str, **kwargs) -> List[Dict]:
        """List from configured adapter"""
        if self.read_from_primary:
            return await self.primary.list(collection, **kwargs)
        else:
            return await self.secondary.list(collection, **kwargs)
    
    async def update(self, collection: str, id: str, data: Dict) -> bool:
        """Update in both adapters"""
        result = await self.primary.update(collection, id, data)
        
        try:
            await self.secondary.update(collection, id, data)
        except Exception as e:
            print(f"Warning: Failed to update in secondary adapter: {e}")
        
        return result
    
    async def delete(self, collection: str, id: str) -> bool:
        """Delete from both adapters"""
        result = await self.primary.delete(collection, id)
        
        try:
            await self.secondary.delete(collection, id)
        except Exception as e:
            print(f"Warning: Failed to delete from secondary adapter: {e}")
        
        return result
    
    async def count(self, collection: str, filters: Optional[Dict] = None) -> int:
        """Count from configured adapter"""
        if self.read_from_primary:
            return await self.primary.count(collection, filters)
        else:
            return await self.secondary.count(collection, filters)
    
    async def exists(self, collection: str, id: str) -> bool:
        """Check existence in configured adapter"""
        if self.read_from_primary:
            return await self.primary.exists(collection, id)
        else:
            return await self.secondary.exists(collection, id)
    
    async def clear(self, collection: str) -> bool:
        """Clear both adapters"""
        result = await self.primary.clear(collection)
        
        try:
            await self.secondary.clear(collection)
        except Exception as e:
            print(f"Warning: Failed to clear secondary adapter: {e}")
        
        return result


# Migration script example
async def run_migration_example():
    """Example migration script"""
    # Create adapters
    json_adapter = StorageFactory.create_adapter("json")
    supabase_adapter = StorageFactory.create_adapter("supabase")
    
    # Create migrator
    migrator = StorageMigrator(
        source_adapter=json_adapter,
        target_adapter=supabase_adapter
    )
    
    # Define collections to migrate
    collections = [
        'affirmations',
        'visual_posts',
        'instagram_posts',
        'workflows',
        'feedback'
    ]
    
    # Run migration
    results = await migrator.migrate_all(collections, dry_run=True)
    
    # Print results
    print("\nMigration Summary:")
    for collection, stats in results.items():
        print(f"{collection}: {stats}")


if __name__ == "__main__":
    # Example usage
    asyncio.run(run_migration_example())