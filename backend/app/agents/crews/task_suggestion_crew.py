"""Crew for suggesting tasks based on goals"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from crewai import Crew, Task, Agent
from langchain_openai import ChatOpenAI
from .base_crew import BaseCrew
import logging
import json
from app.core.config import settings

logger = logging.getLogger(__name__)


class TaskSuggestionInput(BaseModel):
    goal_title: str
    goal_description: Optional[str] = None
    goal_target_date: Optional[str] = None
    project_description: Optional[str] = None
    existing_tasks: List[Dict[str, Any]] = []
    custom_prompt: Optional[str] = None
    historical_feedback: Optional[Dict[str, Any]] = None


class TaskSuggestion(BaseModel):
    title: str
    description: str
    priority: str  # low, medium, high, urgent
    estimated_duration: Optional[str] = None
    suggested_assignee_type: Optional[str] = None  # member, agent
    suggested_assignee_id: Optional[str] = None
    rationale: str
    dependencies: List[str] = []


class TaskSuggestionOutput(BaseModel):
    tasks: List[TaskSuggestion]
    breakdown_strategy: str


class TaskSuggestionCrew(BaseCrew):
    """Crew for generating task suggestions based on goals"""
    
    def __init__(self):
        # Skip BaseCrew init since we don't use YAML configs
        # Initialize attributes that BaseCrew would set
        self.config_dir = None
        self.agents_config = {}
        self.tasks_config = {}
        self.crews_config = {}
        self.cost_tracking_enabled = True
        self.session_costs = []
        self._context = None
        self.storage_adapter = None
        
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Create task breakdown specialist agent
        self.task_breakdown_specialist = Agent(
            role="Task Breakdown Specialist",
            goal="Break down goals into specific, actionable tasks with clear deliverables",
            backstory="You are an expert in project management and task decomposition. You excel at breaking down complex goals into manageable, concrete tasks that can be executed efficiently. You understand dependencies, priorities, and resource allocation.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Create execution strategist agent
        self.execution_strategist = Agent(
            role="Execution Strategy Expert",
            goal="Optimize task sequencing, priorities, and assignments for efficient goal achievement",
            backstory="You specialize in execution strategy and workflow optimization. You understand how to sequence tasks for maximum efficiency, identify critical paths, and suggest optimal task assignments based on complexity and dependencies.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Create task refinement agent
        self.task_refiner = Agent(
            role="Task Refinement Specialist",
            goal="Refine tasks to be specific, measurable, and actionable with clear success criteria",
            backstory="You are a detail-oriented specialist who ensures tasks are well-defined, measurable, and actionable. You focus on clarity, completeness, and ensuring each task has clear deliverables and success criteria.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def _extract_json_from_output(self, output: str) -> Dict[str, Any]:
        """Extract JSON from agent output"""
        try:
            # Try to parse the entire output as JSON first
            return json.loads(output)
        except:
            # Look for JSON blocks in the output
            import re
            json_pattern = r'\{[\s\S]*\}'
            matches = re.findall(json_pattern, output)
            
            for match in reversed(matches):  # Try from the last match first
                try:
                    return json.loads(match)
                except:
                    continue
            
            # If no JSON found, return a default structure
            logger.warning("Could not extract JSON from output, using default structure")
            return {
                "tasks": [],
                "breakdown_strategy": "Could not parse agent output"
            }
    
    def suggest_tasks(self, input_data: TaskSuggestionInput) -> TaskSuggestionOutput:
        """Generate task suggestions based on a goal"""
        try:
            # Task 1: Analyze goal and break down into tasks
            existing_context = ""
            if input_data.existing_tasks:
                existing_context = f"""
                Existing tasks for this goal:
                {json.dumps(input_data.existing_tasks, indent=2)}
                
                Consider these when suggesting new tasks to avoid duplication and ensure comprehensive coverage.
                """
            
            custom_criteria = input_data.custom_prompt if input_data.custom_prompt else """
                Focus on creating tasks that:
                1. Have clear, measurable deliverables
                2. Can be completed within reasonable timeframes
                3. Follow a logical progression toward the goal
                4. Include necessary research, planning, and validation steps
                """
            
            breakdown_task = Task(
                description=f"""
                Analyze the following goal and create specific tasks to achieve it:
                
                Goal Title: {input_data.goal_title}
                Goal Description: {input_data.goal_description or "No description provided"}
                Target Date: {input_data.goal_target_date or "No target date"}
                
                Project Context: {input_data.project_description or "No project description"}
                
                {existing_context}
                
                Task Generation Criteria:
                {custom_criteria}
                
                Generate 5-8 specific tasks that will systematically work toward achieving this goal.
                Consider the full lifecycle: planning, execution, validation, and documentation.
                """,
                agent=self.task_breakdown_specialist,
                expected_output="A comprehensive list of tasks with descriptions and rationale"
            )
            
            # Task 2: Optimize task sequencing and priorities
            feedback_context = ""
            if input_data.historical_feedback:
                fb = input_data.historical_feedback
                feedback_context = f"""
                Historical Feedback Analysis:
                - Average rating of previous suggestions: {fb.get('average_rating', 0):.1f}/5
                - Total feedback received: {fb.get('total_feedback', 0)}
                
                Based on this feedback, ensure tasks are:
                - Specific and actionable (not vague)
                - Appropriately sized (not too large or too small)
                - Logically sequenced with clear dependencies
                """
            
            sequencing_task = Task(
                description=f"""
                Based on the task breakdown, optimize the sequencing and priorities:
                
                {feedback_context}
                
                Consider:
                1. Task dependencies and prerequisites
                2. Critical path to goal achievement
                3. Quick wins vs. foundational work
                4. Resource requirements and complexity
                5. Risk factors and mitigation needs
                
                Assign appropriate priorities (urgent, high, medium, low) based on:
                - Impact on goal achievement
                - Time sensitivity
                - Dependency for other tasks
                - Risk mitigation importance
                """,
                agent=self.execution_strategist,
                expected_output="Optimized task sequence with priorities and dependencies identified"
            )
            
            # Task 3: Refine and format tasks
            refinement_task = Task(
                description=f"""
                Refine the tasks and format them for implementation:
                
                For each task:
                1. Ensure the title is clear and action-oriented (max 100 characters)
                2. Write a detailed description of what needs to be done
                3. Specify the priority (urgent, high, medium, low)
                4. Estimate duration (e.g., "2 hours", "1 day", "3 days", "1 week")
                5. Suggest assignee type (member for human tasks, agent for AI-suitable tasks)
                6. Provide a clear rationale for why this task is important
                7. List any dependencies on other tasks
                
                Return the result as a JSON object with this structure:
                {{
                    "tasks": [
                        {{
                            "title": "Task title",
                            "description": "Detailed description",
                            "priority": "high",
                            "estimated_duration": "2 days",
                            "suggested_assignee_type": "member",
                            "suggested_assignee_id": null,
                            "rationale": "Why this task matters",
                            "dependencies": ["dependency1", "dependency2"]
                        }}
                    ],
                    "breakdown_strategy": "Overall strategy for breaking down this goal into tasks"
                }}
                """,
                agent=self.task_refiner,
                expected_output="A JSON object containing refined tasks with all required fields"
            )
            
            # Create and run the crew
            crew = Crew(
                agents=[self.task_breakdown_specialist, self.execution_strategist, self.task_refiner],
                tasks=[breakdown_task, sequencing_task, refinement_task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Extract the JSON from the result
            if hasattr(result, 'raw_output'):
                output = result.raw_output
            elif hasattr(result, 'output'):
                output = result.output
            else:
                output = str(result)
            
            parsed_result = self._extract_json_from_output(output)
            
            # Validate and create output
            tasks = []
            for task_data in parsed_result.get("tasks", []):
                try:
                    # Ensure priority is valid
                    priority = task_data.get("priority", "medium").lower()
                    if priority not in ["low", "medium", "high", "urgent"]:
                        priority = "medium"
                    
                    task = TaskSuggestion(
                        title=task_data.get("title", "Untitled Task"),
                        description=task_data.get("description", ""),
                        priority=priority,
                        estimated_duration=task_data.get("estimated_duration"),
                        suggested_assignee_type=task_data.get("suggested_assignee_type"),
                        suggested_assignee_id=task_data.get("suggested_assignee_id"),
                        rationale=task_data.get("rationale", ""),
                        dependencies=task_data.get("dependencies", [])
                    )
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Error creating task suggestion: {e}")
            
            return TaskSuggestionOutput(
                tasks=tasks,
                breakdown_strategy=parsed_result.get("breakdown_strategy", "Tasks generated based on goal analysis")
            )
            
        except Exception as e:
            logger.error(f"Error in task suggestion crew: {e}")
            raise