"""
Scoped storage adapter for multi-tenant data isolation
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.core.storage.base import StorageAdapter
from app.models.auth import RequestContext

logger = logging.getLogger(__name__)


class ScopedStorageAdapter(StorageAdapter):
    """
    Storage adapter that automatically scopes all operations to the current organization/project context
    """
    
    def __init__(self, base_adapter: StorageAdapter, context: RequestContext):
        self.base_adapter = base_adapter
        self.context = context
        
        if not context or not context.organization_id:
            raise ValueError("Valid context with organization_id is required for ScopedStorageAdapter")
    
    async def save(self, collection: str, data: Dict[str, Any], id: Optional[str] = None) -> str:
        """Save data with automatic context injection"""
        # Inject context into data
        scoped_data = {
            **data,
            'organization_id': str(self.context.organization_id),
            'project_id': str(self.context.project_id) if self.context.project_id else None,
            'created_by': str(self.context.user_id) if not data.get('created_by') else data['created_by'],
            'created_at': data.get('created_at', datetime.utcnow().isoformat()),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.debug(f"Saving to {collection} with org={self.context.organization_id}, project={self.context.project_id}")
        
        return await self.base_adapter.save(collection, scoped_data, id)
    
    async def load(self, collection: str, id: str) -> Optional[Dict[str, Any]]:
        """Load a document by ID with context validation"""
        result = await self.base_adapter.load(collection, id)
        
        if not result:
            return None
        
        # Validate that the document belongs to the current context
        doc_org_id = result.get('organization_id')
        doc_project_id = result.get('project_id')
        
        # Check organization match
        if str(doc_org_id) != str(self.context.organization_id):
            logger.warning(f"Access denied: document org {doc_org_id} != context org {self.context.organization_id}")
            return None
        
        # Check project match if context has project_id
        if self.context.project_id and doc_project_id:
            if str(doc_project_id) != str(self.context.project_id):
                logger.warning(f"Access denied: document project {doc_project_id} != context project {self.context.project_id}")
                return None
        
        return result
    
    async def list(self, collection: str, filters: Optional[Dict] = None, 
                   limit: int = 100, offset: int = 0, 
                   order_by: Optional[str] = None, 
                   order_desc: bool = False) -> List[Dict[str, Any]]:
        """List documents with automatic context filtering"""
        # Add context filters
        scoped_filters = {
            **(filters or {}),
            'organization_id': str(self.context.organization_id)
        }
        
        # Add project filter if context has project_id
        if self.context.project_id:
            scoped_filters['project_id'] = str(self.context.project_id)
        
        logger.debug(f"Listing {collection} with filters: {scoped_filters}")
        
        return await self.base_adapter.list(
            collection, 
            scoped_filters, 
            limit=limit, 
            offset=offset,
            order_by=order_by,
            order_desc=order_desc
        )
    
    async def update(self, collection: str, id: str, data: Dict[str, Any]) -> bool:
        """Update a document with context validation"""
        # First check if document exists and belongs to current context
        existing = await self.load(collection, id)
        if not existing:
            logger.warning(f"Cannot update: document {id} not found or access denied")
            return False
        
        # Add updated_at timestamp
        update_data = {
            **data,
            'updated_at': datetime.utcnow().isoformat(),
            'updated_by': str(self.context.user_id)
        }
        
        # Ensure context fields are not modified
        update_data['organization_id'] = str(self.context.organization_id)
        if self.context.project_id:
            update_data['project_id'] = str(self.context.project_id)
        
        return await self.base_adapter.update(collection, id, update_data)
    
    async def delete(self, collection: str, id: str) -> bool:
        """Delete a document with context validation"""
        # First check if document exists and belongs to current context
        existing = await self.load(collection, id)
        if not existing:
            logger.warning(f"Cannot delete: document {id} not found or access denied")
            return False
        
        return await self.base_adapter.delete(collection, id)
    
    async def count(self, collection: str, filters: Optional[Dict] = None) -> int:
        """Count documents with automatic context filtering"""
        # Add context filters
        scoped_filters = {
            **(filters or {}),
            'organization_id': str(self.context.organization_id)
        }
        
        if self.context.project_id:
            scoped_filters['project_id'] = str(self.context.project_id)
        
        return await self.base_adapter.count(collection, scoped_filters)
    
    async def exists(self, collection: str, id: str) -> bool:
        """Check if a document exists with context validation"""
        result = await self.load(collection, id)
        return result is not None
    
    async def clear(self, collection: str) -> bool:
        """Clear all items in collection for current context (use with caution!)"""
        # This is a dangerous operation - we should only clear items in current context
        logger.warning(f"Clear operation requested for {collection} in org {self.context.organization_id}")
        
        # Get all items in current context
        items = await self.list(collection, limit=10000)  # Set a high limit
        
        # Delete each item
        success = True
        for item in items:
            if 'id' in item:
                if not await self.delete(collection, item['id']):
                    success = False
        
        return success
    
    async def search(self, collection: str, query: str, 
                     filters: Optional[Dict] = None,
                     limit: int = 100) -> List[Dict[str, Any]]:
        """Search documents with automatic context filtering"""
        # Add context filters
        scoped_filters = {
            **(filters or {}),
            'organization_id': str(self.context.organization_id)
        }
        
        if self.context.project_id:
            scoped_filters['project_id'] = str(self.context.project_id)
        
        # If base adapter supports search
        if hasattr(self.base_adapter, 'search'):
            return await self.base_adapter.search(collection, query, scoped_filters, limit)
        else:
            # Fallback to basic filtering
            logger.warning(f"Base adapter does not support search, using basic list filtering")
            all_results = await self.list(collection, scoped_filters, limit=limit)
            
            # Simple text search in results
            query_lower = query.lower()
            filtered = []
            for doc in all_results:
                # Search in string values
                for key, value in doc.items():
                    if isinstance(value, str) and query_lower in value.lower():
                        filtered.append(doc)
                        break
            
            return filtered[:limit]
    
    def get_context_info(self) -> Dict[str, Any]:
        """Get information about the current context"""
        return {
            'organization_id': str(self.context.organization_id),
            'project_id': str(self.context.project_id) if self.context.project_id else None,
            'user_id': str(self.context.user_id),
            'role': self.context.role.value,
            'permissions': [p.value for p in self.context.permissions]
        }