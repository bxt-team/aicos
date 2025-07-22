"""
Permission checking utilities for multi-tenant access control
"""
from typing import Optional
from app.models.auth import User, Permission, OrganizationRole

def has_organization_permission(
    user: User, 
    organization_id: str, 
    permission: Permission
) -> bool:
    """
    Check if user has specific permission in organization
    
    Args:
        user: Current user
        organization_id: Organization ID to check
        permission: Required permission
        
    Returns:
        bool: True if user has permission
    """
    # For now, simplified check - always return True
    # In a real implementation:
    # 1. Query organization_members for user's role in org
    # 2. Check if role has required permission
    # 3. Consider special cases (e.g., system admins)
    
    return True

def has_project_permission(
    user: User,
    project_id: str,
    permission: Permission
) -> bool:
    """
    Check if user has specific permission in project
    
    Args:
        user: Current user
        project_id: Project ID to check
        permission: Required permission
        
    Returns:
        bool: True if user has permission
    """
    # For now, simplified check - assume user has access
    # In real implementation:
    # 1. Query project_members for user's role in project
    # 2. If not direct member, check organization membership
    # 3. Map role to permissions
    
    return True

def get_user_organization_role(user: User, organization_id: str) -> Optional[OrganizationRole]:
    """
    Get user's role in organization
    
    Args:
        user: Current user
        organization_id: Organization ID
        
    Returns:
        Role or None if user is not a member
    """
    # In real implementation, query database
    # For now, return OWNER for any organization
    return OrganizationRole.OWNER

def get_user_project_role(user: User, project_id: str) -> Optional[OrganizationRole]:
    """
    Get user's role in project
    
    Args:
        user: Current user
        project_id: Project ID
        
    Returns:
        Role or None if user is not a member
    """
    # In real implementation, query database
    # For now, return admin role
    return OrganizationRole.ADMIN

def can_manage_organization(user: User, organization_id: str) -> bool:
    """Check if user can manage organization (owner or admin)"""
    role = get_user_organization_role(user, organization_id)
    return role in [OrganizationRole.OWNER, OrganizationRole.ADMIN] if role else False

def can_manage_project(user: User, project_id: str) -> bool:
    """Check if user can manage project (admin role)"""
    role = get_user_project_role(user, project_id)
    return role == OrganizationRole.ADMIN if role else False

def filter_by_organization_access(user: User, query):
    """
    Filter database query by user's organization access
    
    This would be used to automatically filter queries to only
    return data the user has access to.
    """
    # In real implementation:
    # 1. Get list of organizations user belongs to
    # 2. Add filter to query
    # Example: query.filter(Model.organization_id.in_(user_orgs))
    
    return query

def filter_by_project_access(user: User, query):
    """
    Filter database query by user's project access
    """
    # In real implementation:
    # 1. Get list of projects user has access to
    # 2. Add filter to query
    
    return query