"""
Project management endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.core.auth import get_current_user
from app.models.auth import User, Permission
from app.core.security.permissions import has_project_permission

router = APIRouter(prefix="/api/projects", tags=["Projects"])

# Request models
class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    organization_id: str
    settings: Optional[dict] = None

class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[dict] = None
    is_active: Optional[bool] = None

class ProjectMemberAddRequest(BaseModel):
    user_id: str
    role: str = "member"  # admin, member, viewer

# Project endpoints
@router.get("/")
async def list_projects(
    organization_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """List all projects the user has access to"""
    try:
        from app.core.dependencies import get_supabase_client
        supabase_client = get_supabase_client()
        supabase = supabase_client.client
        
        if not supabase:
            raise HTTPException(
                status_code=503,
                detail="Database connection not available"
            )
        
        # Get projects the user has access to
        if organization_id:
            # Get projects for specific organization
            # First check if user has access to this organization
            org_check = supabase.table("organization_members").select("role").eq(
                "user_id", str(current_user.id)
            ).eq("organization_id", organization_id).execute()
            
            if not org_check.data:
                raise HTTPException(status_code=403, detail="Access denied to this organization")
            
            # Get all projects for the organization
            result = supabase.table("projects").select("*").eq(
                "organization_id", organization_id
            ).execute()
            
            projects = []
            for project in result.data:
                # Check if user is a member of this project
                member_check = supabase.table("project_members").select("role").eq(
                    "user_id", str(current_user.id)
                ).eq("project_id", project["id"]).execute()
                
                projects.append({
                    "id": project["id"],
                    "name": project["name"],
                    "description": project.get("description"),
                    "organization_id": project["organization_id"],
                    "created_at": project["created_at"],
                    "is_active": project.get("is_active", True),
                    "role": member_check.data[0]["role"] if member_check.data else None
                })
        else:
            # Get all projects user has access to
            result = supabase.table("project_members").select(
                "role, projects(id, name, description, organization_id, created_at, is_active)"
            ).eq("user_id", str(current_user.id)).execute()
            
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
    current_user: User = Depends(get_current_user)
):
    """Create a new project within an organization"""
    # Check if user has permission to create projects in this organization
    if request.organization_id != current_user.default_organization_id:
        raise HTTPException(status_code=403, detail="Cannot create project in this organization")
    
    try:
        # In a real implementation:
        # 1. Validate organization exists and user has access
        # 2. Create project in database
        # 3. Add current user as project admin
        
        project = {
            "id": f"proj_{datetime.now().timestamp()}",
            "name": request.name,
            "description": request.description,
            "organization_id": request.organization_id,
            "settings": request.settings or {},
            "created_at": datetime.now().isoformat(),
            "created_by": current_user.id,
            "is_active": True
        }
        
        return {
            "success": True,
            "project": project,
            "message": "Project created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get project details"""
    # Check if user has access to this project
    if not has_project_permission(current_user, project_id, Permission.READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, fetch from database
    project = {
        "id": project_id,
        "name": "Project Name",
        "description": "Project description",
        "organization_id": current_user.default_organization_id,
        "settings": {},
        "created_at": datetime.now().isoformat(),
        "is_active": True,
        "statistics": {
            "content_items": 42,
            "team_members": 5,
            "last_activity": datetime.now().isoformat()
        }
    }
    
    return {
        "success": True,
        "project": project
    }

@router.put("/{project_id}")
async def update_project(
    project_id: str,
    request: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Update project details (requires admin permission)"""
    # Check if user has admin access to this project
    if not has_project_permission(current_user, project_id, Permission.WRITE):
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
    current_user: User = Depends(get_current_user)
):
    """Delete project (requires admin permission)"""
    # Check if user has admin access to this project
    if not has_project_permission(current_user, project_id, Permission.DELETE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation:
    # 1. Check if project has active data
    # 2. Soft delete or archive project
    # 3. Notify team members
    
    return {
        "success": True,
        "message": "Project deleted successfully"
    }

# Project member endpoints
@router.get("/{project_id}/members")
async def list_project_members(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """List project members"""
    # Check if user has access to this project
    if not has_project_permission(current_user, project_id, Permission.READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, fetch from database
    members = [
        {
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.name,
            "role": "admin",
            "joined_at": datetime.now().isoformat()
        }
    ]
    
    return {
        "success": True,
        "members": members,
        "count": len(members)
    }

@router.post("/{project_id}/members")
async def add_project_member(
    project_id: str,
    request: ProjectMemberAddRequest,
    current_user: User = Depends(get_current_user)
):
    """Add member to project (requires admin permission)"""
    # Check if user has admin access to this project
    if not has_project_permission(current_user, project_id, Permission.WRITE):
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
    if not has_project_permission(current_user, project_id, Permission.WRITE):
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
    if not has_project_permission(current_user, project_id, Permission.WRITE):
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
    if not has_project_permission(current_user, project_id, Permission.READ):
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
    if not has_project_permission(current_user, project_id, Permission.WRITE):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In a real implementation, validate and update settings
    
    return {
        "success": True,
        "message": "Settings updated successfully",
        "settings": settings
    }

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
    if not has_project_permission(current_user, project_id, Permission.READ):
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
    current_user: User = Depends(get_current_user)
):
    """Get project statistics"""
    # Check if user has access to this project
    if not has_project_permission(current_user, project_id, Permission.READ):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In a real implementation, calculate from database
    stats = {
        "content": {
            "affirmations": 156,
            "visual_posts": 89,
            "videos": 23,
            "workflows": 45
        },
        "engagement": {
            "total_views": 12500,
            "total_shares": 340,
            "avg_engagement_rate": 4.2
        },
        "team": {
            "total_members": 5,
            "active_today": 3,
            "pending_invites": 1
        },
        "period": "last_30_days"
    }
    
    return {
        "success": True,
        "statistics": stats,
        "generated_at": datetime.now().isoformat()
    }