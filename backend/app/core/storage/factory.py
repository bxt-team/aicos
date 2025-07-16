"""Storage adapter factory"""

import os
from typing import Optional
from .base import StorageAdapter
from .supabase_adapter import SupabaseAdapter
from .json_adapter import JSONAdapter
from .migration import DualWriteAdapter


class StorageFactory:
    """Factory for creating storage adapters"""
    
    _instance: Optional[StorageAdapter] = None
    
    @classmethod
    def create_adapter(cls, 
                      adapter_type: Optional[str] = None,
                      **kwargs) -> StorageAdapter:
        """
        Create a storage adapter instance
        
        Args:
            adapter_type: Type of adapter ('json', 'supabase', or 'dual')
                         If not provided, uses STORAGE_ADAPTER env var
            **kwargs: Additional arguments for the adapter
            
        Returns:
            StorageAdapter instance
        """
        # Use environment variable if adapter_type not specified
        if adapter_type is None:
            adapter_type = os.getenv("STORAGE_ADAPTER", "json")
        
        if adapter_type == "supabase":
            # Get Supabase credentials from environment or kwargs
            url = kwargs.get("url") or os.getenv("SUPABASE_URL")
            key = kwargs.get("key") or os.getenv("SUPABASE_SERVICE_KEY")
            
            if not url or not key:
                raise ValueError(
                    "Supabase URL and key must be provided via kwargs or environment variables"
                )
            
            return SupabaseAdapter(url=url, key=key)
        
        elif adapter_type == "json":
            base_path = kwargs.get("base_path", "static")
            return JSONAdapter(base_path=base_path)
        
        elif adapter_type == "dual":
            # Create dual-write adapter for gradual migration
            primary_type = kwargs.get("primary", "json")
            secondary_type = kwargs.get("secondary", "supabase")
            read_from = kwargs.get("read_from") or os.getenv("DUAL_WRITE_READ_FROM", "json")
            
            # Create primary adapter
            if primary_type == "json":
                primary = JSONAdapter(base_path=kwargs.get("base_path", "static"))
            else:
                primary = SupabaseAdapter(
                    url=os.getenv("SUPABASE_URL"),
                    key=os.getenv("SUPABASE_SERVICE_KEY")
                )
            
            # Create secondary adapter
            if secondary_type == "supabase":
                secondary = SupabaseAdapter(
                    url=os.getenv("SUPABASE_URL"),
                    key=os.getenv("SUPABASE_SERVICE_KEY")
                )
            else:
                secondary = JSONAdapter(base_path=kwargs.get("base_path", "static"))
            
            return DualWriteAdapter(
                primary=primary,
                secondary=secondary,
                read_from_primary=(read_from == "json")
            )
        
        else:
            raise ValueError(f"Unknown adapter type: {adapter_type}")
    
    @classmethod
    def get_adapter(cls) -> StorageAdapter:
        """
        Get or create a singleton storage adapter instance
        Uses environment configuration
        
        Returns:
            StorageAdapter instance
        """
        if cls._instance is None:
            cls._instance = cls.create_adapter()
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset the singleton instance (useful for testing)"""
        cls._instance = None


# Convenience function
def get_storage() -> StorageAdapter:
    """Get the default storage adapter instance"""
    return StorageFactory.get_adapter()