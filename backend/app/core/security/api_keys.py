"""
API Key management for programmatic access
"""
import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.core.dependencies import get_supabase_client


class APIKeyManager:
    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate API key and its hash"""
        key = f"7c_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return key, key_hash
    
    @staticmethod
    async def validate_api_key(key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return permissions"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            return None
            
        # Look up in database
        result = supabase.table("api_keys").select("*").eq("key_hash", key_hash).eq("revoked_at", None).single().execute()
        
        if not result.data:
            return None
        
        api_key_record = result.data
        
        # Check expiration
        if api_key_record.get('expires_at'):
            expires_at = datetime.fromisoformat(api_key_record['expires_at'].replace('Z', '+00:00'))
            if expires_at < datetime.utcnow():
                return None
        
        # Update last used
        if supabase:
            supabase.table("api_keys").update({
                "last_used_at": datetime.utcnow().isoformat()
            }).eq("id", api_key_record['id']).execute()
        
        return {
            'organization_id': api_key_record['organization_id'],
            'project_id': api_key_record.get('project_id'),
            'permissions': api_key_record.get('permissions', {})
        }
    
    @staticmethod
    async def create_api_key(
        organization_id: UUID,
        name: str,
        created_by: UUID,
        project_id: Optional[UUID] = None,
        expires_in_days: Optional[int] = None,
        permissions: Optional[Dict[str, Any]] = None
    ) -> tuple[str, Dict[str, Any]]:
        """Create a new API key"""
        key, key_hash = APIKeyManager.generate_api_key()
        key_prefix = key[:12]
        
        expires_at = None
        if expires_in_days:
            expires_at = (datetime.utcnow() + timedelta(days=expires_in_days)).isoformat()
        
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            raise Exception("Database connection not available")
            
        # Insert into database
        result = supabase.table("api_keys").insert({
            "organization_id": str(organization_id),
            "project_id": str(project_id) if project_id else None,
            "name": name,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "permissions": permissions or {},
            "expires_at": expires_at,
            "created_by": str(created_by)
        }).execute()
        
        return key, result.data[0]
    
    @staticmethod
    async def revoke_api_key(key_id: UUID, user_id: UUID) -> bool:
        """Revoke an API key"""
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            return False
            
        # Check if user has permission to revoke
        # (This would normally check organization membership)
        
        result = supabase.table("api_keys").update({
            "revoked_at": datetime.utcnow().isoformat()
        }).eq("id", str(key_id)).execute()
        
        return bool(result.data)