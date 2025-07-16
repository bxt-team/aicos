"""JSON file storage adapter for backward compatibility"""

import json
import os
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
import asyncio
from pathlib import Path

from .base import StorageAdapter


class JSONAdapter(StorageAdapter):
    """Storage adapter that uses JSON files"""
    
    def __init__(self, base_path: str = "static"):
        self.base_path = base_path
        self._locks = {}  # Collection-level locks for thread safety
        
    def _get_storage_path(self, collection: str) -> str:
        """Get the storage file path for a collection"""
        # Map collection names to existing file names
        mapping = {
            'affirmations': 'affirmations_storage.json',
            'visual_posts': 'visual_posts_storage.json',
            'instagram_posts': 'instagram_posts_history.json',
            'instagram_analyses': 'instagram_analysis_storage.json',
            'content_items': 'workflows_storage.json',
            'voice_overs': 'voice_overs_storage.json',
            'video_items': 'videos_storage.json',
            'workflows': 'workflows_storage.json',
            'feedback': 'feedback_storage.json',
            'generic_storage': 'generic_storage.json',
        }
        
        filename = mapping.get(collection, f"{collection}_storage.json")
        return os.path.join(self.base_path, filename)
    
    def _get_lock(self, collection: str):
        """Get or create a lock for a collection"""
        if collection not in self._locks:
            self._locks[collection] = asyncio.Lock()
        return self._locks[collection]
    
    async def _load_data(self, collection: str) -> Dict[str, Any]:
        """Load data from JSON file"""
        path = self._get_storage_path(collection)
        
        if not os.path.exists(path):
            # Return empty structure based on collection type
            if collection in ['affirmations', 'visual_posts']:
                return {"items": [], "by_hash": {}}
            else:
                return {}
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {path}: {e}")
            return {}
    
    async def _save_data(self, collection: str, data: Dict[str, Any]):
        """Save data to JSON file"""
        path = self._get_storage_path(collection)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving {path}: {e}")
            raise
    
    async def save(self, 
                   collection: str, 
                   data: Dict[str, Any], 
                   id: Optional[str] = None) -> str:
        """Save data to storage"""
        async with self._get_lock(collection):
            storage = await self._load_data(collection)
            
            # Generate ID if not provided
            if not id:
                id = str(uuid.uuid4())
            
            # Add metadata
            data['id'] = id
            if 'created_at' not in data:
                data['created_at'] = datetime.now().isoformat()
            
            # Handle different storage structures
            if 'items' in storage:
                # List-based storage (affirmations, visual_posts)
                # Remove existing item if updating
                storage['items'] = [
                    item for item in storage.get('items', [])
                    if item.get('id') != id
                ]
                storage['items'].append(data)
                
                # Update hash index if present
                if 'by_hash' in storage and 'hash' in data:
                    storage['by_hash'][data['hash']] = data
            else:
                # Dictionary-based storage
                storage[id] = data
            
            await self._save_data(collection, storage)
            return id
    
    async def load(self, 
                   collection: str, 
                   id: str) -> Optional[Dict[str, Any]]:
        """Load single item by ID"""
        async with self._get_lock(collection):
            storage = await self._load_data(collection)
            
            if 'items' in storage:
                # List-based storage
                for item in storage.get('items', []):
                    if item.get('id') == id:
                        return item
                return None
            else:
                # Dictionary-based storage
                return storage.get(id)
    
    async def list(self, 
                   collection: str, 
                   filters: Optional[Dict] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None,
                   order_by: Optional[str] = None,
                   order_desc: bool = False) -> List[Dict[str, Any]]:
        """List items with optional filtering"""
        async with self._get_lock(collection):
            storage = await self._load_data(collection)
            
            # Get all items
            if 'items' in storage:
                items = storage.get('items', [])
            else:
                items = list(storage.values())
            
            # Apply filters
            if filters:
                filtered_items = []
                for item in items:
                    match = True
                    for key, value in filters.items():
                        if key not in item or item[key] != value:
                            match = False
                            break
                    if match:
                        filtered_items.append(item)
                items = filtered_items
            
            # Apply ordering
            if order_by and items and order_by in items[0]:
                items.sort(
                    key=lambda x: x.get(order_by, ''),
                    reverse=order_desc
                )
            
            # Apply pagination
            if offset:
                items = items[offset:]
            if limit:
                items = items[:limit]
            
            return items
    
    async def update(self, 
                     collection: str, 
                     id: str, 
                     data: Dict[str, Any]) -> bool:
        """Update existing item"""
        async with self._get_lock(collection):
            storage = await self._load_data(collection)
            
            # Add updated timestamp
            data['updated_at'] = datetime.now().isoformat()
            
            if 'items' in storage:
                # List-based storage
                updated = False
                for i, item in enumerate(storage.get('items', [])):
                    if item.get('id') == id:
                        # Merge data
                        storage['items'][i].update(data)
                        updated = True
                        break
                
                if updated:
                    await self._save_data(collection, storage)
                return updated
            else:
                # Dictionary-based storage
                if id in storage:
                    storage[id].update(data)
                    await self._save_data(collection, storage)
                    return True
                return False
    
    async def delete(self, 
                     collection: str, 
                     id: str) -> bool:
        """Delete item by ID"""
        async with self._get_lock(collection):
            storage = await self._load_data(collection)
            
            if 'items' in storage:
                # List-based storage
                original_len = len(storage.get('items', []))
                storage['items'] = [
                    item for item in storage.get('items', [])
                    if item.get('id') != id
                ]
                
                if len(storage['items']) < original_len:
                    await self._save_data(collection, storage)
                    return True
                return False
            else:
                # Dictionary-based storage
                if id in storage:
                    del storage[id]
                    await self._save_data(collection, storage)
                    return True
                return False
    
    async def count(self, 
                    collection: str, 
                    filters: Optional[Dict] = None) -> int:
        """Count items in collection"""
        items = await self.list(collection, filters)
        return len(items)
    
    async def exists(self, 
                     collection: str, 
                     id: str) -> bool:
        """Check if item exists"""
        item = await self.load(collection, id)
        return item is not None
    
    async def clear(self, collection: str) -> bool:
        """Clear all items in collection"""
        async with self._get_lock(collection):
            storage = await self._load_data(collection)
            
            if 'items' in storage:
                storage['items'] = []
                if 'by_hash' in storage:
                    storage['by_hash'] = {}
            else:
                storage.clear()
            
            await self._save_data(collection, storage)
            return True