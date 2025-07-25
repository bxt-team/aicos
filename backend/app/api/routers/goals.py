from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, date

from supabase import create_client, Client
import os
from ...core.supabase_auth import get_current_user

router = APIRouter(prefix="/api/goals", tags=["goals"])


def get_supabase() -> Client:
    """Get the actual Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)


class GoalCreate(BaseModel):
    project_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    target_date: Optional[date] = None


class GoalUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    target_date: Optional[date] = None
    status: Optional[str] = Field(None, pattern="^(active|completed|archived)$")
    progress: Optional[int] = Field(None, ge=0, le=100)


class Goal(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: Optional[str]
    target_date: Optional[date]
    status: str
    progress: int
    created_at: datetime
    updated_at: datetime
    task_count: Optional[int] = 0
    completed_task_count: Optional[int] = 0
    project_name: Optional[str] = None


async def verify_project_access(project_id: str, user_id: str, supabase) -> bool:
    """Verify user has access to the project."""
    try:
        # Check if user is a member of the project
        member_check = supabase.table('project_members').select('role').eq(
            'project_id', project_id
        ).eq('user_id', user_id).execute()
        
        if member_check.data:
            return True
        
        # Check if user is member of organization that owns the project
        project_org = supabase.table('projects').select('organization_id').eq(
            'id', project_id
        ).single().execute()
        
        if project_org.data:
            org_member_check = supabase.table('organization_members').select('role').eq(
                'organization_id', project_org.data['organization_id']
            ).eq('user_id', user_id).execute()
            
            return bool(org_member_check.data)
        
        return False
    except:
        return False


@router.get("", response_model=List[Goal])
async def list_goals(
    project_id: Optional[UUID] = None,
    status: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List goals. Can filter by project and status."""
    supabase = get_supabase()
    
    try:
        # Get the user ID from the auth context
        auth_email = current_user.get('email')
        user_id = str(current_user['user_id'])
        
        # Get the public user ID from the users table if needed
        if auth_email:
            user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
            if user_result.data:
                user_id = user_result.data[0]['id']
        
        # Build query
        query = supabase.table('goals').select(
            '*, projects!inner(id, name, organization_id)'
        )
        
        if project_id:
            # Verify access to specific project
            if not await verify_project_access(str(project_id), user_id, supabase):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project"
                )
            query = query.eq('project_id', str(project_id))
        else:
            # Get all projects user has access to
            # First get projects via direct membership
            member_projects = supabase.table('project_members').select('project_id').eq(
                'user_id', user_id
            ).execute()
            
            # Then get projects via organization membership
            org_memberships = supabase.table('organization_members').select('organization_id').eq(
                'user_id', user_id
            ).execute()
            
            project_ids = [m['project_id'] for m in member_projects.data]
            
            if org_memberships.data:
                org_ids = [m['organization_id'] for m in org_memberships.data]
                org_projects = supabase.table('projects').select('id').in_(
                    'organization_id', org_ids
                ).execute()
                project_ids.extend([p['id'] for p in org_projects.data])
            
            if not project_ids:
                return []
            
            query = query.in_('project_id', list(set(project_ids)))
        
        if status:
            query = query.eq('status', status)
        
        response = query.order('created_at', desc=True).execute()
        
        goals = []
        for goal in response.data:
            goal_dict = dict(goal)
            
            # Get task counts
            task_count_response = supabase.table('tasks').select(
                'id, status', count='exact'
            ).eq('goal_id', goal['id']).execute()
            
            goal_dict['task_count'] = task_count_response.count or 0
            goal_dict['completed_task_count'] = len([
                t for t in task_count_response.data if t['status'] == 'completed'
            ])
            
            if goal.get('projects'):
                goal_dict['project_name'] = goal['projects']['name']
                del goal_dict['projects']
            
            goals.append(Goal(**goal_dict))
        
        return goals
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list goals: {str(e)}"
        )


@router.post("", response_model=Goal, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal: GoalCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new goal for a project."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get('email')
    user_id = str(current_user['user_id'])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]['id']
    
    # Verify user has access to the project
    if not await verify_project_access(str(goal.project_id), user_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    try:
        goal_data = {
            'project_id': str(goal.project_id),
            'title': goal.title,
            'description': goal.description,
            'target_date': goal.target_date.isoformat() if goal.target_date else None,
            'status': 'active',
            'progress': 0
        }
        
        response = supabase.table('goals').insert(goal_data).execute()
        
        # Get with project name
        created_id = response.data[0]['id']
        goal_response = supabase.table('goals').select(
            '*, projects!inner(name)'
        ).eq('id', created_id).single().execute()
        
        goal_dict = dict(goal_response.data)
        goal_dict['task_count'] = 0
        goal_dict['completed_task_count'] = 0
        
        if goal_dict.get('projects'):
            goal_dict['project_name'] = goal_dict['projects']['name']
            del goal_dict['projects']
        
        return Goal(**goal_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create goal: {str(e)}"
        )


@router.get("/{goal_id}", response_model=Goal)
async def get_goal(
    goal_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific goal."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('goals').select(
            '*, projects!inner(id, name)'
        ).eq('id', str(goal_id)).single().execute()
        
        goal_dict = dict(response.data)
        
        # Get the user ID from the auth context
        auth_email = current_user.get('email')
        user_id = str(current_user['user_id'])
        
        # Get the public user ID from the users table if needed
        if auth_email:
            user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
            if user_result.data:
                user_id = user_result.data[0]['id']
        
        # Verify user has access to the project
        if not await verify_project_access(goal_dict['project_id'], user_id, supabase):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Get task counts
        task_count_response = supabase.table('tasks').select(
            'id, status', count='exact'
        ).eq('goal_id', str(goal_id)).execute()
        
        goal_dict['task_count'] = task_count_response.count or 0
        goal_dict['completed_task_count'] = len([
            t for t in task_count_response.data if t['status'] == 'completed'
        ])
        
        if goal_dict.get('projects'):
            goal_dict['project_name'] = goal_dict['projects']['name']
            del goal_dict['projects']
        
        return Goal(**goal_dict)
    except Exception as e:
        if 'No rows found' in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get goal: {str(e)}"
        )


@router.patch("/{goal_id}", response_model=Goal)
async def update_goal(
    goal_id: UUID,
    goal: GoalUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a goal."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get('email')
    user_id = str(current_user['user_id'])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]['id']
    
    # Get the goal to verify access
    try:
        goal_check = supabase.table('goals').select('project_id').eq(
            'id', str(goal_id)
        ).single().execute()
        
        if not await verify_project_access(goal_check.data['project_id'], user_id, supabase):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    update_data = {}
    if goal.title is not None:
        update_data['title'] = goal.title
    if goal.description is not None:
        update_data['description'] = goal.description
    if goal.target_date is not None:
        update_data['target_date'] = goal.target_date.isoformat()
    if goal.status is not None:
        update_data['status'] = goal.status
    if goal.progress is not None:
        update_data['progress'] = goal.progress
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        response = supabase.table('goals').update(update_data).eq(
            'id', str(goal_id)
        ).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
        
        # Get with project name and task counts
        goal_response = supabase.table('goals').select(
            '*, projects!inner(name)'
        ).eq('id', str(goal_id)).single().execute()
        
        goal_dict = dict(goal_response.data)
        
        # Get task counts
        task_count_response = supabase.table('tasks').select(
            'id, status', count='exact'
        ).eq('goal_id', str(goal_id)).execute()
        
        goal_dict['task_count'] = task_count_response.count or 0
        goal_dict['completed_task_count'] = len([
            t for t in task_count_response.data if t['status'] == 'completed'
        ])
        
        if goal_dict.get('projects'):
            goal_dict['project_name'] = goal_dict['projects']['name']
            del goal_dict['projects']
        
        return Goal(**goal_dict)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update goal: {str(e)}"
        )


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a goal. This will also delete all associated tasks."""
    supabase = get_supabase()
    
    # Get the user ID from the auth context
    auth_email = current_user.get('email')
    user_id = str(current_user['user_id'])
    
    # Get the public user ID from the users table if needed
    if auth_email:
        user_result = supabase.table('users').select('id').eq('email', auth_email).execute()
        if user_result.data:
            user_id = user_result.data[0]['id']
    
    # Get the goal to verify access
    try:
        goal_check = supabase.table('goals').select('project_id').eq(
            'id', str(goal_id)
        ).single().execute()
        
        if not await verify_project_access(goal_check.data['project_id'], user_id, supabase):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
    except:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    try:
        # Delete goal (tasks will be cascade deleted)
        response = supabase.table('goals').delete().eq(
            'id', str(goal_id)
        ).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Goal not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete goal: {str(e)}"
        )