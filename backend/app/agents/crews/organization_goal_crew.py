from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from crewai import Agent, Task, Crew
from .base_crew import BaseCrew, CrewOutput
# Tools removed - not needed for this agent
import json
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class OrganizationGoalInput(BaseModel):
    description: str
    user_feedback: Optional[str] = None
    previous_result: Optional[str] = None


class OrganizationGoalOutput(BaseModel):
    improved_description: str
    organization_purpose: str
    primary_goals: List[str]
    success_metrics: List[str]
    value_proposition: str


class OrganizationGoalCrew(BaseCrew):
    """Crew for improving organization descriptions and goals"""
    
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
        """Create the goal optimization agent"""
        goal_optimizer = Agent(
            role='Organization Strategy Specialist',
            goal='Transform raw organizational descriptions into comprehensive, strategic goal definitions',
            backstory="""You are an expert in organizational strategy and business development 
            with 20 years of experience helping companies define their purpose and goals. 
            You excel at taking vague ideas and transforming them into clear, actionable, 
            and inspiring organizational missions. You understand that well-defined goals 
            are the foundation of successful projects and initiatives.""",
            tools=[],
            llm=self.llm,
            verbose=True
        )
        
        return [goal_optimizer]
    
    def _create_tasks(self, input_data: OrganizationGoalInput) -> List[Task]:
        """Create tasks for goal optimization"""
        context = f"Raw description: {input_data.description}"
        if input_data.user_feedback and input_data.previous_result:
            context += f"\n\nPrevious result:\n{input_data.previous_result}\n\nUser feedback: {input_data.user_feedback}"
        
        optimize_task = Task(
            description=f"""Analyze and improve the organization description. 
            
            Context: {context}
            
            Your task is to:
            1. Understand the core purpose and vision from the raw description
            2. Expand and clarify the organizational purpose
            3. Define clear, measurable primary goals (3-5 goals)
            4. Identify success metrics for each goal
            5. Articulate the unique value proposition
            
            If user feedback is provided, incorporate it to improve the previous result.
            
            Return a comprehensive organizational profile that can serve as the foundation 
            for all projects and initiatives.""",
            expected_output="""A detailed JSON object containing:
            - improved_description: Enhanced, professional description of the organization
            - organization_purpose: Clear statement of why the organization exists
            - primary_goals: List of 3-5 specific, measurable goals
            - success_metrics: Metrics to measure progress for each goal
            - value_proposition: What makes this organization unique""",
            agent=self.agents[0]
        )
        
        return [optimize_task]
    
    def run(self, input_data: OrganizationGoalInput) -> CrewOutput:
        """Run the organization goal optimization crew"""
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
                # Handle different types of results from CrewAI
                if hasattr(result, 'output'):
                    # CrewOutput object
                    result_str = result.output
                elif hasattr(result, 'result'):
                    # Some other wrapper object
                    result_str = str(result.result)
                elif isinstance(result, dict):
                    # Already a dict, use it directly
                    parsed_result = result
                    result_str = None
                else:
                    # Convert to string
                    result_str = str(result)
                
                # If we have a string result, parse it
                if result_str is not None:
                    # Clean up the result string
                    result_str = result_str.strip()
                    if result_str.startswith('```json'):
                        result_str = result_str[7:]
                    if result_str.endswith('```'):
                        result_str = result_str[:-3]
                    
                    # Try to parse as JSON
                    try:
                        parsed_result = json.loads(result_str.strip())
                    except json.JSONDecodeError:
                        # If direct parsing fails, try to extract JSON from the string
                        import re
                        json_match = re.search(r'\{.*\}', result_str, re.DOTALL)
                        if json_match:
                            parsed_result = json.loads(json_match.group())
                        else:
                            raise ValueError("Could not extract JSON from result")
                    
                # Handle case where AI returns goals as objects instead of strings
                if isinstance(parsed_result.get('primary_goals', []), list) and len(parsed_result.get('primary_goals', [])) > 0:
                    first_goal = parsed_result['primary_goals'][0]
                    if isinstance(first_goal, dict) and 'goal' in first_goal:
                        # Extract just the goal text from objects
                        parsed_result['primary_goals'] = [
                            g['goal'] if isinstance(g, dict) else g 
                            for g in parsed_result['primary_goals']
                        ]
                
                # Handle case where AI returns success_metrics in different formats
                if 'success_metrics' in parsed_result:
                    metrics = parsed_result['success_metrics']
                    
                    if isinstance(metrics, dict):
                        # If it's a dictionary, convert values to a list
                        parsed_result['success_metrics'] = list(metrics.values())
                    elif isinstance(metrics, list) and len(metrics) > 0:
                        first_metric = metrics[0]
                        if isinstance(first_metric, dict) and 'metric' in first_metric:
                            # Extract just the metric text from objects
                            parsed_result['success_metrics'] = [
                                m['metric'] if isinstance(m, dict) else m 
                                for m in metrics
                            ]
                else:
                    # If no success_metrics provided, generate them from goals
                    parsed_result['success_metrics'] = [
                        f"Measure progress on: {goal}"
                        for goal in parsed_result.get('primary_goals', [])
                    ]
                
                output = OrganizationGoalOutput(**parsed_result)
                
                return CrewOutput(
                    success=True,
                    result=output.dict(),
                    message="Organization goals optimized successfully"
                )
            except Exception as e:
                logger.error(f"Failed to parse result: {e}")
                logger.error(f"Raw result was: {result}")
                
                # Try to provide a better fallback
                result_str = str(result) if not isinstance(result, str) else result
                
                # If the result looks like it contains valid content, extract what we can
                fallback_description = result_str[:500] if len(result_str) > 500 else result_str
                
                return CrewOutput(
                    success=True,
                    result={
                        "improved_description": "Your organization description is being processed. Please try again.",
                        "organization_purpose": "To be defined",
                        "primary_goals": ["Goal definition in progress"],
                        "success_metrics": ["Metrics to be defined"],
                        "value_proposition": "Value proposition in development"
                    },
                    message="Goals generated but parsing failed - please try again"
                )
                
        except Exception as e:
            logger.error(f"OrganizationGoalCrew error: {str(e)}")
            return CrewOutput(
                success=False,
                result=None,
                message=f"Failed to optimize organization goals: {str(e)}"
            )