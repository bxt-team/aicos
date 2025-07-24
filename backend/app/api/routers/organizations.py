"""
Organization management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging
import traceback

from app.core.supabase_auth import get_current_user
from app.models.auth import Permission, OrganizationRole
from app.core.dependencies import get_supabase_client

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
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
        logger.info(f"Listing organizations for user: {current_user['user_id']}")
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # First, get the public user ID from the Supabase auth user email
        auth_email = current_user.get("email")
        public_user_id = str(current_user["user_id"])
        
        # If we have an email, try to find the corresponding public user
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
                logger.info(f"Mapped auth user {current_user['user_id']} to public user {public_user_id}")
        
        # Get user's organization memberships from database with joined organization data
        # Exclude soft-deleted organizations
        result = supabase.table("organization_members").select(
            "role, created_at, organizations!inner(*)"
        ).eq("user_id", public_user_id).is_("organizations.deleted_at", "null").execute()
        
        logger.info(f"Organization memberships query result: {result.data}")
        
        organizations = []
        for membership in result.data:
            if membership.get("organizations"):
                org = membership["organizations"]
                organizations.append({
                    "id": org["id"],
                    "name": org["name"],
                    "description": org.get("description"),
                    "website": org.get("website"),
                    "subscription_tier": org.get("subscription_tier", "free"),
                    "owner_id": org.get("created_by"),  # created_by is the owner_id
                    "role": membership["role"],
                    "created_at": org["created_at"],
                    "updated_at": org.get("updated_at", org["created_at"])
                })
        
        logger.info(f"Returning {len(organizations)} organizations for user {current_user['user_id']}")
        
        return {
            "success": True,
            "organizations": organizations,
            "count": len(organizations)
        }
    except Exception as e:
        logger.error(f"Error listing organizations: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_organization(
    request: OrganizationCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new organization"""
    logger.info(f"Creating organization: {request.name} for user: {current_user}")
    
    try:
        from uuid import uuid4
        import re
        import random
        
        logger.debug("Getting Supabase client")
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            logger.error("Database connection not available")
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Ensure user exists in users table
        auth_user_id = str(current_user["user_id"])
        user_email = current_user.get("email", "")
        logger.debug(f"Auth User ID: {auth_user_id}, Email: {user_email}")
        
        # First check if user exists by email (this handles both old and new auth systems)
        if user_email:
            email_result = supabase.table("users").select("id").eq("email", user_email).execute()
            if email_result.data:
                # User exists, use their ID
                user_id = email_result.data[0]["id"]
                logger.info(f"Found existing user by email: {user_id}")
            else:
                # Create new user with auth user ID
                user_id = auth_user_id
                user_data = {
                    "id": user_id,
                    "email": user_email,
                    "name": user_email.split('@')[0] if user_email else "User",
                    "auth_provider": "supabase",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                supabase.table("users").insert(user_data).execute()
                logger.info(f"Created new user: {user_id}")
        else:
            # No email, just use auth user ID
            user_id = auth_user_id
        
        # Create organization with unique slug
        org_id = str(uuid4())
        base_slug = re.sub(r'[^a-z0-9-]', '-', request.name.lower()).strip('-')
        logger.debug(f"Generated org_id: {org_id}, base_slug: {base_slug}")
        
        # Ensure slug is unique by adding random suffix if needed
        slug = base_slug
        counter = 0
        while True:
            logger.debug(f"Checking if slug '{slug}' exists")
            existing = supabase.table("organizations").select("id").eq("slug", slug).execute()
            if not existing.data:
                logger.debug(f"Slug '{slug}' is unique")
                break
            counter += 1
            # Add random 4-character suffix
            random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=4))
            slug = f"{base_slug}-{random_suffix}"
            logger.debug(f"Slug exists, trying new slug: {slug}")
        
        org_data = {
            "id": org_id,
            "name": request.name,
            "slug": slug,
            "description": request.description,
            "website": request.website,
            "subscription_tier": request.subscription_tier or "free",
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Creating organization with data: {org_data}")
        
        try:
            supabase.table("organizations").insert(org_data).execute()
            logger.info("Organization created successfully")
        except Exception as e:
            logger.error(f"Failed to create organization: {str(e)}")
            raise
        
        # Add user as owner
        membership_data = {
            "id": str(uuid4()),
            "organization_id": org_id,
            "user_id": user_id,
            "role": "owner",
            "accepted_at": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Adding user as organization owner: {membership_data}")
        
        try:
            supabase.table("organization_members").insert(membership_data).execute()
            logger.info("User added as organization owner")
        except Exception as e:
            logger.error(f"Failed to add user as organization member: {str(e)}")
            raise
        
        # Create default project with slug
        project_id = str(uuid4())
        project_slug = "default-project"
        
        # Ensure project slug is unique within organization
        counter = 0
        while True:
            existing = supabase.table("projects").select("id").eq("slug", project_slug).eq("organization_id", org_id).execute()
            if not existing.data:
                break
            counter += 1
            project_slug = f"default-project-{counter}"
        
        project_data = {
            "id": project_id,
            "organization_id": org_id,
            "name": "Default Project",
            "slug": project_slug,
            "description": "Your first project - feel free to rename or create additional projects",
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        try:
            supabase.table("projects").insert(project_data).execute()
            logger.info("Default project created successfully")
        except Exception as e:
            logger.error(f"Failed to create default project: {str(e)}")
            raise
        
        # Add user as project admin
        project_membership_data = {
            "id": str(uuid4()),
            "project_id": project_id,
            "user_id": user_id,
            "role": "admin",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        logger.info(f"Adding user as project admin: {project_membership_data}")
        
        try:
            supabase.table("project_members").insert(project_membership_data).execute()
            logger.info("User added as project admin")
        except Exception as e:
            logger.error(f"Failed to add user as project member: {str(e)}")
            raise
        
        return {
            "success": True,
            "organization": {
                "id": org_id,
                "name": request.name,
                "slug": slug,
                "description": request.description,
                "website": request.website,
                "subscription_tier": request.subscription_tier or "free",
                "owner_id": user_id,
                "created_at": org_data["created_at"],
                "updated_at": org_data["updated_at"]
            },
            "message": "Organization created successfully"
        }
    except HTTPException:
        # Re-raise HTTP exceptions as they are
        raise
    except Exception as e:
        logger.error(f"Failed to create organization: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return detailed error in development
        raise HTTPException(
            status_code=500, 
            detail={
                "error": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc().split('\n')
            }
        )

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
        result = supabase.table("organizations").select("*").eq("id", organization_id).is_("deleted_at", "null").single().execute()
        
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
    try:
        logger.info(f"Deleting organization {organization_id} by user {current_user['user_id']}")
        
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Get the public user ID
        auth_email = current_user.get("email")
        public_user_id = str(current_user["user_id"])
        
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
        
        # Check if user is owner of this organization
        membership_result = supabase.table("organization_members").select("role").eq(
            "organization_id", organization_id
        ).eq("user_id", public_user_id).execute()
        
        if not membership_result.data:
            raise HTTPException(status_code=403, detail="You are not a member of this organization")
        
        if membership_result.data[0]["role"] != "owner":
            raise HTTPException(status_code=403, detail="Only organization owners can delete the organization")
        
        # Check if there are other owners
        other_owners = supabase.table("organization_members").select("id").eq(
            "organization_id", organization_id
        ).eq("role", "owner").neq("user_id", public_user_id).execute()
        
        if other_owners.data:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete organization with multiple owners. Transfer ownership first."
            )
        
        # Check if organization exists and is not already deleted
        org_result = supabase.table("organizations").select("id, name, deleted_at").eq(
            "id", organization_id
        ).execute()
        
        if not org_result.data:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if org_result.data[0].get("deleted_at"):
            raise HTTPException(status_code=400, detail="Organization is already deleted")
        
        # Get count of active projects
        projects_result = supabase.table("projects").select("id").eq(
            "organization_id", organization_id
        ).is_("deleted_at", "null").execute()
        
        active_projects_count = len(projects_result.data) if projects_result.data else 0
        
        # Perform soft delete by setting deleted_at timestamp
        delete_result = supabase.table("organizations").update({
            "deleted_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", organization_id).execute()
        
        if not delete_result.data:
            raise HTTPException(status_code=500, detail="Failed to delete organization")
        
        # Log the deletion in audit logs if the table exists
        try:
            audit_data = {
                "event_type": "organization.deleted",
                "organization_id": organization_id,
                "user_id": public_user_id,
                "metadata": {
                    "organization_name": org_result.data[0]["name"],
                    "active_projects_count": active_projects_count
                }
            }
            supabase.table("audit_logs").insert(audit_data).execute()
        except Exception as e:
            # Log error but don't fail the operation
            logger.warning(f"Failed to create audit log: {str(e)}")
        
        return {
            "success": True,
            "message": "Organization deleted successfully",
            "organization": {
                "id": organization_id,
                "name": org_result.data[0]["name"],
                "deleted_at": delete_result.data[0]["deleted_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete organization: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{organization_id}/restore")
async def restore_organization(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Restore a soft-deleted organization (requires owner permission)"""
    try:
        logger.info(f"Restoring organization {organization_id} by user {current_user['user_id']}")
        
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Get the public user ID
        auth_email = current_user.get("email")
        public_user_id = str(current_user["user_id"])
        
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
        
        # Check if organization exists and is deleted
        org_result = supabase.table("organizations").select("id, name, deleted_at").eq(
            "id", organization_id
        ).execute()
        
        if not org_result.data:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        if not org_result.data[0].get("deleted_at"):
            raise HTTPException(status_code=400, detail="Organization is not deleted")
        
        # Check if user was an owner of this organization
        membership_result = supabase.table("organization_members").select("role").eq(
            "organization_id", organization_id
        ).eq("user_id", public_user_id).eq("role", "owner").execute()
        
        if not membership_result.data:
            raise HTTPException(status_code=403, detail="Only former organization owners can restore the organization")
        
        # Restore organization by clearing deleted_at
        restore_result = supabase.table("organizations").update({
            "deleted_at": None,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", organization_id).execute()
        
        if not restore_result.data:
            raise HTTPException(status_code=500, detail="Failed to restore organization")
        
        # Log the restoration in audit logs
        try:
            audit_data = {
                "event_type": "organization.restored",
                "organization_id": organization_id,
                "user_id": public_user_id,
                "metadata": {
                    "organization_name": org_result.data[0]["name"]
                }
            }
            supabase.table("audit_logs").insert(audit_data).execute()
        except Exception as e:
            logger.warning(f"Failed to create audit log: {str(e)}")
        
        return {
            "success": True,
            "message": "Organization restored successfully",
            "organization": {
                "id": organization_id,
                "name": org_result.data[0]["name"],
                "updated_at": restore_result.data[0]["updated_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to restore organization: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

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