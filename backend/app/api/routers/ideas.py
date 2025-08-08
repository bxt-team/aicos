"""
API Router for Ideas management
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.dependencies import get_supabase_client, get_agent
from app.core.supabase_auth import get_current_user
from app.agents.crews.idea_assistant_crew import (
    IdeaAssistantCrew, 
    IdeaRefinementInput,
    IdeaValidationInput,
    TaskGenerationInput
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["ideas"])


# Pydantic models for API
class IdeaCreate(BaseModel):
    """Model for creating a new idea"""
    title: str
    initial_description: str
    project_id: Optional[UUID] = None  # None for company-level ideas
    
class IdeaUpdate(BaseModel):
    """Model for updating an idea"""
    title: Optional[str] = None
    refined_description: Optional[str] = None
    status: Optional[str] = None
    
class IdeaResponse(BaseModel):
    """Model for idea response"""
    id: UUID
    organization_id: UUID
    project_id: Optional[UUID]
    user_id: UUID
    title: str
    initial_description: str
    refined_description: Optional[str]
    status: str
    validation_score: Optional[float]
    validation_reasons: Optional[Dict[str, Any]]
    conversation_history: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class RefineIdeaRequest(BaseModel):
    """Request model for refining an idea"""
    message: str
    
class RefineIdeaResponse(BaseModel):
    """Response model for idea refinement"""
    response: str
    questions: List[str]
    refined_description: Optional[str]

class ValidateIdeaResponse(BaseModel):
    """Response model for idea validation"""
    validation_score: float
    validation_reasons: Dict[str, Any]
    recommendation: str

class ConvertToTasksResponse(BaseModel):
    """Response model for task conversion"""
    tasks_created: int
    task_ids: List[UUID]
    tasks: List[Dict[str, Any]]


@router.post("/ideas", response_model=IdeaResponse)
async def create_idea(
    idea: IdeaCreate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """Create a new idea"""
    try:
        # Get user's organization - prefer from current_user if available
        if 'organization_id' in current_user:
            organization_id = current_user['organization_id']
        else:
            # Fallback to querying organization_members
            org_result = supabase.table('organization_members').select(
                'organization_id'
            ).eq('user_id', current_user.get('app_user_id', current_user['user_id'])).execute()
            
            if not org_result.data:
                raise HTTPException(status_code=404, detail="No organization found for user. Please ensure you belong to an organization.")
            
            organization_id = org_result.data[0]['organization_id']
        
        # Verify project belongs to organization if provided
        if idea.project_id:
            project_result = supabase.table('projects').select('id').eq(
                'id', str(idea.project_id)
            ).eq('organization_id', organization_id).execute()
            
            if not project_result.data:
                raise HTTPException(status_code=404, detail="Project not found in organization")
        
        # Create the idea
        idea_data = {
            'organization_id': organization_id,
            'project_id': str(idea.project_id) if idea.project_id else None,
            'user_id': current_user['user_id'],  # Use auth user ID, not app user ID
            'title': idea.title,
            'initial_description': idea.initial_description,
            'status': 'draft',
            'conversation_history': [],
            'metadata': {}
        }
        
        logger.info(f"Attempting to create idea with data: {idea_data}")
        
        result = supabase.table('ideas').insert(idea_data).execute()
        
        logger.info(f"Insert result: {result}")
        
        if result.data:
            return IdeaResponse(**result.data[0])
        else:
            logger.error(f"Insert failed, no data returned. Result: {result}")
            raise HTTPException(status_code=500, detail="Failed to create idea")
            
    except HTTPException:
        # Re-raise HTTPException as-is (for 404, 403, etc.)
        raise
    except Exception as e:
        logger.error(f"Error creating idea: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e) if str(e) else "Failed to create idea")


@router.get("/ideas", response_model=List[IdeaResponse])
async def list_ideas(
    project_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """List ideas with optional filters"""
    try:
        # Build query
        query = supabase.table('ideas').select('*')
        
        # Filter by user's organizations
        if 'organization_id' in current_user:
            # User has organization_id in their context
            query = query.eq('organization_id', current_user['organization_id'])
        else:
            # Fallback to querying organization_members
            org_result = supabase.table('organization_members').select(
                'organization_id'
            ).eq('user_id', current_user.get('app_user_id', current_user['user_id'])).execute()
            
            if org_result.data:
                org_ids = [row['organization_id'] for row in org_result.data]
                query = query.in_('organization_id', org_ids)
            else:
                return []
        
        # Apply filters
        if project_id:
            query = query.eq('project_id', str(project_id))
        if status:
            query = query.eq('status', status)
        
        # Apply pagination and ordering
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        
        result = query.execute()
        
        return [IdeaResponse(**idea) for idea in result.data]
        
    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        logger.error(f"Error listing ideas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ideas/{idea_id}", response_model=IdeaResponse)
async def get_idea(
    idea_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """Get a specific idea"""
    try:
        result = supabase.table('ideas').select('*').eq('id', str(idea_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        idea = result.data[0]
        
        # Verify user has access
        org_result = supabase.table('organization_members').select(
            'organization_id'
        ).eq('user_id', current_user.get('app_user_id', current_user['user_id'])).eq(
            'organization_id', idea['organization_id']
        ).execute()
        
        if not org_result.data:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return IdeaResponse(**idea)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting idea: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/ideas/{idea_id}", response_model=IdeaResponse)
async def update_idea(
    idea_id: UUID,
    update: IdeaUpdate,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """Update an idea"""
    try:
        # Get the idea first
        idea_result = supabase.table('ideas').select('*').eq('id', str(idea_id)).execute()
        
        if not idea_result.data:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        idea = idea_result.data[0]
        
        # Verify user owns the idea
        if idea['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Can only update your own ideas")
        
        # Build update data
        update_data = {}
        if update.title is not None:
            update_data['title'] = update.title
        if update.refined_description is not None:
            update_data['refined_description'] = update.refined_description
        if update.status is not None:
            update_data['status'] = update.status
        
        if update_data:
            result = supabase.table('ideas').update(update_data).eq(
                'id', str(idea_id)
            ).execute()
            
            if result.data:
                return IdeaResponse(**result.data[0])
        
        return IdeaResponse(**idea)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating idea: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ideas/{idea_id}")
async def delete_idea(
    idea_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """Delete an idea"""
    try:
        # Get the idea first
        idea_result = supabase.table('ideas').select('*').eq('id', str(idea_id)).execute()
        
        if not idea_result.data:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        idea = idea_result.data[0]
        
        # Verify user owns the idea and it's not converted
        if idea['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Can only delete your own ideas")
        
        if idea['status'] == 'converted':
            raise HTTPException(status_code=400, detail="Cannot delete converted ideas")
        
        # Delete the idea
        supabase.table('ideas').delete().eq('id', str(idea_id)).execute()
        
        return {"message": "Idea deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting idea: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ideas/{idea_id}/refine", response_model=RefineIdeaResponse)
async def refine_idea(
    idea_id: UUID,
    request: RefineIdeaRequest,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """Continue refining an idea through conversation"""
    try:
        # Get the idea
        idea_result = supabase.table('ideas').select('*').eq('id', str(idea_id)).execute()
        
        if not idea_result.data:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        idea = idea_result.data[0]
        
        # Verify user has access
        if idea['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Can only refine your own ideas")
        
        # Get organization and project context
        context = await _get_idea_context(idea, supabase)
        
        # Update conversation history
        conversation_history = idea.get('conversation_history', [])
        conversation_history.append({
            'role': 'user',
            'content': request.message,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Use the idea assistant to refine
        crew: IdeaAssistantCrew = get_agent('idea_assistant')
        
        refinement_input = IdeaRefinementInput(
            idea_description=idea['initial_description'],
            conversation_history=conversation_history,
            context=context
        )
        
        result = crew.refine_idea(refinement_input)
        
        # Extract the response
        output = result.result
        response_text = output['output']
        questions = output.get('questions', [])
        
        # Add assistant response to history
        conversation_history.append({
            'role': 'assistant',
            'content': response_text,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        # Update the idea with new conversation history and status
        update_data = {
            'conversation_history': conversation_history,
            'status': 'refining'
        }
        
        # If the response contains a refined description, update it
        if "refined idea" in response_text.lower():
            update_data['refined_description'] = response_text
        
        supabase.table('ideas').update(update_data).eq('id', str(idea_id)).execute()
        
        return RefineIdeaResponse(
            response=response_text,
            questions=questions,
            refined_description=update_data.get('refined_description')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refining idea: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ideas/{idea_id}/validate", response_model=ValidateIdeaResponse)
async def validate_idea(
    idea_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """Validate an idea"""
    try:
        # Get the idea
        idea_result = supabase.table('ideas').select('*').eq('id', str(idea_id)).execute()
        
        if not idea_result.data:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        idea = idea_result.data[0]
        
        # Verify user has access
        if idea['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Can only validate your own ideas")
        
        # Get the refined description or use initial
        idea_description = idea.get('refined_description') or idea['initial_description']
        
        # Get context
        context = await _get_idea_context(idea, supabase)
        
        # Use the idea assistant to validate
        crew: IdeaAssistantCrew = get_agent('idea_assistant')
        
        validation_input = IdeaValidationInput(
            refined_idea=idea_description,
            context=context
        )
        
        result = crew.validate_idea(validation_input)
        
        # Extract validation results
        output = result.result
        validation_score = output['validation_score']
        validation_reasons = output['validation_reasons']
        
        # Update the idea with validation results
        update_data = {
            'status': 'validated' if validation_score >= 0.6 else 'rejected',
            'validation_score': validation_score,
            'validation_reasons': validation_reasons
        }
        
        supabase.table('ideas').update(update_data).eq('id', str(idea_id)).execute()
        
        # Determine recommendation
        if validation_score >= 0.8:
            recommendation = "Highly recommended - proceed with implementation"
        elif validation_score >= 0.6:
            recommendation = "Recommended with considerations"
        else:
            recommendation = "Not recommended - needs significant refinement"
        
        return ValidateIdeaResponse(
            validation_score=validation_score,
            validation_reasons=validation_reasons,
            recommendation=recommendation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating idea: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ideas/{idea_id}/convert", response_model=ConvertToTasksResponse)
async def convert_to_tasks(
    idea_id: UUID,
    current_user: dict = Depends(get_current_user),
    supabase=Depends(get_supabase_client)
):
    """Convert a validated idea to tasks"""
    try:
        # Get the idea
        idea_result = supabase.table('ideas').select('*').eq('id', str(idea_id)).execute()
        
        if not idea_result.data:
            raise HTTPException(status_code=404, detail="Idea not found")
        
        idea = idea_result.data[0]
        
        # Verify user has access and idea is validated
        if idea['user_id'] != current_user['user_id']:
            raise HTTPException(status_code=403, detail="Can only convert your own ideas")
        
        if idea['status'] not in ['validated', 'refining']:
            raise HTTPException(
                status_code=400, 
                detail="Idea must be validated before conversion"
            )
        
        # Get context including project info
        context = await _get_idea_context(idea, supabase)
        
        # Use the idea assistant to generate tasks
        crew: IdeaAssistantCrew = get_agent('idea_assistant')
        
        task_input = TaskGenerationInput(
            validated_idea=idea.get('refined_description') or idea['initial_description'],
            validation_score=idea.get('validation_score', 0.8),
            project_context=context
        )
        
        result = crew.generate_tasks(task_input)
        
        # Extract generated tasks
        output = result.result
        generated_tasks = output['generated_tasks']
        
        # For now, we'll store the generated tasks in the idea's metadata
        # since the tasks table requires a goal_id which we don't have
        
        # Update idea status and store generated tasks
        update_data = {
            'status': 'converted',
            'metadata': {
                'generated_tasks': generated_tasks,
                'converted_at': datetime.utcnow().isoformat()
            }
        }
        
        supabase.table('ideas').update(update_data).eq('id', str(idea_id)).execute()
        
        # Return the generated tasks
        # In a real implementation, these would be created as actual task records
        # when the user assigns them to a specific goal/project
        return ConvertToTasksResponse(
            tasks_created=len(generated_tasks),
            task_ids=[],  # No actual task IDs since we're not creating database records
            tasks=generated_tasks
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error converting idea to tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


async def _get_idea_context(idea: dict, supabase) -> Dict[str, Any]:
    """Get context for an idea including organization and project info"""
    context = {}
    
    # Get organization info
    org_result = supabase.table('organizations').select('*').eq(
        'id', idea['organization_id']
    ).execute()
    
    if org_result.data:
        org = org_result.data[0]
        context['organization_name'] = org.get('name')
        context['industry'] = org.get('industry')
        context['company_size'] = org.get('company_size')
        # Add more org fields as needed
    
    # Get project info if applicable
    if idea['project_id']:
        project_result = supabase.table('projects').select('*').eq(
            'id', idea['project_id']
        ).execute()
        
        if project_result.data:
            project = project_result.data[0]
            context['project_name'] = project.get('name')
            context['project_type'] = project.get('type')
            context['budget'] = project.get('budget')
            context['timeline'] = project.get('timeline')
            
            # Get project goals
            goals_result = supabase.table('goals').select('*').eq(
                'project_id', idea['project_id']
            ).eq('status', 'active').execute()
            
            if goals_result.data:
                context['goals'] = [
                    {'title': g['title'], 'description': g['description']}
                    for g in goals_result.data
                ]
    
    return context