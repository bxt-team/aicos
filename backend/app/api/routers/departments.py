from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from datetime import datetime
from supabase import create_client, Client
import os

from ...core.supabase_auth import get_current_user
from ...core.dependencies import get_agent

router = APIRouter(prefix="/api/departments", tags=["departments"])


def get_supabase() -> Client:
    """Get the actual Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)


# Available AI agents that can be assigned to departments
AVAILABLE_AI_AGENTS = [
    {"id": "qa_agent", "name": "Q&A Agent", "type": "qa_agent", "capabilities": ["answer_questions", "knowledge_base"]},
    {"id": "researcher_agent", "name": "Researcher Agent", "type": "researcher_agent", "capabilities": ["research", "analysis"]},
    {"id": "content_creator_agent", "name": "Content Creator Agent", "type": "content_creator_agent", "capabilities": ["content_generation", "writing"]},
    {"id": "visual_post_creator_agent", "name": "Visual Post Creator Agent", "type": "visual_post_creator_agent", "capabilities": ["image_generation", "visual_content"]},
    {"id": "instagram_poster_agent", "name": "Instagram Poster Agent", "type": "instagram_poster_agent", "capabilities": ["social_media", "instagram"]},
    {"id": "x_poster_agent", "name": "X Poster Agent", "type": "x_poster_agent", "capabilities": ["social_media", "twitter"]},
    {"id": "threads_poster_agent", "name": "Threads Poster Agent", "type": "threads_poster_agent", "capabilities": ["social_media", "threads"]},
]


class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class Department(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0
    ai_agent_count: Optional[int] = 0


class DepartmentAssignment(BaseModel):
    id: UUID
    department_id: UUID
    assignee_type: str  # 'member' or 'ai_agent'
    assignee_id: UUID
    assignee_name: str
    assignee_metadata: Dict[str, Any] = {}
    role: Optional[str]
    assigned_at: datetime
    assigned_by: Optional[UUID]
    created_at: datetime
    updated_at: datetime
    # Additional fields from view
    member_email: Optional[str] = None
    member_full_name: Optional[str] = None


class AssignmentCreate(BaseModel):
    assignee_type: str = Field(..., pattern="^(member|ai_agent)$")
    assignee_id: str  # For AI agents, this will be the agent type ID
    role: Optional[str] = None


class AIAgent(BaseModel):
    id: str
    name: str
    type: str
    capabilities: List[str]


@router.get("", response_model=List[Department])
async def list_departments(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all departments in the project."""
    supabase = get_supabase()
    
    try:
        # Get departments
        response = supabase.table('departments').select('*').eq(
            'project_id', str(project_id)
        ).order('name').execute()
        
        departments = []
        for dept in response.data:
            dept_dict = dict(dept)
            
            # Get assignment counts
            assignments = supabase.table('department_assignments').select(
                'assignee_type'
            ).eq('department_id', dept['id']).execute()
            
            member_count = sum(1 for a in assignments.data if a['assignee_type'] == 'member')
            ai_agent_count = sum(1 for a in assignments.data if a['assignee_type'] == 'ai_agent')
            
            dept_dict['member_count'] = member_count
            dept_dict['ai_agent_count'] = ai_agent_count
            departments.append(Department(**dept_dict))
            
        return departments
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list departments: {str(e)}"
        )


@router.post("", response_model=Department, status_code=status.HTTP_201_CREATED)
async def create_department(
    project_id: UUID,
    department: DepartmentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new department. Requires admin or owner role."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('departments').insert({
            'project_id': str(project_id),
            'name': department.name,
            'description': department.description
        }).execute()
        
        dept_dict = dict(response.data[0])
        dept_dict['member_count'] = 0
        dept_dict['ai_agent_count'] = 0
        return Department(**dept_dict)
    except Exception as e:
        if 'duplicate key' in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A department with this name already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create department: {str(e)}"
        )


@router.get("/ai-agents", response_model=List[AIAgent])
async def list_available_ai_agents(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all available AI agents that can be assigned to departments."""
    return AVAILABLE_AI_AGENTS


@router.get("/{department_id}", response_model=Department)
async def get_department(
    department_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a specific department."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('departments').select('*').eq(
            'id', str(department_id)
        ).single().execute()
        
        dept_dict = dict(response.data)
        
        # Get assignment counts
        assignments = supabase.table('department_assignments').select(
            'assignee_type'
        ).eq('department_id', str(department_id)).execute()
        
        member_count = sum(1 for a in assignments.data if a['assignee_type'] == 'member')
        ai_agent_count = sum(1 for a in assignments.data if a['assignee_type'] == 'ai_agent')
        
        dept_dict['member_count'] = member_count
        dept_dict['ai_agent_count'] = ai_agent_count
        
        return Department(**dept_dict)
    except Exception as e:
        if 'not found' in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get department: {str(e)}"
        )


@router.patch("/{department_id}", response_model=Department)
async def update_department(
    department_id: UUID,
    department: DepartmentUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update a department. Requires admin or owner role."""
    supabase = get_supabase()
    
    update_data = {k: v for k, v in department.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    try:
        response = supabase.table('departments').update(
            update_data
        ).eq('id', str(department_id)).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
        
        dept_dict = dict(response.data[0])
        
        # Get assignment counts
        assignments = supabase.table('department_assignments').select(
            'assignee_type'
        ).eq('department_id', str(department_id)).execute()
        
        member_count = sum(1 for a in assignments.data if a['assignee_type'] == 'member')
        ai_agent_count = sum(1 for a in assignments.data if a['assignee_type'] == 'ai_agent')
        
        dept_dict['member_count'] = member_count
        dept_dict['ai_agent_count'] = ai_agent_count
        
        return Department(**dept_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update department: {str(e)}"
        )


@router.delete("/{department_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(
    department_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a department. Requires admin or owner role."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('departments').delete().eq(
            'id', str(department_id)
        ).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Department not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete department: {str(e)}"
        )


# Department Assignment endpoints
@router.get("/{department_id}/assignments", response_model=List[DepartmentAssignment])
async def list_department_assignments(
    department_id: UUID,
    assignee_type: Optional[str] = Query(None, pattern="^(member|ai_agent)$"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all assignments in a department."""
    supabase = get_supabase()
    
    try:
        query = supabase.table('department_assignments_view').select('*').eq(
            'department_id', str(department_id)
        )
        
        if assignee_type:
            query = query.eq('assignee_type', assignee_type)
        
        response = query.order('assignee_name').execute()
        
        return [DepartmentAssignment(**dict(a)) for a in response.data]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list assignments: {str(e)}"
        )


@router.post("/{department_id}/assignments", response_model=DepartmentAssignment, status_code=status.HTTP_201_CREATED)
async def create_department_assignment(
    department_id: UUID,
    assignment: AssignmentCreate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Assign a member or AI agent to a department."""
    supabase = get_supabase()
    
    try:
        # Prepare assignment data
        assignment_data = {
            'department_id': str(department_id),
            'assignee_type': assignment.assignee_type,
            'role': assignment.role,
            'assigned_by': current_user['id']
        }
        
        if assignment.assignee_type == 'member':
            # For members, assignee_id is the user ID
            # Get member details
            user_response = supabase.auth.admin.get_user_by_id(assignment.assignee_id)
            if not user_response.user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Member not found"
                )
            
            assignment_data['assignee_id'] = assignment.assignee_id
            assignment_data['assignee_name'] = user_response.user.user_metadata.get('full_name', user_response.user.email)
            assignment_data['assignee_metadata'] = {
                'email': user_response.user.email
            }
        else:
            # For AI agents, assignee_id is the agent type
            # Find the agent in our list
            agent = next((a for a in AVAILABLE_AI_AGENTS if a['id'] == assignment.assignee_id), None)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="AI agent not found"
                )
            
            # Generate a unique ID for this agent assignment
            assignment_data['assignee_id'] = str(uuid4())
            assignment_data['assignee_name'] = agent['name']
            assignment_data['assignee_metadata'] = {
                'agent_type': agent['type'],
                'agent_id': agent['id'],
                'capabilities': agent['capabilities']
            }
        
        # Create the assignment
        response = supabase.table('department_assignments').insert(
            assignment_data
        ).execute()
        
        # Fetch the created assignment with view data
        created = supabase.table('department_assignments_view').select('*').eq(
            'id', response.data[0]['id']
        ).single().execute()
        
        return DepartmentAssignment(**dict(created.data))
    except HTTPException:
        raise
    except Exception as e:
        if 'duplicate key' in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This assignee is already assigned to this department"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create assignment: {str(e)}"
        )


@router.delete("/{department_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department_assignment(
    department_id: UUID,
    assignment_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Remove an assignment from a department."""
    supabase = get_supabase()
    
    try:
        response = supabase.table('department_assignments').delete().match({
            'id': str(assignment_id),
            'department_id': str(department_id)
        }).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assignment not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete assignment: {str(e)}"
        )