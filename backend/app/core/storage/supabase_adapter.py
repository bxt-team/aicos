"""Supabase storage adapter"""

import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime
from supabase import create_client, Client

from .base import StorageAdapter


class SupabaseAdapter(StorageAdapter):
    """Storage adapter that uses Supabase database"""
    
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)
        self._table_mappings = {
            # Map collection names to table names
            'affirmations': 'agent_affirmation_items',
            'visual_posts': 'agent_visual_posts',
            'instagram_posts': 'agent_instagram_posts',
            'instagram_analyses': 'agent_instagram_analyses',
            'instagram_reels': 'agent_instagram_reels',
            'content_items': 'agent_content_items',
            'content_approvals': 'agent_content_approvals',
            'video_items': 'agent_video_items',
            'voice_overs': 'agent_voice_overs',
            'x_analyses': 'agent_x_analyses',
            'x_posts': 'agent_x_posts',
            'threads_analyses': 'agent_threads_analyses',
            'threads_posts': 'agent_threads_posts',
            'play_store_analyses': 'agent_play_store_analyses',
            'qa_interactions': 'agent_qa_interactions',
            'workflows': 'system_workflows',
            'feedback': 'system_feedback',
            'cost_tracking': 'system_cost_tracking',
            'generic_storage': 'system_generic_storage',
        }
    
    def _get_table_name(self, collection: str) -> str:
        """Get the actual table name for a collection"""
        return self._table_mappings.get(collection, collection)
    
    def _prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for Supabase insertion"""
        # Remove None values (Supabase doesn't like them)
        cleaned = {k: v for k, v in data.items() if v is not None}
        
        # Convert datetime objects to ISO strings
        for key, value in cleaned.items():
            if isinstance(value, datetime):
                cleaned[key] = value.isoformat()
        
        # Handle special fields based on collection
        if 'metadata' not in cleaned:
            cleaned['metadata'] = {}
            
        return cleaned
    
    async def save(self, 
                   collection: str, 
                   data: Dict[str, Any], 
                   id: Optional[str] = None) -> str:
        """Save data to Supabase"""
        table_name = self._get_table_name(collection)
        
        # Generate ID if not provided
        if not id:
            id = str(uuid.uuid4())
        
        # Prepare data
        data = self._prepare_data(data)
        data['id'] = id
        
        # Special handling for different collections
        if collection == 'affirmations':
            # Ensure required fields
            if 'theme' not in data or 'period' not in data or 'affirmation' not in data:
                raise ValueError("Affirmations require theme, period, and affirmation fields")
        
        try:
            # Use upsert to handle both insert and update
            response = self.client.table(table_name).upsert(data).execute()
            return id
        except Exception as e:
            print(f"Error saving to {table_name}: {e}")
            raise
    
    async def load(self, 
                   collection: str, 
                   id: str) -> Optional[Dict[str, Any]]:
        """Load single item by ID"""
        table_name = self._get_table_name(collection)
        
        try:
            response = self.client.table(table_name).select("*").eq('id', id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            print(f"Error loading from {table_name}: {e}")
            return None
    
    async def list(self, 
                   collection: str, 
                   filters: Optional[Dict] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None,
                   order_by: Optional[str] = None,
                   order_desc: bool = False) -> List[Dict[str, Any]]:
        """List items with optional filtering"""
        table_name = self._get_table_name(collection)
        
        try:
            query = self.client.table(table_name).select("*")
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(key, value)
                    elif value is None:
                        query = query.is_(key, 'null')
                    else:
                        query = query.eq(key, value)
            
            # Apply ordering
            if order_by:
                query = query.order(order_by, desc=order_desc)
            else:
                # Default ordering by created_at desc
                query = query.order('created_at', desc=True)
            
            # Apply pagination
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error listing from {table_name}: {e}")
            return []
    
    async def update(self, 
                     collection: str, 
                     id: str, 
                     data: Dict[str, Any]) -> bool:
        """Update existing item"""
        table_name = self._get_table_name(collection)
        
        # Prepare data
        data = self._prepare_data(data)
        
        # Add updated timestamp if table has it
        if collection not in ['affirmations', 'instagram_analyses', 'workflows']:
            data['updated_at'] = datetime.now().isoformat()
        
        try:
            response = self.client.table(table_name).update(data).eq('id', id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error updating {table_name}: {e}")
            return False
    
    async def delete(self, 
                     collection: str, 
                     id: str) -> bool:
        """Delete item by ID"""
        table_name = self._get_table_name(collection)
        
        try:
            response = self.client.table(table_name).delete().eq('id', id).execute()
            return True
        except Exception as e:
            print(f"Error deleting from {table_name}: {e}")
            return False
    
    async def count(self, 
                    collection: str, 
                    filters: Optional[Dict] = None) -> int:
        """Count items in collection"""
        table_name = self._get_table_name(collection)
        
        try:
            query = self.client.table(table_name).select("id", count='exact')
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        query = query.in_(key, value)
                    elif value is None:
                        query = query.is_(key, 'null')
                    else:
                        query = query.eq(key, value)
            
            response = query.execute()
            return response.count or 0
        except Exception as e:
            print(f"Error counting in {table_name}: {e}")
            return 0
    
    async def exists(self, 
                     collection: str, 
                     id: str) -> bool:
        """Check if item exists"""
        table_name = self._get_table_name(collection)
        
        try:
            response = self.client.table(table_name).select("id").eq('id', id).execute()
            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking existence in {table_name}: {e}")
            return False
    
    async def clear(self, collection: str) -> bool:
        """Clear all items in collection"""
        table_name = self._get_table_name(collection)
        
        try:
            # Delete all records
            response = self.client.table(table_name).delete().neq('id', '').execute()
            return True
        except Exception as e:
            print(f"Error clearing {table_name}: {e}")
            return False
    
    # Additional Supabase-specific methods
    
    async def search(self, 
                     collection: str, 
                     search_term: str, 
                     search_fields: List[str]) -> List[Dict[str, Any]]:
        """Full-text search across specified fields"""
        table_name = self._get_table_name(collection)
        
        try:
            query = self.client.table(table_name).select("*")
            
            # Build OR condition for search fields
            or_conditions = []
            for field in search_fields:
                or_conditions.append(f"{field}.ilike.%{search_term}%")
            
            query = query.or_(','.join(or_conditions))
            response = query.execute()
            return response.data
        except Exception as e:
            print(f"Error searching {table_name}: {e}")
            return []
    
    async def batch_save(self, 
                         collection: str, 
                         items: List[Dict[str, Any]]) -> List[str]:
        """Save multiple items at once"""
        table_name = self._get_table_name(collection)
        ids = []
        
        # Prepare all items
        for item in items:
            if 'id' not in item:
                item['id'] = str(uuid.uuid4())
            ids.append(item['id'])
            item = self._prepare_data(item)
        
        try:
            response = self.client.table(table_name).upsert(items).execute()
            return ids
        except Exception as e:
            print(f"Error batch saving to {table_name}: {e}")
            raise