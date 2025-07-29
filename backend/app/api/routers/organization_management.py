"""Router for organization management AI agents"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.core.dependencies import (
    get_organization_goal_crew,
    get_department_structure_crew,
    get_project_description_crew,
    get_project_task_crew,
    get_supabase_client
)
from app.core.supabase_auth import get_current_user
from app.agents.crews.organization_goal_crew import OrganizationGoalInput
from app.agents.crews.department_structure_crew import DepartmentStructureInput
from app.agents.crews.project_description_crew import ProjectDescriptionInput
from app.agents.crews.project_task_crew import ProjectTaskInput

import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/organization-management",
    tags=["organization-management"]
)


class OrganizationGoalRequest(BaseModel):
    description: str
    user_feedback: Optional[str] = None
    previous_result: Optional[str] = None


class DepartmentStructureRequest(BaseModel):
    organization_description: str
    organization_goals: Optional[List[str]] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    user_feedback: Optional[str] = None
    previous_result: Optional[List[Dict]] = None


class ProjectDescriptionRequest(BaseModel):
    raw_description: str
    organization_purpose: str
    organization_goals: List[str]
    department: Optional[str] = None
    user_feedback: Optional[str] = None
    previous_result: Optional[Dict] = None


class ProjectTaskRequest(BaseModel):
    project_description: str
    project_objectives: List[str]
    project_milestones: List[Dict]
    organization_context: str
    department: Optional[str] = None
    team_size: Optional[int] = None
    timeline: Optional[str] = None
    user_feedback: Optional[str] = None
    previous_tasks: Optional[List[Dict]] = None


@router.post("/improve-organization-goals")
async def improve_organization_goals(
    request: OrganizationGoalRequest,
    current_user: dict = Depends(get_current_user),
    goal_crew = Depends(get_organization_goal_crew)
) -> Dict[str, Any]:
    """
    Improve organization description and define clear goals
    """
    try:
        logger.info(f"[ORG_GOALS] User {current_user['user_id']} improving organization goals")
        
        input_data = OrganizationGoalInput(
            description=request.description,
            user_feedback=request.user_feedback,
            previous_result=request.previous_result
        )
        
        result = goal_crew.run(input_data)
        
        if result.success:
            logger.info(f"[ORG_GOALS] Successfully improved organization goals")
            return {
                "success": True,
                "data": result.result,
                "message": result.message
            }
        else:
            logger.error(f"[ORG_GOALS] Failed: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
            
    except Exception as e:
        logger.error(f"[ORG_GOALS] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve organization goals: {str(e)}"
        )


@router.post("/suggest-departments")
async def suggest_departments(
    request: DepartmentStructureRequest,
    current_user: dict = Depends(get_current_user),
    structure_crew = Depends(get_department_structure_crew)
) -> Dict[str, Any]:
    """
    Suggest optimal department structure for the organization
    """
    try:
        logger.info(f"[DEPT_STRUCTURE] User {current_user['user_id']} requesting department suggestions")
        
        input_data = DepartmentStructureInput(
            organization_description=request.organization_description,
            organization_goals=request.organization_goals,
            industry=request.industry,
            company_size=request.company_size,
            user_feedback=request.user_feedback,
            previous_result=request.previous_result
        )
        
        result = structure_crew.run(input_data)
        
        if result.success:
            logger.info(f"[DEPT_STRUCTURE] Successfully created department structure")
            return {
                "success": True,
                "data": result.result,
                "message": result.message
            }
        else:
            logger.error(f"[DEPT_STRUCTURE] Failed: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
            
    except Exception as e:
        logger.error(f"[DEPT_STRUCTURE] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest departments: {str(e)}"
        )


@router.post("/enhance-project-description")
async def enhance_project_description(
    request: ProjectDescriptionRequest,
    current_user: dict = Depends(get_current_user),
    description_crew = Depends(get_project_description_crew)
) -> Dict[str, Any]:
    """
    Enhance project description with objectives, KPIs, and milestones
    """
    try:
        logger.info(f"[PROJECT_DESC] User {current_user['user_id']} enhancing project description")
        
        input_data = ProjectDescriptionInput(
            raw_description=request.raw_description,
            organization_purpose=request.organization_purpose,
            organization_goals=request.organization_goals,
            department=request.department,
            user_feedback=request.user_feedback,
            previous_result=request.previous_result
        )
        
        result = description_crew.run(input_data)
        
        if result.success:
            logger.info(f"[PROJECT_DESC] Successfully enhanced project description")
            return {
                "success": True,
                "data": result.result,
                "message": result.message
            }
        else:
            logger.error(f"[PROJECT_DESC] Failed: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
            
    except Exception as e:
        logger.error(f"[PROJECT_DESC] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enhance project description: {str(e)}"
        )


@router.post("/generate-project-tasks")
async def generate_project_tasks(
    request: ProjectTaskRequest,
    current_user: dict = Depends(get_current_user),
    task_crew = Depends(get_project_task_crew)
) -> Dict[str, Any]:
    """
    Generate comprehensive task list for a project
    """
    try:
        logger.info(f"[PROJECT_TASKS] User {current_user['user_id']} generating project tasks")
        
        input_data = ProjectTaskInput(
            project_description=request.project_description,
            project_objectives=request.project_objectives,
            project_milestones=request.project_milestones,
            organization_context=request.organization_context,
            department=request.department,
            team_size=request.team_size,
            timeline=request.timeline,
            user_feedback=request.user_feedback,
            previous_tasks=request.previous_tasks
        )
        
        result = task_crew.run(input_data)
        
        if result.success:
            logger.info(f"[PROJECT_TASKS] Successfully generated project tasks")
            return {
                "success": True,
                "data": result.result,
                "message": result.message
            }
        else:
            logger.error(f"[PROJECT_TASKS] Failed: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message
            )
            
    except Exception as e:
        logger.error(f"[PROJECT_TASKS] Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate project tasks: {str(e)}"
        )