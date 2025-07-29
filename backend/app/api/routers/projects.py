"""
Project management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

from app.core.auth import get_current_user, get_request_context
from app.models.auth import User, Permission, RequestContext
from app.core.security.permissions import has_project_permission
from app.core.supabase_auth import get_current_user as get_current_user_supabase
from supabase import create_client, Client
import os

router = APIRouter(prefix="/api/projects", tags=["Projects"])
logger = logging.getLogger(__name__)


def get_supabase() -> Client:
    """Get the actual Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)

# Request models
class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: str
    settings: Optional[dict] = None
    department_ids: Optional[List[str]] = None  # Departments to share with

class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None
    is_active: Optional[bool] = None

class ProjectMemberAddRequest(BaseModel):
    user_id: str
    role: str = "member"  # admin, member, viewer

class ProjectDepartmentRequest(BaseModel):
    department_id: str

# Project endpoints
@router.get("/")
async def list_projects(
    organization_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """List all projects the user has access to"""
    try:
        supabase = get_supabase()
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Map Supabase auth user to public user
        auth_email = current_user.get("email")
        public_user_id = str(current_user["user_id"])
        
        # If we have an email, try to find the corresponding public user
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
                logger.info(f"Mapped auth user {current_user['user_id']} to public user {public_user_id}")
        
        # Get projects the user has access to
        if organization_id:
            # Get projects for specific organization
            # First check if user has access to this organization
            org_check = supabase.table("organization_members").select("role").eq(
                "user_id", public_user_id
            ).eq("organization_id", organization_id).execute()
            
            if not org_check.data:
                raise HTTPException(status_code=403, detail="Access denied to this organization")
            
            # Get all projects for the organization with user's membership info in a single query
            # First get all project IDs for this organization
            project_result = supabase.table("projects").select("*").eq(
                "organization_id", organization_id
            ).execute()
            
            if not project_result.data:
                projects = []
            else:
                # Get all project IDs
                project_ids = [p["id"] for p in project_result.data]
                
                # Get all user's memberships for these projects in one query
                membership_result = supabase.table("project_members").select("project_id, role").eq(
                    "user_id", public_user_id
                ).in_("project_id", project_ids).execute()
                
                # Create a map of project_id to role for quick lookup
                membership_map = {m["project_id"]: m["role"] for m in membership_result.data}
                
                # Build the projects list with membership info
                projects = []
                for project in project_result.data:
                    projects.append({
                        "id": project["id"],
                        "name": project["name"],
                        "description": project.get("description"),
                        "organization_id": project["organization_id"],
                        "created_at": project["created_at"],
                        "is_active": project.get("is_active", True),
                        "role": membership_map.get(project["id"])  # O(1) lookup instead of query
                    })
        else:
            # Get all projects user has access to
            result = supabase.table("project_members").select(
                "role, projects(id, name, description, organization_id, created_at, is_active)"
            ).eq("user_id", public_user_id).execute()
            
            projects = []
            for membership in result.data:
                if membership.get("projects"):
                    project = membership["projects"]
                    projects.append({
                        "id": project["id"],
                        "name": project["name"],
                        "description": project.get("description"),
                        "organization_id": project["organization_id"],
                        "created_at": project["created_at"],
                        "is_active": project.get("is_active", True),
                        "role": membership["role"]
                    })
        
        return {
            "success": True,
            "projects": projects,
            "count": len(projects)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_project(
    request: ProjectCreateRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Create a new project within an organization"""
    try:
        from uuid import uuid4
        import re
        import random
        
        supabase = get_supabase()
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Ensure user exists in users table
        user_id = str(current_user["user_id"])
        user_email = current_user.get("email", "")
        
        # Check if user exists in users table by ID first
        user_result = supabase.table("users").select("id").eq("id", user_id).execute()
        
        if not user_result.data and user_email:
            # Check if user exists by email
            email_result = supabase.table("users").select("id").eq("email", user_email).execute()
            if email_result.data:
                # User exists with different ID, use existing user
                user_id = email_result.data[0]["id"]
            else:
                # Create new user
                user_data = {
                    "id": user_id,
                    "email": user_email,
                    "name": user_email.split('@')[0] if user_email else "User",
                    "auth_provider": "supabase",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                supabase.table("users").insert(user_data).execute()
        
        # Verify user has access to the organization
        org_member_check = supabase.table("organization_members").select("role").eq(
            "user_id", user_id
        ).eq("organization_id", request.organization_id).execute()
        
        if not org_member_check.data:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this organization"
            )
        
        # Create project with unique slug
        project_id = str(uuid4())
        base_slug = re.sub(r'[^a-z0-9-]', '-', request.name.lower()).strip('-')
        
        # Ensure slug is unique by adding random suffix if needed
        slug = base_slug
        while True:
            existing = supabase.table("projects").select("id").eq("slug", slug).eq("organization_id", request.organization_id).execute()
            if not existing.data:
                break
            # Add random 4-character suffix
            random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=4))
            slug = f"{base_slug}-{random_suffix}"
        
        # Create project
        project_data = {
            "id": project_id,
            "organization_id": request.organization_id,
            "name": request.name,
            "slug": slug,
            "description": request.description,
            "settings": request.settings or {},
            "created_by": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("projects").insert(project_data).execute()
        
        # Add user as project admin
        membership_data = {
            "id": str(uuid4()),
            "project_id": project_id,
            "user_id": user_id,
            "role": "admin",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        supabase.table("project_members").insert(membership_data).execute()
        
        # Add department associations if provided
        if request.department_ids:
            department_associations = []
            for dept_id in request.department_ids:
                # Verify department exists and belongs to same organization
                dept_check = supabase.table("departments").select("id").eq(
                    "id", dept_id
                ).eq("organization_id", request.organization_id).execute()
                
                if dept_check.data:
                    department_associations.append({
                        "id": str(uuid4()),
                        "project_id": project_id,
                        "department_id": dept_id,
                        "created_at": datetime.utcnow().isoformat()
                    })
            
            if department_associations:
                supabase.table("project_departments").insert(department_associations).execute()
        
        return {
            "success": True,
            "project": {
                "id": project_id,
                "name": request.name,
                "description": request.description,
                "organization_id": request.organization_id,
                "slug": slug,
                "created_at": project_data["created_at"],
                "is_active": True,
                "role": "admin"
            },
            "message": "Project created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get project details"""
    try:
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
        
        # Check if user has access to this project
        access_check = supabase.table("project_members").select("role").eq(
            "project_id", project_id
        ).eq("user_id", public_user_id).execute()
        
        if not access_check.data:
            # Check if user has organization-level access
            project_data = supabase.table("projects").select("organization_id").eq("id", project_id).execute()
            if project_data.data:
                org_id = project_data.data[0]["organization_id"]
                org_access = supabase.table("organization_members").select("role").eq(
                    "organization_id", org_id
                ).eq("user_id", public_user_id).execute()
                
                if not org_access.data:
                    raise HTTPException(status_code=403, detail="Access denied")
        
        # Fetch project details
        result = supabase.table("projects").select("*").eq("id", project_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = result.data[0]
        
        # Get basic statistics
        stats = {
            "content_items": 0,
            "team_members": len(access_check.data) if access_check.data else 1,
            "last_activity": project.get("updated_at", project.get("created_at"))
        }
        
        project["statistics"] = stats
        
        return {
            "success": True,
            "project": project
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{project_id}")
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update project details (requires admin permission)"""
    # Check if user has admin access to this project
    if not has_project_permission(current_user, project_id, Permission.PROJECT_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, update in database
    updated_fields = {k: v for k, v in request.dict().items() if v is not None}
    
    return {
        "success": True,
        "message": "Project updated successfully",
        "updated_fields": updated_fields
    }

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Delete project (requires admin permission)"""
    try:
        logger.info(f"Delete project {project_id} requested by user: {current_user}")
        
        supabase = get_supabase()
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # First, check if the project exists and user has access
        project_result = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = project_result.data
        
        # Check if user belongs to the organization
        # First, get the public user ID from the Supabase auth user
        auth_email = current_user.get("email")
        auth_user_id = str(current_user["user_id"])
        public_user_id = auth_user_id
        
        # If we have an email, try to find the corresponding public user
        if auth_email:
            user_result = supabase.table("users").select("id").eq("email", auth_email).execute()
            if user_result.data:
                public_user_id = user_result.data[0]["id"]
                logger.info(f"Mapped auth user {auth_user_id} to public user {public_user_id}")
        
        logger.debug(f"Using public_user_id: {public_user_id} for org membership check")
            
        org_member_result = supabase.table("organization_members").select("role").eq(
            "organization_id", project["organization_id"]
        ).eq("user_id", public_user_id).execute()
        
        if not org_member_result.data or len(org_member_result.data) == 0:
            raise HTTPException(status_code=403, detail="Access denied - user is not a member of this organization")
        
        # Check if user has admin or owner role
        user_role = org_member_result.data[0].get("role")
        if user_role not in ["admin", "owner"]:
            raise HTTPException(status_code=403, detail="Admin or owner access required")
        
        # Delete the project
        delete_result = supabase.table("projects").delete().eq("id", project_id).execute()
        
        return {
            "success": True,
            "message": "Project deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Project member endpoints
@router.get("/{project_id}/members")
async def list_project_members(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """List project members"""
    try:
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
        
        # Check if user has access to this project
        access_check = supabase.table("project_members").select("role").eq(
            "project_id", project_id
        ).eq("user_id", public_user_id).execute()
        
        if not access_check.data:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all project members with user details
        result = supabase.table("project_members").select(
            "*, users!project_members_user_id_fkey(id, email, name)"
        ).eq("project_id", project_id).execute()
        
        members = []
        for membership in result.data:
            user_data = membership.get("users!project_members_user_id_fkey") or membership.get("users")
            if user_data:
                members.append({
                    "id": membership["id"],
                    "user_id": user_data["id"],
                    "email": user_data["email"],
                    "name": user_data.get("name", user_data["email"].split('@')[0]),
                    "role": membership["role"],
                    "joined_at": membership.get("created_at")
                })
        
        return {
            "success": True,
            "members": members,
            "count": len(members)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing project members: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/members")
async def add_project_member(
    project_id: str,
    request: ProjectMemberAddRequest,
    current_user: User = Depends(get_current_user)
):
    """Add member to project (requires admin permission)"""
    # Check if user has admin access to this project
    if not has_project_permission(current_user, project_id, Permission.PROJECT_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate role
    valid_roles = ["admin", "member", "viewer"]
    if request.role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    # In a real implementation:
    # 1. Check if user exists and belongs to organization
    # 2. Add user to project_members table
    # 3. Send notification
    
    return {
        "success": True,
        "message": "Member added successfully",
        "member": {
            "user_id": request.user_id,
            "role": request.role,
            "added_by": current_user.id,
            "added_at": datetime.now().isoformat()
        }
    }

@router.put("/{project_id}/members/{member_id}")
async def update_project_member(
    project_id: str,
    member_id: str,
    role: str,
    current_user: User = Depends(get_current_user)
):
    """Update member role (requires admin permission)"""
    # Check if user has admin access to this project
    if not has_project_permission(current_user, project_id, Permission.PROJECT_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate role
    valid_roles = ["admin", "member", "viewer"]
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")
    
    return {
        "success": True,
        "message": "Member role updated successfully",
        "member": {
            "id": member_id,
            "role": role
        }
    }

@router.delete("/{project_id}/members/{member_id}")
async def remove_project_member(
    project_id: str,
    member_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove member from project (requires admin permission)"""
    # Check if user has admin access to this project
    if not has_project_permission(current_user, project_id, Permission.PROJECT_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Can't remove yourself if you're the only admin
    if member_id == current_user.id:
        # In real implementation, check if there are other admins
        raise HTTPException(status_code=400, detail="Cannot remove last admin")
    
    return {
        "success": True,
        "message": "Member removed successfully"
    }

# Project settings endpoints
@router.get("/{project_id}/settings")
async def get_project_settings(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get project settings"""
    # Check if user has access to this project
    if not has_project_permission(current_user, project_id, Permission.PROJECT_READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, fetch from database
    settings = {
        "general": {
            "default_language": "de",
            "timezone": "Europe/Berlin",
            "date_format": "DD.MM.YYYY"
        },
        "content": {
            "auto_save": True,
            "default_period": "Energie",
            "review_required": True
        },
        "notifications": {
            "email_on_publish": True,
            "slack_integration": False
        }
    }
    
    return {
        "success": True,
        "settings": settings
    }

@router.put("/{project_id}/settings")
async def update_project_settings(
    project_id: str,
    settings: dict,
    current_user: User = Depends(get_current_user)
):
    """Update project settings (requires admin permission)"""
    # Check if user has admin access to this project
    if not has_project_permission(current_user, project_id, Permission.PROJECT_UPDATE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, validate and update settings
    
    return {
        "success": True,
        "message": "Settings updated successfully",
        "settings": settings
    }

# Project department endpoints
@router.get("/{project_id}/departments")
async def list_project_departments(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """List departments associated with a project"""
    try:
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
        
        # Check if user has access to this project
        access_check = supabase.table("project_members").select("role").eq(
            "project_id", project_id
        ).eq("user_id", public_user_id).execute()
        
        if not access_check.data:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get departments associated with this project
        result = supabase.table("project_departments").select(
            "*, departments!inner(id, name, description)"
        ).eq("project_id", project_id).execute()
        
        departments = []
        for assoc in result.data:
            dept = assoc.get("departments")
            if dept:
                departments.append({
                    "id": dept["id"],
                    "name": dept["name"],
                    "description": dept.get("description"),
                    "associated_at": assoc.get("created_at")
                })
        
        return {
            "success": True,
            "departments": departments,
            "count": len(departments)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing project departments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{project_id}/departments")
async def add_project_department(
    project_id: str,
    request: ProjectDepartmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Add department to project (requires admin permission)"""
    try:
        from uuid import uuid4
        
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
        
        # Check if user has admin access to this project
        access_check = supabase.table("project_members").select("role").eq(
            "project_id", project_id
        ).eq("user_id", public_user_id).execute()
        
        if not access_check.data or access_check.data[0]["role"] not in ["admin", "owner"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get project's organization
        project_result = supabase.table("projects").select("organization_id").eq(
            "id", project_id
        ).single().execute()
        
        # Verify department exists and belongs to same organization
        dept_check = supabase.table("departments").select("id, name").eq(
            "id", request.department_id
        ).eq("organization_id", project_result.data["organization_id"]).execute()
        
        if not dept_check.data:
            raise HTTPException(status_code=404, detail="Department not found in organization")
        
        # Check if already associated
        existing = supabase.table("project_departments").select("id").eq(
            "project_id", project_id
        ).eq("department_id", request.department_id).execute()
        
        if existing.data:
            raise HTTPException(status_code=409, detail="Department already associated with project")
        
        # Add association
        association_data = {
            "id": str(uuid4()),
            "project_id": project_id,
            "department_id": request.department_id,
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("project_departments").insert(association_data).execute()
        
        return {
            "success": True,
            "message": "Department added successfully",
            "department": {
                "id": request.department_id,
                "name": dept_check.data[0]["name"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding project department: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{project_id}/departments/{department_id}")
async def remove_project_department(
    project_id: str,
    department_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Remove department from project (requires admin permission)"""
    try:
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
        
        # Check if user has admin access to this project
        access_check = supabase.table("project_members").select("role").eq(
            "project_id", project_id
        ).eq("user_id", public_user_id).execute()
        
        if not access_check.data or access_check.data[0]["role"] not in ["admin", "owner"]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Remove association
        result = supabase.table("project_departments").delete().eq(
            "project_id", project_id
        ).eq("department_id", department_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Department not associated with project")
        
        return {
            "success": True,
            "message": "Department removed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing project department: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Project activity endpoints
@router.get("/{project_id}/activity")
async def get_project_activity(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user)
):
    """Get project activity log"""
    # Check if user has access to this project
    if not has_project_permission(current_user, project_id, Permission.PROJECT_READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, fetch from audit_logs table
    activities = [
        {
            "id": "act_1",
            "action": "content.created",
            "user": {
                "id": current_user.id,
                "name": current_user.name
            },
            "resource": {
                "type": "affirmation",
                "id": "aff_123",
                "name": "Morning Affirmation"
            },
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    return {
        "success": True,
        "activities": activities,
        "pagination": {
            "limit": limit,
            "offset": offset,
            "total": len(activities)
        }
    }

# Project statistics endpoints
@router.get("/{project_id}/stats")
async def get_project_statistics(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get project statistics"""
    try:
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
        
        # Check if user has access to this project (simplified check)
        access_check = supabase.table("project_members").select("role").eq(
            "project_id", project_id
        ).eq("user_id", public_user_id).execute()
        
        # If no direct project access, check organization access
        if not access_check.data:
            project_data = supabase.table("projects").select("organization_id").eq("id", project_id).execute()
            if project_data.data:
                org_id = project_data.data[0]["organization_id"]
                org_access = supabase.table("organization_members").select("role").eq(
                    "organization_id", org_id
                ).eq("user_id", public_user_id).execute()
                
                if not org_access.data:
                    raise HTTPException(status_code=403, detail="Access denied")
        
        # Get goals count
        goals_result = supabase.table("goals").select("id, status").eq(
            "project_id", project_id
        ).execute()
        
        goals_data = goals_result.data or []
        goals_total = len(goals_data)
        active_goals = len([g for g in goals_data if g.get("status") == "active"])
        completed_goals = len([g for g in goals_data if g.get("status") == "completed"])
        
        # Get tasks count
        tasks_result = None
        if goals_data:
            goal_ids = [g["id"] for g in goals_data]
            tasks_result = supabase.table("tasks").select("id, status").in_(
                "goal_id", goal_ids
            ).execute()
        
        tasks_data = tasks_result.data if tasks_result else []
        tasks_total = len(tasks_data)
        pending_tasks = len([t for t in tasks_data if t.get("status") == "pending"])
        in_progress_tasks = len([t for t in tasks_data if t.get("status") == "in_progress"])
        completed_tasks = len([t for t in tasks_data if t.get("status") == "completed"])
        
        # Get team members count
        members_result = supabase.table("project_members").select("id").eq(
            "project_id", project_id
        ).execute()
        
        team_members = len(members_result.data or [])
        
        stats = {
            "content": {
                "goals": goals_total,
                "active_goals": active_goals,
                "completed_goals": completed_goals,
                "tasks": tasks_total,
                "pending_tasks": pending_tasks,
                "in_progress_tasks": in_progress_tasks,
                "completed_tasks": completed_tasks,
                "affirmations": 0,  # TODO: Implement when content types are added
                "visual_posts": 0,
                "videos": 0,
                "workflows": 0
            },
            "engagement": {
                "total_views": 0,
                "total_shares": 0,
                "avg_engagement_rate": 0
            },
            "team": {
                "total_members": team_members,
                "active_today": 0,  # TODO: Implement activity tracking
                "pending_invites": 0
            },
            "period": "all_time"
        }
        
        return {
            "success": True,
            "statistics": stats,
            "generated_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))