"""Base storage adapter interface"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


class StorageAdapter(ABC):
    """Abstract base class for storage adapters"""
    
    @abstractmethod
    async def save(self, 
                   collection: str, 
                   data: Dict[str, Any], 
                   id: Optional[str] = None) -> str:
        """
        Save data to storage and return ID
        
        Args:
            collection: Name of the collection/table
            data: Data to save
            id: Optional ID (will generate if not provided)
            
        Returns:
            str: The ID of the saved item
        """
        pass
    
    @abstractmethod
    async def load(self, 
                   collection: str, 
                   id: str) -> Optional[Dict[str, Any]]:
        """
        Load single item by ID
        
        Args:
            collection: Name of the collection/table
            id: ID of the item to load
            
        Returns:
            Optional[Dict]: The item if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def list(self, 
                   collection: str, 
                   filters: Optional[Dict] = None,
                   limit: Optional[int] = None,
                   offset: Optional[int] = None,
                   order_by: Optional[str] = None,
                   order_desc: bool = False) -> List[Dict[str, Any]]:
        """
        List items with optional filtering
        
        Args:
            collection: Name of the collection/table
            filters: Optional filters to apply
            limit: Maximum number of items to return
            offset: Number of items to skip
            order_by: Field to order by
            order_desc: Whether to order descending
            
        Returns:
            List[Dict]: List of items matching the criteria
        """
        pass
    
    @abstractmethod
    async def update(self, 
                     collection: str, 
                     id: str, 
                     data: Dict[str, Any]) -> bool:
        """
        Update existing item
        
        Args:
            collection: Name of the collection/table
            id: ID of the item to update
            data: New data (will be merged with existing)
            
        Returns:
            bool: True if updated successfully
        """
        pass
    
    @abstractmethod
    async def delete(self, 
                     collection: str, 
                     id: str) -> bool:
        """
        Delete item by ID
        
        Args:
            collection: Name of the collection/table
            id: ID of the item to delete
            
        Returns:
            bool: True if deleted successfully
        """
        pass
    
    @abstractmethod
    async def count(self, 
                    collection: str, 
                    filters: Optional[Dict] = None) -> int:
        """
        Count items in collection
        
        Args:
            collection: Name of the collection/table
            filters: Optional filters to apply
            
        Returns:
            int: Number of items matching the criteria
        """
        pass
    
    @abstractmethod
    async def exists(self, 
                     collection: str, 
                     id: str) -> bool:
        """
        Check if item exists
        
        Args:
            collection: Name of the collection/table
            id: ID of the item to check
            
        Returns:
            bool: True if item exists
        """
        pass
    
    @abstractmethod
    async def clear(self, collection: str) -> bool:
        """
        Clear all items in collection (use with caution!)
        
        Args:
            collection: Name of the collection/table
            
        Returns:
            bool: True if cleared successfully
        """
        pass