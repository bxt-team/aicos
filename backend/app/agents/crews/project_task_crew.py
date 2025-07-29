from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew
from .base_crew import BaseCrew, CrewOutput
# Tools removed - not needed for this agent
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class ProjectTask(BaseModel):
    title: str
    description: str
    category: str
    priority: str  # high, medium, low
    estimated_hours: int
    dependencies: List[str]
    deliverables: List[str]
    acceptance_criteria: List[str]
    skills_required: List[str]


class ProjectTaskInput(BaseModel):
    project_description: str
    project_objectives: List[str]
    project_milestones: List[Dict]
    organization_context: str
    department: Optional[str] = None
    team_size: Optional[int] = None
    timeline: Optional[str] = None
    user_feedback: Optional[str] = None
    previous_tasks: Optional[List[Dict]] = None


class ProjectTaskOutput(BaseModel):
    tasks: List[ProjectTask]
    task_summary: Dict[str, int]  # Summary by category
    critical_path: List[str]  # Task titles in order
    resource_requirements: Dict[str, str]


class ProjectTaskCrew(BaseCrew):
    """Crew for generating comprehensive project task lists"""
    
    def __init__(self):
        super().__init__()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini", 
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY
        )
        
    def _create_agents(self) -> List[Agent]:
        """Create the task planning specialist agent"""
        task_specialist = Agent(
            role='Project Task Planning Specialist',
            goal='Break down projects into comprehensive, actionable task lists that ensure successful project delivery',
            backstory="""You are an expert in Work Breakdown Structure (WBS) creation 
            and task planning with experience across software development, business operations, 
            and project management. You excel at identifying all necessary tasks, their 
            dependencies, and creating realistic estimates. You understand that comprehensive 
            task planning is crucial for project success and helps teams work efficiently 
            toward their goals.""",
            tools=[],
            llm=self.llm,
            verbose=True
        )
        
        return [task_specialist]
    
    def _create_tasks(self, input_data: ProjectTaskInput) -> List[Task]:
        """Create tasks for project task generation"""
        context = f"""Project Description: {input_data.project_description}
        Objectives: {', '.join(input_data.project_objectives)}
        Milestones: {json.dumps(input_data.project_milestones)}
        Organization Context: {input_data.organization_context}"""
        
        if input_data.department:
            context += f"\nDepartment: {input_data.department}"
        if input_data.team_size:
            context += f"\nTeam Size: {input_data.team_size}"
        if input_data.timeline:
            context += f"\nTimeline: {input_data.timeline}"
            
        if input_data.user_feedback and input_data.previous_tasks:
            context += f"\n\nPrevious tasks: {json.dumps(input_data.previous_tasks)}"
            context += f"\nUser feedback: {input_data.user_feedback}"
        
        planning_task = Task(
            description=f"""Create a comprehensive task list for the project.
            
            Context: {context}
            
            Your task is to:
            1. Analyze the project description, objectives, and milestones
            2. Create a complete Work Breakdown Structure (WBS)
            3. For each task, define:
               - Clear, action-oriented title
               - Detailed description of what needs to be done
               - Category (e.g., Planning, Development, Testing, Documentation, etc.)
               - Priority level (high, medium, low)
               - Realistic time estimate in hours
               - Dependencies on other tasks (by title)
               - Specific deliverables
               - Clear acceptance criteria
               - Required skills or expertise
            4. Ensure tasks:
               - Cover all aspects needed to achieve objectives
               - Are sized appropriately (4-40 hours each)
               - Have clear dependencies identified
               - Include necessary planning, execution, and review tasks
            5. Identify the critical path through the project
            6. Summarize resource requirements
            
            If user feedback is provided, adjust the task list accordingly.
            
            Generate 15-40 tasks depending on project complexity.""",
            expected_output="""A JSON object containing:
            - tasks: Array of task objects with all specified fields
            - task_summary: Dictionary showing count of tasks by category
            - critical_path: Ordered list of task titles that form the critical path
            - resource_requirements: Dictionary of required resources and skills""",
            agent=self.agents[0]
        )
        
        return [planning_task]
    
    def run(self, input_data: ProjectTaskInput) -> CrewOutput:
        """Run the project task generation crew"""
        try:
            self.agents = self._create_agents()
            tasks = self._create_tasks(input_data)
            
            crew = Crew(
                agents=self.agents,
                tasks=tasks,
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                if isinstance(result, str):
                    # Clean up the result string
                    result = result.strip()
                    if result.startswith('```json'):
                        result = result[7:]
                    if result.endswith('```'):
                        result = result[:-3]
                    parsed_result = json.loads(result.strip())
                else:
                    parsed_result = result
                    
                output = ProjectTaskOutput(**parsed_result)
                
                return CrewOutput(
                    success=True,
                    result=output.dict(),
                    message="Project tasks generated successfully"
                )
            except Exception as e:
                logger.error(f"Failed to parse result: {e}")
                # Provide a basic task structure if parsing fails
                return CrewOutput(
                    success=True,
                    result={
                        "tasks": [
                            {
                                "title": "Project Planning",
                                "description": "Initial project planning and setup",
                                "category": "Planning",
                                "priority": "high",
                                "estimated_hours": 8,
                                "dependencies": [],
                                "deliverables": ["Project plan"],
                                "acceptance_criteria": ["Plan approved"],
                                "skills_required": ["Project management"]
                            }
                        ],
                        "task_summary": {"Planning": 1},
                        "critical_path": ["Project Planning"],
                        "resource_requirements": {"Project Manager": "Required"}
                    },
                    message="Tasks generated but parsing failed"
                )
                
        except Exception as e:
            logger.error(f"ProjectTaskCrew error: {str(e)}")
            return CrewOutput(
                success=False,
                result=None,
                message=f"Failed to generate project tasks: {str(e)}"
            )