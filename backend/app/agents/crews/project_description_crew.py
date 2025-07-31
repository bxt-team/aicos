from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew
from .base_crew import BaseCrew, CrewOutput
# Tools removed - not needed for this agent
import json
import re
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
            expected_output="""Return ONLY a valid JSON object with no additional text or formatting. The JSON must contain:
            {
                "project_name": "Compelling, descriptive project name",
                "executive_summary": "2-3 paragraph summary of the project",
                "detailed_description": "Comprehensive project description", 
                "objectives": ["objective 1", "objective 2", "objective 3"],
                "key_results": [
                    {
                        "metric": "Name of the metric",
                        "target": "Specific target value",
                        "timeframe": "Time period",
                        "measurement_method": "How to measure"
                    }
                ],
                "milestones": [
                    {
                        "name": "Milestone name",
                        "description": "What this milestone achieves",
                        "deliverables": ["deliverable 1", "deliverable 2"],
                        "estimated_completion": "Date or timeframe",
                        "success_criteria": ["criterion 1", "criterion 2"]
                    }
                ],
                "success_factors": ["factor 1", "factor 2", "factor 3"],
                "risks_and_mitigations": {
                    "Risk description": "Mitigation strategy"
                }
            }
            
            IMPORTANT: Return ONLY the JSON object, no markdown formatting, no explanations.""",
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
            
            # Log the result type and content for debugging
            logger.info(f"Result type: {type(result)}")
            logger.info(f"Result content (first 500 chars): {str(result)[:500]}")
            
            # Handle CrewAI output object
            if hasattr(result, 'raw_output'):
                result = result.raw_output
            elif hasattr(result, 'output'):
                result = result.output
            
            # Parse the result
            try:
                # First, try to parse directly if it's already a dict
                if isinstance(result, dict):
                    parsed_result = result
                elif isinstance(result, str):
                    # Clean up the result string
                    result = result.strip()
                    
                    # Remove any leading/trailing whitespace or newlines
                    result = result.strip('\n\r\t ')
                    
                    # Handle nested JSON strings
                    if result.startswith('"') and result.endswith('"'):
                        try:
                            result = json.loads(result)  # Unwrap outer quotes
                        except:
                            # If it fails, just remove the quotes
                            result = result[1:-1]
                        
                    # Remove markdown code blocks
                    if result.startswith('```json'):
                        result = result[7:]
                    elif result.startswith('```'):
                        result = result[3:]
                    if result.endswith('```'):
                        result = result[:-3]
                    
                    # Clean up the string again after removing markdown
                    result = result.strip()
                    
                    # If it starts with { and ends with }, try direct parsing first
                    if result.startswith('{') and result.endswith('}'):
                        try:
                            parsed_result = json.loads(result)
                        except json.JSONDecodeError:
                            # If direct parsing fails, try regex extraction
                            # Look for a JSON object that starts with { and contains project_name
                            json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*"project_name"(?:[^{}]|(?:\{[^{}]*\}))*\}'
                            json_match = re.search(json_pattern, result, re.DOTALL)
                            if json_match:
                                result = json_match.group(0)
                                parsed_result = json.loads(result)
                            else:
                                raise ValueError("Could not extract valid JSON")
                    else:
                        # Try to extract JSON from the text
                        json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*"project_name"(?:[^{}]|(?:\{[^{}]*\}))*\}'
                        json_match = re.search(json_pattern, result, re.DOTALL)
                        if json_match:
                            result = json_match.group(0)
                            parsed_result = json.loads(result)
                        else:
                            raise ValueError("No JSON object found in result")
                else:
                    # Try to convert to dict if it's another type
                    if hasattr(result, '__dict__'):
                        parsed_result = result.__dict__
                    else:
                        parsed_result = {"raw_result": str(result)}
                
                # Validate and create output
                output = ProjectDescriptionOutput(**parsed_result)
                
                return CrewOutput(
                    success=True,
                    result=output.dict(),
                    message="Project description enhanced successfully"
                )
            except Exception as e:
                logger.error(f"Failed to parse result: {e}")
                logger.error(f"Raw result type: {type(result)}")
                logger.error(f"Raw result content: {result}")
                
                # Try to extract meaningful information from the text
                try:
                    # If the result contains a JSON string, try to extract it
                    if isinstance(result, str) and "{" in result and "}" in result:
                        # Find the JSON object in the string
                        start_idx = result.find("{")
                        end_idx = result.rfind("}") + 1
                        if start_idx >= 0 and end_idx > start_idx:
                            json_str = result[start_idx:end_idx]
                            parsed_result = json.loads(json_str)
                            
                            output = ProjectDescriptionOutput(**parsed_result)
                            return CrewOutput(
                                success=True,
                                result=output.dict(),
                                message="Project description enhanced successfully"
                            )
                except Exception as inner_e:
                    logger.error(f"Secondary parsing failed: {inner_e}")
                
                # Don't return the raw JSON as string in fields - it's confusing
                # Instead, return a clear error message
                return CrewOutput(
                    success=False,
                    result=None,
                    message=f"Failed to parse AI response: {str(e)}"
                )
                
        except Exception as e:
            logger.error(f"ProjectDescriptionCrew error: {str(e)}")
            return CrewOutput(
                success=False,
                result=None,
                message=f"Failed to enhance project description: {str(e)}"
            )