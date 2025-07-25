from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, Field
from datetime import datetime

from ...core.dependencies import get_supabase_client
from ...core.dependencies import get_agent

router = APIRouter(prefix="/api/agent-tasks", tags=["agent-tasks"])


class AgentTaskCreate(BaseModel):
    goal_id: UUID
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[str] = Field("medium", pattern="^(low|medium|high|urgent)$")
    assign_to_agent: Optional[bool] = True  # Auto-assign to creating agent


class AgentTaskAssign(BaseModel):
    task_id: UUID
    assign_to_agent_id: Optional[str] = None  # If None, assign to self


class AgentTaskUpdate(BaseModel):
    task_id: UUID
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    notes: Optional[str] = None  # Agent's notes about progress


class AgentTaskBatch(BaseModel):
    goal_id: UUID
    tasks: List[Dict[str, Any]]  # Flexible task definitions


async def get_agent_id(x_agent_id: Optional[str] = Header(None)) -> str:
    """Extract agent ID from header."""
    if not x_agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Agent-ID header required for agent endpoints"
        )
    return x_agent_id


async def verify_agent_project_access(goal_id: str, agent_id: str, supabase) -> bool:
    """Verify agent has access to the goal's project."""
    # For now, we'll assume agents have access to all projects
    # In the future, this could check agent configurations or permissions
    return True


@router.get("/available", response_model=List[Dict[str, Any]])
async def get_available_tasks(
    status: Optional[str] = "pending",
    agent_id: str = Depends(get_agent_id)
):
    """Get tasks available for the agent to work on."""
    supabase = get_supabase_client()
    
    try:
        # Build query for unassigned or agent-assigned tasks
        query = supabase.table('tasks').select(
            '*, goals!inner(id, title, project_id, projects!inner(id, name, organization_id))'
        )
        
        if status:
            query = query.eq('status', status)
        
        # Get tasks that are either unassigned or assigned to this agent
        query = query.or_(
            f'assigned_to_type.is.null,and(assigned_to_type.eq.agent,assigned_to_id.eq.{agent_id})'
        )
        
        response = query.order('priority', desc=True).order('created_at').execute()
        
        tasks = []
        for task in response.data:
            task_dict = dict(task)
            
            # Flatten nested data
            if task.get('goals'):
                task_dict['goal_title'] = task['goals']['title']
                task_dict['goal_id'] = task['goals']['id']
                if task['goals'].get('projects'):
                    task_dict['project_id'] = task['goals']['projects']['id']
                    task_dict['project_name'] = task['goals']['projects']['name']
                    task_dict['organization_id'] = task['goals']['projects']['organization_id']
                del task_dict['goals']
            
            tasks.append(task_dict)
        
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available tasks: {str(e)}"
        )


@router.post("/create", response_model=Dict[str, Any])
async def create_task_as_agent(
    task: AgentTaskCreate,
    agent_id: str = Depends(get_agent_id)
):
    """Create a new task as an agent."""
    supabase = get_supabase_client()
    
    # Verify agent has access to the goal
    if not await verify_agent_project_access(str(task.goal_id), agent_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent does not have access to this goal"
        )
    
    try:
        agent_name = f"Agent-{agent_id[:8]}"
        
        task_data = {
            'goal_id': str(task.goal_id),
            'title': task.title,
            'description': task.description,
            'status': 'pending',
            'priority': task.priority,
            'created_by_type': 'agent',
            'created_by_id': agent_id,
            'created_by_name': agent_name
        }
        
        # Auto-assign to creating agent if requested
        if task.assign_to_agent:
            task_data['assigned_to_type'] = 'agent'
            task_data['assigned_to_id'] = agent_id
            task_data['assigned_to_name'] = agent_name
        
        response = supabase.table('tasks').insert(task_data).execute()
        created_task = response.data[0]
        
        # Create history entry
        history_data = {
            'task_id': created_task['id'],
            'action': 'created',
            'actor_type': 'agent',
            'actor_id': agent_id,
            'actor_name': agent_name,
            'new_value': task_data
        }
        supabase.table('task_history').insert(history_data).execute()
        
        return {
            'success': True,
            'task': created_task,
            'message': f'Task created successfully by {agent_name}'
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task: {str(e)}"
        )


@router.post("/assign", response_model=Dict[str, Any])
async def assign_task_as_agent(
    assignment: AgentTaskAssign,
    agent_id: str = Depends(get_agent_id)
):
    """Assign a task to an agent (self or another agent)."""
    supabase = get_supabase_client()
    
    try:
        # Get the task
        task_response = supabase.table('tasks').select('*, goals!inner(id)').eq(
            'id', str(assignment.task_id)
        ).single().execute()
        
        if not task_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task = task_response.data
        
        # Verify agent has access
        if not await verify_agent_project_access(task['goal_id'], agent_id, supabase):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Agent does not have access to this task"
            )
        
        # Determine target agent
        target_agent_id = assignment.assign_to_agent_id or agent_id
        target_agent_name = f"Agent-{target_agent_id[:8]}"
        assigning_agent_name = f"Agent-{agent_id[:8]}"
        
        # Update task assignment
        update_data = {
            'assigned_to_type': 'agent',
            'assigned_to_id': target_agent_id,
            'assigned_to_name': target_agent_name
        }
        
        supabase.table('tasks').update(update_data).eq(
            'id', str(assignment.task_id)
        ).execute()
        
        # Create history entry
        history_data = {
            'task_id': str(assignment.task_id),
            'action': 'assigned',
            'actor_type': 'agent',
            'actor_id': agent_id,
            'actor_name': assigning_agent_name,
            'old_value': {
                'assigned_to_type': task.get('assigned_to_type'),
                'assigned_to_id': task.get('assigned_to_id'),
                'assigned_to_name': task.get('assigned_to_name')
            },
            'new_value': update_data
        }
        supabase.table('task_history').insert(history_data).execute()
        
        return {
            'success': True,
            'message': f'Task assigned to {target_agent_name} by {assigning_agent_name}',
            'assignment': update_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign task: {str(e)}"
        )


@router.post("/update", response_model=Dict[str, Any])
async def update_task_as_agent(
    update: AgentTaskUpdate,
    agent_id: str = Depends(get_agent_id)
):
    """Update task status or add notes as an agent."""
    supabase = get_supabase_client()
    
    try:
        # Get the task
        task_response = supabase.table('tasks').select('*').eq(
            'id', str(update.task_id)
        ).single().execute()
        
        if not task_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        task = task_response.data
        
        # Verify agent is assigned or has access
        if task.get('assigned_to_type') == 'agent' and task.get('assigned_to_id') != agent_id:
            # Check if agent has general access
            if not await verify_agent_project_access(task['goal_id'], agent_id, supabase):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Agent is not assigned to this task"
                )
        
        agent_name = f"Agent-{agent_id[:8]}"
        update_data = {}
        changes = {}
        
        if update.status and update.status != task['status']:
            update_data['status'] = update.status
            changes['status'] = {'old': task['status'], 'new': update.status}
            
            if update.status == 'completed':
                update_data['completed_at'] = datetime.utcnow().isoformat()
        
        if update.notes:
            # Append notes to description
            current_desc = task.get('description', '')
            timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            new_desc = f"{current_desc}\n\n[{timestamp}] {agent_name}: {update.notes}"
            update_data['description'] = new_desc.strip()
            changes['notes_added'] = update.notes
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No updates provided"
            )
        
        # Update task
        supabase.table('tasks').update(update_data).eq(
            'id', str(update.task_id)
        ).execute()
        
        # Create history entry
        history_data = {
            'task_id': str(update.task_id),
            'action': 'updated',
            'actor_type': 'agent',
            'actor_id': agent_id,
            'actor_name': agent_name,
            'old_value': changes,
            'new_value': update_data
        }
        supabase.table('task_history').insert(history_data).execute()
        
        return {
            'success': True,
            'message': f'Task updated by {agent_name}',
            'updates': update_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.post("/batch-create", response_model=Dict[str, Any])
async def create_tasks_batch_as_agent(
    batch: AgentTaskBatch,
    agent_id: str = Depends(get_agent_id)
):
    """Create multiple tasks at once as an agent."""
    supabase = get_supabase_client()
    
    # Verify agent has access to the goal
    if not await verify_agent_project_access(str(batch.goal_id), agent_id, supabase):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent does not have access to this goal"
        )
    
    try:
        agent_name = f"Agent-{agent_id[:8]}"
        created_tasks = []
        
        for task_def in batch.tasks:
            task_data = {
                'goal_id': str(batch.goal_id),
                'title': task_def.get('title', 'Untitled Task'),
                'description': task_def.get('description'),
                'status': 'pending',
                'priority': task_def.get('priority', 'medium'),
                'created_by_type': 'agent',
                'created_by_id': agent_id,
                'created_by_name': agent_name
            }
            
            # Handle assignment
            if task_def.get('assign_to_agent', False):
                task_data['assigned_to_type'] = 'agent'
                task_data['assigned_to_id'] = task_def.get('agent_id', agent_id)
                task_data['assigned_to_name'] = f"Agent-{task_data['assigned_to_id'][:8]}"
            elif task_def.get('assign_to_employee_id'):
                # Look up employee name
                emp_response = supabase.table('employees').select('name').eq(
                    'id', task_def['assign_to_employee_id']
                ).single().execute()
                
                if emp_response.data:
                    task_data['assigned_to_type'] = 'employee'
                    task_data['assigned_to_id'] = task_def['assign_to_employee_id']
                    task_data['assigned_to_name'] = emp_response.data['name']
            
            response = supabase.table('tasks').insert(task_data).execute()
            created_task = response.data[0]
            created_tasks.append(created_task)
            
            # Create history entry
            history_data = {
                'task_id': created_task['id'],
                'action': 'created',
                'actor_type': 'agent',
                'actor_id': agent_id,
                'actor_name': agent_name,
                'new_value': task_data
            }
            supabase.table('task_history').insert(history_data).execute()
        
        return {
            'success': True,
            'message': f'{len(created_tasks)} tasks created by {agent_name}',
            'tasks': created_tasks
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tasks: {str(e)}"
        )


@router.get("/my-tasks", response_model=List[Dict[str, Any]])
async def get_agent_tasks(
    status: Optional[str] = None,
    agent_id: str = Depends(get_agent_id)
):
    """Get tasks assigned to the agent."""
    supabase = get_supabase_client()
    
    try:
        query = supabase.table('tasks').select(
            '*, goals!inner(id, title, project_id, projects!inner(id, name))'
        ).eq('assigned_to_type', 'agent').eq('assigned_to_id', agent_id)
        
        if status:
            query = query.eq('status', status)
        
        response = query.order('priority', desc=True).order('created_at').execute()
        
        tasks = []
        for task in response.data:
            task_dict = dict(task)
            
            # Flatten nested data
            if task.get('goals'):
                task_dict['goal_title'] = task['goals']['title']
                if task['goals'].get('projects'):
                    task_dict['project_id'] = task['goals']['projects']['id']
                    task_dict['project_name'] = task['goals']['projects']['name']
                del task_dict['goals']
            
            tasks.append(task_dict)
        
        return tasks
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get agent tasks: {str(e)}"
        )