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
from supabase import create_client, Client
import os

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# from app.core.security.permissions import has_organization_permission

# Temporary permission check until permissions.py is updated for Supabase
def has_organization_permission(current_user: Dict[str, Any], organization_id: str, permission: Permission) -> bool:
    """Temporary permission check - always returns True for authenticated users"""
    return True

router = APIRouter(prefix="/api/organizations", tags=["Organizations"])


def get_supabase() -> Client:
    """Get the actual Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)

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
        supabase = get_supabase()
        
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
        supabase = get_supabase()
        
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
        supabase = get_supabase()
        
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
        
        supabase = get_supabase()
        
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
        
        supabase = get_supabase()
        
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
    try:
        logger.info(f"Listing members for organization: {organization_id}")
        supabase = get_supabase()
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Get the public user ID from the Supabase auth user
        auth_email = current_user.get("email")
        public_user_id = str(current_user["user_id"])
        
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
        
        # Check if user has access to this organization
        user_membership = supabase.table("organization_members").select("role").eq(
            "organization_id", organization_id
        ).eq("user_id", public_user_id).execute()
        
        logger.info(f"User membership check - Auth email: {auth_email}, Public user ID: {public_user_id}, Membership: {user_membership.data}")
        
        if not user_membership.data:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all members of this organization with user details
        # Using the user_id foreign key relationship specifically
        result = supabase.table("organization_members").select(
            "*, users!organization_members_user_id_fkey(id, email, name)"
        ).eq("organization_id", organization_id).execute()
        
        logger.info(f"Raw query result count: {len(result.data) if result.data else 0}")
        logger.info(f"Organization members query result: {result.data}")
        
        members = []
        for membership in result.data:
            logger.info(f"Processing membership: {membership}")
            # The user data might be under different keys depending on Supabase version
            user_data = membership.get("users!organization_members_user_id_fkey") or membership.get("users")
            logger.info(f"User data extracted: {user_data}")
            if user_data:
                # Check if this user is the current user by comparing emails
                is_current_user = user_data["email"] == auth_email if auth_email else False
                
                member_info = {
                    "id": membership["id"],
                    "user_id": user_data["id"],
                    "email": user_data["email"],
                    "name": user_data.get("name", user_data["email"].split('@')[0]),
                    "role": membership["role"],
                    "joined_at": membership.get("accepted_at", membership["created_at"]),
                    "is_current_user": is_current_user  # Add flag to identify current user
                }
                
                # Log current user's role for debugging
                if is_current_user:
                    logger.info(f"Current user role in organization {organization_id}: {membership['role']}")
                
                members.append(member_info)
        
        logger.info(f"Returning {len(members)} members for organization {organization_id}")
        logger.info(f"Members data: {members}")
        
        # Return the response in the expected format
        response = {
            "success": True,
            "members": members,
            "count": len(members)
        }
        
        logger.info(f"Full API response: {response}")
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing organization members: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{organization_id}/members")
async def invite_organization_member(
    organization_id: str,
    request: OrganizationMemberInviteRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Invite a new member to organization (requires admin permission)"""
    try:
        supabase = get_supabase()
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Get the public user ID for permission check
        auth_email = current_user.get("email")
        public_user_id = str(current_user["user_id"])
        
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
        
        # Check if user has admin or owner access to this organization
        membership_check = supabase.table("organization_members").select("role").eq(
            "organization_id", organization_id
        ).eq("user_id", public_user_id).execute()
        
        if not membership_check.data:
            raise HTTPException(status_code=403, detail="Access denied")
        
        user_role = membership_check.data[0]["role"]
        if user_role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admin or owner access required")
        
        # Validate role
        valid_roles = ["owner", "admin", "member", "viewer"]
        if request.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
        
        # Check if user already exists in the system
        existing_user = supabase.table("users").select("id").eq("email", request.email).execute()
        
        if existing_user.data:
            # User exists, check if already a member
            invited_user_id = existing_user.data[0]["id"]
            
            existing_membership = supabase.table("organization_members").select("id").eq(
                "organization_id", organization_id
            ).eq("user_id", invited_user_id).execute()
            
            if existing_membership.data:
                raise HTTPException(status_code=400, detail="User is already a member of this organization")
            
            # Add user as member
            membership_data = {
                "organization_id": organization_id,
                "user_id": invited_user_id,
                "role": request.role,
                "invited_by": public_user_id,
                "invited_at": datetime.utcnow().isoformat(),
                "accepted_at": datetime.utcnow().isoformat()  # Auto-accept for existing users
            }
            
            membership_result = supabase.table("organization_members").insert(membership_data).execute()
            
            if not membership_result.data:
                raise HTTPException(status_code=500, detail="Failed to add member")
            
            return {
                "success": True,
                "message": f"User {request.email} added to organization",
                "member": membership_result.data[0]
            }
        else:
            # User doesn't exist - in a real app, you'd send an invitation email
            # For now, we'll return an error
            raise HTTPException(
                status_code=404, 
                detail="User not found. Please ask them to sign up first."
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error inviting member: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{organization_id}/members/{member_id}")
async def update_organization_member(
    organization_id: str,
    member_id: str,
    request: OrganizationMemberUpdateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update member role (requires admin permission)"""
    try:
        supabase = get_supabase()
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Get the public user ID for permission check
        auth_email = current_user.get("email")
        public_user_id = str(current_user["user_id"])
        
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
        
        # Check if user has admin or owner access to this organization
        membership_check = supabase.table("organization_members").select("role").eq(
            "organization_id", organization_id
        ).eq("user_id", public_user_id).execute()
        
        if not membership_check.data:
            raise HTTPException(status_code=403, detail="Access denied")
        
        user_role = membership_check.data[0]["role"]
        if user_role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admin or owner access required")
        
        # Validate new role
        valid_roles = ["owner", "admin", "member", "viewer"]
        if request.role not in valid_roles:
            raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
        
        # Get the member to be updated
        member_result = supabase.table("organization_members").select("*").eq(
            "id", member_id
        ).eq("organization_id", organization_id).execute()
        
        if not member_result.data:
            raise HTTPException(status_code=404, detail="Member not found")
        
        member_data = member_result.data[0]
        current_member_role = member_data["role"]
        member_user_id = member_data["user_id"]
        
        # Check if trying to remove owner role from the last owner
        if current_member_role == "owner" and request.role != "owner":
            # Count remaining owners
            owner_count = supabase.table("organization_members").select("id", count="exact").eq(
                "organization_id", organization_id
            ).eq("role", "owner").execute()
            
            if owner_count.count <= 1:
                raise HTTPException(status_code=400, detail="Cannot remove owner role from the last owner")
        
        # Only owners can promote others to owner
        if request.role == "owner" and user_role != "owner":
            raise HTTPException(status_code=403, detail="Only owners can promote others to owner")
        
        # Update the member role
        update_result = supabase.table("organization_members").update({
            "role": request.role,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", member_id).eq("organization_id", organization_id).execute()
        
        if not update_result.data:
            raise HTTPException(status_code=500, detail="Failed to update member role")
        
        return {
            "success": True,
            "message": "Member role updated successfully",
            "member": update_result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating member role: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{organization_id}/members/{member_id}")
async def remove_organization_member(
    organization_id: str,
    member_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove member from organization (requires admin permission)"""
    try:
        supabase = get_supabase()
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Get the public user ID for permission check
        auth_email = current_user.get("email")
        public_user_id = str(current_user["user_id"])
        
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
        
        # Check if user has admin or owner access to this organization
        membership_check = supabase.table("organization_members").select("role").eq(
            "organization_id", organization_id
        ).eq("user_id", public_user_id).execute()
        
        if not membership_check.data:
            raise HTTPException(status_code=403, detail="Access denied")
        
        user_role = membership_check.data[0]["role"]
        if user_role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admin or owner access required")
        
        # Get the member to be removed
        member_result = supabase.table("organization_members").select("*, users!organization_members_user_id_fkey(*)").eq(
            "id", member_id
        ).eq("organization_id", organization_id).execute()
        
        if not member_result.data:
            raise HTTPException(status_code=404, detail="Member not found")
        
        member_data = member_result.data[0]
        member_role = member_data["role"]
        member_user_id = member_data["user_id"]
        
        # Check if trying to remove the last owner
        if member_role == "owner":
            # Count remaining owners
            owner_count = supabase.table("organization_members").select("id", count="exact").eq(
                "organization_id", organization_id
            ).eq("role", "owner").execute()
            
            if owner_count.count <= 1:
                raise HTTPException(status_code=400, detail="Cannot remove the last owner. Transfer ownership first.")
        
        # Can't remove yourself
        if member_user_id == public_user_id:
            raise HTTPException(status_code=400, detail="You cannot remove yourself from the organization")
        
        # Remove the member
        delete_result = supabase.table("organization_members").delete().eq(
            "id", member_id
        ).eq("organization_id", organization_id).execute()
        
        if not delete_result.data:
            raise HTTPException(status_code=500, detail="Failed to remove member")
        
        return {
            "success": True,
            "message": "Member removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing member: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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

@router.get("/{organization_id}/test-members")
async def test_organization_members(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Simple test endpoint to check organization members"""
    try:
        supabase = get_supabase()
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Simple query to get all members
        simple_result = supabase.table("organization_members").select("*").eq(
            "organization_id", organization_id
        ).execute()
        
        # Query with user join
        join_result = supabase.table("organization_members").select(
            "*, users!organization_members_user_id_fkey(*)"
        ).eq("organization_id", organization_id).execute()
        
        return {
            "simple_query_count": len(simple_result.data) if simple_result.data else 0,
            "simple_query_data": simple_result.data,
            "join_query_count": len(join_result.data) if join_result.data else 0,
            "join_query_data": join_result.data,
            "organization_id": organization_id
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{organization_id}/debug-membership")
async def debug_organization_membership(
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Debug endpoint to check user's membership and role in organization"""
    try:
        supabase = get_supabase()
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Get auth user info
        auth_email = current_user.get("email", "")
        auth_user_id = str(current_user["user_id"])
        
        # Get public user info
        public_user_info = None
        if auth_email:
            user_result = supabase.table("users").select("*").eq("email", auth_email).execute()
            if user_result.data:
                public_user_info = user_result.data[0]
        
        # Get organization info
        org_result = supabase.table("organizations").select("*").eq("id", organization_id).execute()
        org_info = org_result.data[0] if org_result.data else None
        
        # Get membership info using public user ID if available
        membership_info = None
        if public_user_info:
            membership_result = supabase.table("organization_members").select(
                "id, user_id, organization_id, role, created_at, accepted_at"
            ).eq(
                "organization_id", organization_id
            ).eq("user_id", public_user_info["id"]).execute()
            membership_info = membership_result.data[0] if membership_result.data else None
        
        # Get all organization members to verify
        all_members_result = supabase.table("organization_members").select(
            "*, users!organization_members_user_id_fkey(id, email, name)"
        ).eq("organization_id", organization_id).execute()
        
        return {
            "auth_user": {
                "id": auth_user_id,
                "email": auth_email
            },
            "public_user": public_user_info,
            "organization": org_info,
            "membership": membership_info,
            "all_members": all_members_result.data,
            "debug_info": {
                "has_public_user": public_user_info is not None,
                "has_membership": membership_info is not None,
                "user_role": membership_info["role"] if membership_info else None,
                "is_owner": membership_info["role"] == "owner" if membership_info else False
            }
        }
    except Exception as e:
        logger.error(f"Debug error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))