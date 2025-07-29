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


class Department(BaseModel):
    name: str
    description: str
    goals: List[str]
    key_responsibilities: List[str]


class DepartmentStructureInput(BaseModel):
    organization_description: str
    organization_goals: Optional[List[str]] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    user_feedback: Optional[str] = None
    previous_result: Optional[List[Dict]] = None


class DepartmentStructureOutput(BaseModel):
    departments: List[Department]
    rationale: str


class DepartmentStructureCrew(BaseCrew):
    """Crew for creating optimal department structures"""
    
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
        """Create the department structure specialist agent"""
        structure_specialist = Agent(
            role='Organizational Structure Specialist',
            goal='Design optimal department structures that align with organizational goals and enable efficient operations',
            backstory="""You are a seasoned organizational design consultant with expertise 
            in creating efficient department structures for companies of all sizes. You have 
            helped hundreds of organizations optimize their structure to improve collaboration, 
            reduce silos, and achieve their strategic goals. You understand that the right 
            organizational structure is critical for operational excellence and growth.""",
            tools=[],
            llm=self.llm,
            verbose=True
        )
        
        return [structure_specialist]
    
    def _create_tasks(self, input_data: DepartmentStructureInput) -> List[Task]:
        """Create tasks for department structure design"""
        context = f"Organization: {input_data.organization_description}"
        if input_data.organization_goals:
            context += f"\nGoals: {', '.join(input_data.organization_goals)}"
        if input_data.industry:
            context += f"\nIndustry: {input_data.industry}"
        if input_data.company_size:
            context += f"\nCompany size: {input_data.company_size}"
            
        if input_data.user_feedback and input_data.previous_result:
            context += f"\n\nPrevious departments: {json.dumps(input_data.previous_result)}"
            context += f"\nUser feedback: {input_data.user_feedback}"
        
        structure_task = Task(
            description=f"""Design an optimal department structure for the organization.
            
            Context: {context}
            
            Your task is to:
            1. Analyze the organization's description and goals
            2. Consider industry best practices and company size
            3. Design a department structure that:
               - Aligns with organizational goals
               - Minimizes silos and promotes collaboration
               - Clearly defines responsibilities
               - Is scalable for growth
            4. For each department, provide:
               - A clear, concise name
               - A comprehensive description of purpose and scope
               - 3-5 specific departmental goals
               - Key responsibilities (4-6 items)
            
            If user feedback is provided, adjust the structure accordingly.
            
            Create between 4-8 departments depending on organization size and complexity.""",
            expected_output="""A JSON object containing:
            - departments: Array of department objects, each with:
              - name: Department name
              - description: Detailed description of department purpose
              - goals: List of 3-5 department-specific goals
              - key_responsibilities: List of 4-6 main responsibilities
            - rationale: Brief explanation of why this structure was chosen""",
            agent=self.agents[0]
        )
        
        return [structure_task]
    
    def run(self, input_data: DepartmentStructureInput) -> CrewOutput:
        """Run the department structure crew"""
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
                    
                output = DepartmentStructureOutput(**parsed_result)
                
                return CrewOutput(
                    success=True,
                    result=output.dict(),
                    message="Department structure created successfully"
                )
            except Exception as e:
                logger.error(f"Failed to parse result: {e}")
                # Provide a default structure if parsing fails
                return CrewOutput(
                    success=True,
                    result={
                        "departments": [
                            {
                                "name": "Leadership",
                                "description": "Executive leadership and strategic direction",
                                "goals": ["Set strategic vision", "Ensure organizational alignment"],
                                "key_responsibilities": ["Strategic planning", "Resource allocation"]
                            }
                        ],
                        "rationale": "Basic structure provided due to parsing error"
                    },
                    message="Structure generated but parsing failed"
                )
                
        except Exception as e:
            logger.error(f"DepartmentStructureCrew error: {str(e)}")
            return CrewOutput(
                success=False,
                result=None,
                message=f"Failed to create department structure: {str(e)}"
            )