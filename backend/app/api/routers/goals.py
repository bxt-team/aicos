from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from datetime import datetime, date

from supabase import create_client, Client
import os
from ...core.supabase_auth import get_current_user
from ...core.dependencies import get_goal_suggestion_crew, get_supabase_client
from ...agents.crews.goal_suggestion_crew import GoalSuggestionInput, GoalSuggestionOutput

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


class GoalSuggestionRequest(BaseModel):
    project_id: UUID
    include_knowledge_base: bool = True
    user_feedback: Optional[str] = None
    previous_goals: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[UUID] = None  # To link feedback to suggestions
    custom_prompt: Optional[str] = None  # Custom prompt for goal generation


class GoalSuggestionFeedback(BaseModel):
    project_id: UUID
    session_id: UUID
    suggested_goals: List[Dict[str, Any]]
    feedback: List[Dict[str, Any]]  # Array of feedback per goal


class GoalFeedbackItem(BaseModel):
    goal_index: int  # Index in the suggested_goals array
    feedback_type: str  # 'accepted', 'rejected', 'modified'
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_text: Optional[str] = None
    modifications: Optional[Dict[str, Any]] = None  # What was changed if modified


@router.post("/suggest", response_model=GoalSuggestionOutput)
async def suggest_goals(
    request: GoalSuggestionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    goal_crew = Depends(get_goal_suggestion_crew)
):
    """Generate AI-powered goal suggestions based on project context."""
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
    if not await verify_project_access(str(request.project_id), user_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    try:
        # Get project details
        project_response = supabase.table('projects').select(
            '*, organizations!inner(name, description)'
        ).eq('id', str(request.project_id)).single().execute()
        
        if not project_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = project_response.data
        organization = project.get('organizations', {})
        
        # Prepare knowledge base content if requested
        knowledge_content = ""
        if request.include_knowledge_base:
            try:
                # Get knowledge base files for the project
                kb_response = supabase.table('knowledge_bases').select(
                    'id, file_name, content'
                ).eq('project_id', str(request.project_id)).execute()
                
                if kb_response.data:
                    # Combine content from all knowledge base files
                    knowledge_content = "\n\n".join([
                        f"--- {kb['file_name']} ---\n{kb.get('content', '')[:3000]}"
                        for kb in kb_response.data
                    ])
            except Exception as e:
                # Continue without knowledge base if there's an error
                pass
        
        # Extract objectives from enhanced_data if available
        project_objectives = []
        if project.get('enhanced_data'):
            enhanced_data = project.get('enhanced_data', {})
            project_objectives = enhanced_data.get('objectives', [])
        
        # Get historical feedback for the crew
        historical_feedback = None
        try:
            feedback_data = supabase.table('goal_suggestion_feedback').select(
                'rating, feedback_type, feedback_text'
            ).eq('project_id', str(request.project_id)).order(
                'created_at', desc=True
            ).limit(20).execute()
            
            if feedback_data.data:
                ratings = [f['rating'] for f in feedback_data.data if f.get('rating')]
                historical_feedback = {
                    'average_rating': sum(ratings) / len(ratings) if ratings else 0,
                    'total_feedback': len(feedback_data.data),
                    'recent_feedback': feedback_data.data[:5]
                }
        except:
            pass
        
        # Prepare input for the crew
        crew_input = GoalSuggestionInput(
            project_description=project.get('description', ''),
            project_objectives=project_objectives,
            organization_purpose=organization.get('description', ''),  # Use description instead of purpose
            knowledge_files_content=knowledge_content if knowledge_content else None,
            user_feedback=request.user_feedback,
            previous_goals=request.previous_goals,
            historical_feedback=historical_feedback,
            custom_prompt=request.custom_prompt
        )
        
        # Generate suggestions
        result = goal_crew.suggest_goals(crew_input)
        
        # Generate session ID if not provided
        session_id = request.session_id or uuid4()
        
        # Add session_id to the response
        result_dict = result.dict() if hasattr(result, 'dict') else result
        result_dict['session_id'] = str(session_id)
        
        # Get previous feedback for this project to improve suggestions
        try:
            feedback_data = supabase.table('goal_suggestion_feedback').select(
                'rating, feedback_type, feedback_text'
            ).eq('project_id', str(request.project_id)).order(
                'created_at', desc=True
            ).limit(10).execute()
            
            if feedback_data.data:
                # Calculate average rating and feedback summary
                ratings = [f['rating'] for f in feedback_data.data if f.get('rating')]
                avg_rating = sum(ratings) / len(ratings) if ratings else 0
                result_dict['historical_feedback'] = {
                    'average_rating': avg_rating,
                    'total_feedback': len(feedback_data.data),
                    'recent_feedback': feedback_data.data[:3]
                }
        except:
            pass  # Continue without feedback data
        
        return result_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate goal suggestions: {str(e)}"
        )


@router.post("/suggest/feedback", status_code=status.HTTP_201_CREATED)
async def submit_goal_suggestion_feedback(
    feedback: GoalSuggestionFeedback,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Submit feedback on AI-generated goal suggestions."""
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
    if not await verify_project_access(str(feedback.project_id), user_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    try:
        # Process each feedback item
        feedback_records = []
        for fb_item in feedback.feedback:
            goal_index = fb_item.get('goal_index', 0)
            
            # Validate goal index
            if goal_index >= len(feedback.suggested_goals):
                continue
            
            suggested_goal = feedback.suggested_goals[goal_index]
            
            feedback_record = {
                'project_id': str(feedback.project_id),
                'user_id': user_id,
                'suggestion_session_id': str(feedback.session_id),
                'suggested_goal': suggested_goal,
                'feedback_type': fb_item.get('feedback_type', 'rejected'),
                'rating': fb_item.get('rating'),
                'feedback_text': fb_item.get('feedback_text'),
                'modifications': fb_item.get('modifications'),
                'created_at': datetime.utcnow().isoformat()
            }
            
            feedback_records.append(feedback_record)
        
        # Insert all feedback records
        if feedback_records:
            result = supabase.table('goal_suggestion_feedback').insert(feedback_records).execute()
            
            return {
                'success': True,
                'message': f'Feedback submitted for {len(feedback_records)} goals',
                'feedback_count': len(feedback_records)
            }
        else:
            return {
                'success': False,
                'message': 'No valid feedback items to submit',
                'feedback_count': 0
            }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )


@router.get("/feedback/summary")
async def get_goal_feedback_summary(
    project_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get a summary of goal suggestion feedback for a project."""
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
    if not await verify_project_access(str(project_id), user_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this project"
        )
    
    try:
        # Get feedback summary
        feedback_data = supabase.table('goal_suggestion_feedback').select(
            'rating, feedback_type, feedback_text, created_at'
        ).eq('project_id', str(project_id)).execute()
        
        if not feedback_data.data:
            return {
                'total_feedback': 0,
                'average_rating': 0,
                'feedback_types': {},
                'recent_feedback': []
            }
        
        # Calculate statistics
        ratings = [f['rating'] for f in feedback_data.data if f.get('rating')]
        feedback_types = {}
        for f in feedback_data.data:
            ft = f.get('feedback_type', 'unknown')
            feedback_types[ft] = feedback_types.get(ft, 0) + 1
        
        # Get recent feedback with text
        recent_feedback = [
            {
                'rating': f.get('rating'),
                'feedback_type': f.get('feedback_type'),
                'feedback_text': f.get('feedback_text'),
                'created_at': f.get('created_at')
            }
            for f in sorted(feedback_data.data, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
            if f.get('feedback_text')
        ]
        
        return {
            'total_feedback': len(feedback_data.data),
            'average_rating': sum(ratings) / len(ratings) if ratings else 0,
            'feedback_types': feedback_types,
            'recent_feedback': recent_feedback
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback summary: {str(e)}"
        )