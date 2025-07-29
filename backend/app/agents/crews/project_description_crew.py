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


class KeyResult(BaseModel):
    metric: str
    target: str
    timeframe: str
    measurement_method: str


class Milestone(BaseModel):
    name: str
    description: str
    deliverables: List[str]
    estimated_completion: str
    success_criteria: List[str]


class ProjectDescriptionInput(BaseModel):
    raw_description: str
    organization_purpose: str
    organization_goals: List[str]
    department: Optional[str] = None
    user_feedback: Optional[str] = None
    previous_result: Optional[Dict] = None


class ProjectDescriptionOutput(BaseModel):
    project_name: str
    executive_summary: str
    detailed_description: str
    objectives: List[str]
    key_results: List[KeyResult]
    milestones: List[Milestone]
    success_factors: List[str]
    risks_and_mitigations: Dict[str, str]


class ProjectDescriptionCrew(BaseCrew):
    """Crew for improving project descriptions and defining KPIs"""
    
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
        """Create the project planning specialist agent"""
        project_specialist = Agent(
            role='Project Strategy and Planning Expert',
            goal='Transform raw project ideas into comprehensive, actionable project plans with clear objectives and measurable outcomes',
            backstory="""You are a certified Project Management Professional (PMP) with 
            extensive experience in strategic project planning across various industries. 
            You excel at taking vague project ideas and turning them into well-structured 
            plans with clear objectives, measurable key results (OKRs), and achievable 
            milestones. You understand that successful projects require clarity of purpose, 
            measurable outcomes, and realistic planning.""",
            tools=[],
            llm=self.llm,
            verbose=True
        )
        
        return [project_specialist]
    
    def _create_tasks(self, input_data: ProjectDescriptionInput) -> List[Task]:
        """Create tasks for project description enhancement"""
        context = f"""Raw project description: {input_data.raw_description}
        Organization purpose: {input_data.organization_purpose}
        Organization goals: {', '.join(input_data.organization_goals)}"""
        
        if input_data.department:
            context += f"\nDepartment: {input_data.department}"
            
        if input_data.user_feedback and input_data.previous_result:
            context += f"\n\nPrevious result: {json.dumps(input_data.previous_result)}"
            context += f"\nUser feedback: {input_data.user_feedback}"
        
        enhance_task = Task(
            description=f"""Create a comprehensive project description with measurable outcomes.
            
            Context: {context}
            
            Your task is to:
            1. Analyze the raw project description and organizational context
            2. Create a compelling project name and executive summary
            3. Write a detailed description that clearly explains:
               - What the project will accomplish
               - Why it's important to the organization
               - How it aligns with organizational goals
            4. Define 3-5 clear, specific objectives
            5. Create measurable key results for each objective using the OKR framework:
               - Specific metrics with targets
               - Realistic timeframes
               - Clear measurement methods
            6. Define 3-4 major milestones with:
               - Clear deliverables
               - Estimated completion dates
               - Success criteria
            7. Identify critical success factors
            8. Assess potential risks and propose mitigations
            
            If user feedback is provided, incorporate it to improve the previous result.
            
            Ensure all elements are specific, measurable, achievable, relevant, and time-bound (SMART).""",
            expected_output="""A JSON object containing:
            - project_name: Compelling, descriptive project name
            - executive_summary: 2-3 paragraph summary of the project
            - detailed_description: Comprehensive project description
            - objectives: List of 3-5 clear project objectives
            - key_results: Array of measurable key results with metric, target, timeframe, and measurement_method
            - milestones: Array of project milestones with deliverables and success criteria
            - success_factors: List of critical factors for project success
            - risks_and_mitigations: Dictionary of potential risks and their mitigations""",
            agent=self.agents[0]
        )
        
        return [enhance_task]
    
    def run(self, input_data: ProjectDescriptionInput) -> CrewOutput:
        """Run the project description crew"""
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
                    
                output = ProjectDescriptionOutput(**parsed_result)
                
                return CrewOutput(
                    success=True,
                    result=output.dict(),
                    message="Project description enhanced successfully"
                )
            except Exception as e:
                logger.error(f"Failed to parse result: {e}")
                return CrewOutput(
                    success=True,
                    result={
                        "project_name": "Project Enhancement in Progress",
                        "executive_summary": str(result)[:500] if result else "Summary being generated",
                        "detailed_description": str(result) if result else "Description being enhanced",
                        "objectives": ["Objective definition in progress"],
                        "key_results": [],
                        "milestones": [],
                        "success_factors": ["To be defined"],
                        "risks_and_mitigations": {}
                    },
                    message="Project description generated but parsing failed"
                )
                
        except Exception as e:
            logger.error(f"ProjectDescriptionCrew error: {str(e)}")
            return CrewOutput(
                success=False,
                result=None,
                message=f"Failed to enhance project description: {str(e)}"
            )