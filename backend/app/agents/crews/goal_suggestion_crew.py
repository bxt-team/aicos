"""Crew for suggesting project goals based on project description and knowledge base"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from crewai import Crew, Task, Agent
from langchain_openai import ChatOpenAI
from .base_crew import BaseCrew
import logging
import json
from app.core.config import settings

logger = logging.getLogger(__name__)


class GoalSuggestionInput(BaseModel):
    project_description: str
    project_objectives: Optional[List[str]] = None
    organization_purpose: Optional[str] = None
    knowledge_files_content: Optional[str] = None
    user_feedback: Optional[str] = None
    previous_goals: Optional[List[Dict[str, Any]]] = None


class GoalSuggestion(BaseModel):
    title: str
    description: str
    target_date_suggestion: str
    priority: str
    rationale: str
    success_criteria: List[str]
    key_milestones: List[str]


class GoalSuggestionOutput(BaseModel):
    goals: List[GoalSuggestion]
    methodology_rationale: str


class GoalSuggestionCrew(BaseCrew):
    """Crew for generating goal suggestions based on project context"""
    
    def __init__(self):
        super().__init__()
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Create goal strategist agent
        self.goal_strategist = Agent(
            role="Goal Setting Strategist",
            goal="Analyze project context and suggest strategic, actionable goals that align with the 7 Cycles methodology",
            backstory="You are an expert in strategic planning and goal setting. You understand how to break down complex projects into achievable goals that follow SMART criteria (Specific, Measurable, Achievable, Relevant, Time-bound). You have deep knowledge of the 7 Cycles of Life methodology and how to apply it to business goals.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Create methodology expert agent
        self.methodology_expert = Agent(
            role="7 Cycles Methodology Expert",
            goal="Ensure goals align with the 7 Cycles of Life principles and extract relevant wisdom from knowledge base",
            backstory="You are a master of the 7 Cycles of Life methodology. You understand how each cycle relates to business growth and personal development. You can identify which cycle a project or goal belongs to and provide guidance based on the methodology's principles.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        # Create goal refinement agent
        self.goal_refiner = Agent(
            role="Goal Refinement Specialist",
            goal="Refine and prioritize goals based on feasibility, impact, and alignment with project objectives",
            backstory="You excel at taking rough goal ideas and refining them into clear, actionable objectives. You understand how to prioritize goals based on their potential impact and feasibility. You ensure goals are properly scoped and have clear success criteria.",
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
                "goals": [],
                "methodology_rationale": "Could not parse agent output"
            }
    
    def suggest_goals(self, input_data: GoalSuggestionInput) -> GoalSuggestionOutput:
        """Generate goal suggestions based on project context"""
        try:
            # Task 1: Analyze project and extract key themes
            analysis_task = Task(
                description=f"""
                Analyze the following project information and extract key themes, objectives, and areas that need goals:
                
                Project Description: {input_data.project_description}
                
                {f"Project Objectives: {', '.join(input_data.project_objectives)}" if input_data.project_objectives else ""}
                
                {f"Organization Purpose: {input_data.organization_purpose}" if input_data.organization_purpose else ""}
                
                {f"Available Knowledge Base Content: {input_data.knowledge_files_content[:2000]}..." if input_data.knowledge_files_content else ""}
                
                {f"User Feedback on Previous Suggestions: {input_data.user_feedback}" if input_data.user_feedback else ""}
                
                Identify 3-5 key areas where goals should be set. Consider both short-term milestones and long-term objectives.
                """,
                agent=self.goal_strategist,
                expected_output="A comprehensive analysis of the project with identified key areas for goal setting"
            )
            
            # Task 2: Apply 7 Cycles methodology
            methodology_task = Task(
                description="""
                Based on the project analysis, apply the 7 Cycles of Life methodology to ensure goals align with natural growth patterns.
                
                Consider:
                1. Which cycle(s) does this project represent?
                2. What wisdom from the knowledge base applies to these goals?
                3. How can goals be structured to follow natural progression?
                
                Provide methodology-based insights for goal setting.
                """,
                agent=self.methodology_expert,
                expected_output="Methodology-based insights and alignment with 7 Cycles principles"
            )
            
            # Task 3: Generate and refine specific goals
            goal_generation_task = Task(
                description=f"""
                Based on the analysis and methodology insights, generate 3-5 specific, actionable goals for this project.
                
                {f"Previous goals to improve upon: {json.dumps(input_data.previous_goals, indent=2)}" if input_data.previous_goals else ""}
                
                For each goal, provide:
                - A clear, concise title (max 100 characters)
                - A detailed description explaining what needs to be achieved
                - A suggested target date (relative timeframe like "3 months", "6 weeks", etc.)
                - Priority level (low, medium, high, urgent)
                - Rationale for why this goal is important
                - 3-5 specific success criteria (measurable outcomes)
                - 2-3 key milestones to track progress
                
                Ensure goals follow SMART criteria and are achievable within the project context.
                
                Return the result as a JSON object with this structure:
                {{
                    "goals": [
                        {{
                            "title": "Goal title",
                            "description": "Detailed description",
                            "target_date_suggestion": "3 months",
                            "priority": "high",
                            "rationale": "Why this goal matters",
                            "success_criteria": ["Criterion 1", "Criterion 2"],
                            "key_milestones": ["Milestone 1", "Milestone 2"]
                        }}
                    ],
                    "methodology_rationale": "How these goals align with the 7 Cycles methodology"
                }}
                """,
                agent=self.goal_refiner,
                expected_output="A JSON object containing refined, actionable goals with all required fields"
            )
            
            # Create and run the crew
            crew = Crew(
                agents=[self.goal_strategist, self.methodology_expert, self.goal_refiner],
                tasks=[analysis_task, methodology_task, goal_generation_task],
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
            goals = []
            for goal_data in parsed_result.get("goals", []):
                try:
                    goal = GoalSuggestion(
                        title=goal_data.get("title", "Untitled Goal"),
                        description=goal_data.get("description", ""),
                        target_date_suggestion=goal_data.get("target_date_suggestion", "3 months"),
                        priority=goal_data.get("priority", "medium"),
                        rationale=goal_data.get("rationale", ""),
                        success_criteria=goal_data.get("success_criteria", []),
                        key_milestones=goal_data.get("key_milestones", [])
                    )
                    goals.append(goal)
                except Exception as e:
                    logger.error(f"Error creating goal suggestion: {e}")
            
            return GoalSuggestionOutput(
                goals=goals,
                methodology_rationale=parsed_result.get("methodology_rationale", "Goals generated based on project analysis")
            )
            
        except Exception as e:
            logger.error(f"Error in goal suggestion crew: {e}")
            raise