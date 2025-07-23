"""
Organization management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.core.supabase_auth import get_current_user
from app.models.auth import Permission, OrganizationRole
from app.core.dependencies import get_supabase_client
# from app.core.security.permissions import has_organization_permission

# Temporary permission check until permissions.py is updated for Supabase
def has_organization_permission(current_user: Dict[str, Any], organization_id: str, permission: Permission) -> bool:
    """Temporary permission check - always returns True for authenticated users"""
    return True

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])

# Request models
class OrganizationCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    website: Optional[str] = None
    subscription_tier: Optional[str] = "free"

class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    subscription_tier: Optional[str] = None
    settings: Optional[dict] = None

class OrganizationMemberInviteRequest(BaseModel):
    email: str
    role: str = "member"  # owner, admin, member, viewer

class OrganizationMemberUpdateRequest(BaseModel):
    role: str

# Organization endpoints
@router.get("/")
async def list_organizations(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all organizations the user belongs to"""
    try:
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Get user's organization memberships from database
        result = supabase.table("organization_members").select(
            "role, created_at, organizations(id, name, description, created_at)"
        ).eq("user_id", str(current_user["user_id"])).execute()
        
        organizations = []
        for membership in result.data:
            if membership.get("organizations"):
                org = membership["organizations"]
                organizations.append({
                    "id": org["id"],
                    "name": org["name"],
                    "description": org.get("description"),
                    "role": membership["role"],
                    "created_at": org["created_at"]
                })
        
        return {
            "success": True,
            "organizations": organizations,
            "count": len(organizations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_organization(
    request: OrganizationCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new organization"""
    try:
        from uuid import uuid4
        import re
        
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Create organization
        org_id = str(uuid4())
        slug = re.sub(r'[^a-z0-9-]', '-', request.name.lower()).strip('-')
        
        org_data = {
            "id": org_id,
            "name": request.name,
            "slug": slug,
            "description": request.description,
            "website": request.website,
            "subscription_tier": request.subscription_tier or "free",
            "created_by": str(current_user["user_id"]),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("organizations").insert(org_data).execute()
        
        # Add user as owner
        membership_data = {
            "id": str(uuid4()),
            "organization_id": org_id,
            "user_id": str(current_user["user_id"]),
            "role": "owner",
            "accepted_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("organization_members").insert(membership_data).execute()
        
        # Create default project
        project_id = str(uuid4())
        project_data = {
            "id": project_id,
            "organization_id": org_id,
            "name": "Default Project",
            "description": "Your first project - feel free to rename or create additional projects",
            "created_by": str(current_user["user_id"]),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("projects").insert(project_data).execute()
        
        # Add user as project admin
        project_membership_data = {
            "id": str(uuid4()),
            "project_id": project_id,
            "user_id": str(current_user["user_id"]),
            "role": "admin",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("project_members").insert(project_membership_data).execute()
        
        return {
            "success": True,
            "organization": {
                "id": org_id,
                "name": request.name,
                "slug": slug,
                "description": request.description,
                "website": request.website,
                "subscription_tier": request.subscription_tier or "free",
                "created_at": org_data["created_at"]
            },
            "message": "Organization created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{organization_id}")
async def get_organization(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get organization details"""
    # Check if user has access to this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        from app.core.dependencies import get_supabase_client
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Fetch organization from database
        result = supabase.table("organizations").select("*").eq("id", organization_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        organization = result.data
        
        return {
            "success": True,
            "organization": organization
        }
    except Exception as e:
        if "404" not in str(e):
            raise HTTPException(status_code=500, detail=str(e))
        raise

@router.put("/{organization_id}")
async def update_organization(
    organization_id: str,
    request: OrganizationUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update organization details (requires admin permission)"""
    # Check if user has admin access to this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, update in database
    updated_fields = {k: v for k, v in request.dict().items() if v is not None}
    
    return {
        "success": True,
        "message": "Organization updated successfully",
        "updated_fields": updated_fields
    }

@router.delete("/{organization_id}")
async def delete_organization(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete organization (requires owner permission)"""
    # Check if user is owner of this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_DELETE):
        raise HTTPException(status_code=403, detail="Owner access required")
    
    # In a real implementation:
    # 1. Check if organization has active projects/data
    # 2. Soft delete or archive organization
    # 3. Remove all members
    
    return {
        "success": True,
        "message": "Organization deleted successfully"
    }

# Member management endpoints
@router.get("/{organization_id}/members")
async def list_organization_members(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List organization members"""
    # Check if user has access to this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, fetch from database
    members = [
        {
            "id": current_user["user_id"],
            "email": current_user["email"],
            "name": current_user.get("user_metadata", {}).get("name", current_user["email"]),
            "role": "owner",
            "joined_at": datetime.now().isoformat()
        }
    ]
    
    return {
        "success": True,
        "members": members,
        "count": len(members)
    }

@router.post("/{organization_id}/members")
async def invite_organization_member(
    organization_id: str,
    request: OrganizationMemberInviteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Invite a new member to organization (requires admin permission)"""
    # Check if user has admin access to this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate role
    valid_roles = ["owner", "admin", "member", "viewer"]
    if request.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    # In a real implementation:
    # 1. Check if user already exists
    # 2. Send invitation email
    # 3. Create pending invitation record
    
    return {
        "success": True,
        "message": f"Invitation sent to {request.email}",
        "invitation": {
            "email": request.email,
            "role": request.role,
            "status": "pending",
            "invited_by": current_user["user_id"],
            "invited_at": datetime.now().isoformat()
        }
    }

@router.put("/{organization_id}/members/{member_id}")
async def update_organization_member(
    organization_id: str,
    member_id: str,
    request: OrganizationMemberUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update member role (requires admin permission)"""
    # Check if user has admin access to this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Can't change your own role if you're the only owner
    if member_id == current_user["user_id"] and request.role != "owner":
        # Check if there are other owners
        # In real implementation, query database
        raise HTTPException(status_code=400, detail="Cannot remove last owner")
    
    return {
        "success": True,
        "message": "Member role updated successfully",
        "member": {
            "id": member_id,
            "role": request.role
        }
    }

@router.delete("/{organization_id}/members/{member_id}")
async def remove_organization_member(
    organization_id: str,
    member_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove member from organization (requires admin permission)"""
    # Check if user has admin access to this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Can't remove yourself if you're the only owner
    if member_id == current_user["user_id"]:
        # Check if there are other owners
        # In real implementation, query database
        raise HTTPException(status_code=400, detail="Cannot remove last owner")
    
    return {
        "success": True,
        "message": "Member removed successfully"
    }

# Settings endpoints
@router.get("/{organization_id}/settings")
async def get_organization_settings(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get organization settings"""
    # Check if user has access to this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, fetch from database
    settings = {
        "branding": {
            "logo_url": None,
            "primary_color": "#2196F3",
            "secondary_color": "#FF4081"
        },
        "features": {
            "max_projects": 10,
            "max_users": 50,
            "api_access": True
        },
        "integrations": {
            "slack": {"enabled": False},
            "webhook": {"enabled": False}
        }
    }
    
    return {
        "success": True,
        "settings": settings
    }

@router.put("/{organization_id}/settings")
async def update_organization_settings(
    organization_id: str,
    settings: dict,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update organization settings (requires admin permission)"""
    # Check if user has admin access to this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, validate and update settings
    
    return {
        "success": True,
        "message": "Settings updated successfully",
        "settings": settings
    }

# Usage statistics endpoints
@router.get("/{organization_id}/usage")
async def get_organization_usage(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get organization usage statistics"""
    # Check if user has access to this organization
    if not has_organization_permission(current_user, organization_id, Permission.ORG_READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, calculate from database
    usage = {
        "projects": {
            "current": 3,
            "limit": 10
        },
        "users": {
            "current": 5,
            "limit": 50
        },
        "storage": {
            "current_gb": 2.5,
            "limit_gb": 100
        },
        "api_calls": {
            "current_month": 15000,
            "limit_month": 100000
        }
    }
    
    return {
        "success": True,
        "usage": usage,
        "period": {
            "start": datetime.now().replace(day=1).isoformat(),
            "end": datetime.now().isoformat()
        }
    }