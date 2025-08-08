"""
Idea Assistant Crew for refining, validating, and converting ideas to tasks
"""
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from crewai import Task
from pydantic import BaseModel, Field

from .base_crew import BaseCrew, CrewOutput

logger = logging.getLogger(__name__)


class IdeaRefinementInput(BaseModel):
    """Input model for idea refinement"""
    idea_description: str = Field(..., description="The initial idea description")
    conversation_history: List[Dict[str, str]] = Field(
        default_factory=list, 
        description="Previous conversation messages"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context (project info, organization goals, etc.)"
    )


class IdeaValidationInput(BaseModel):
    """Input model for idea validation"""
    refined_idea: str = Field(..., description="The refined idea description")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Organization and project context"
    )


class TaskGenerationInput(BaseModel):
    """Input model for task generation"""
    validated_idea: str = Field(..., description="The validated idea")
    validation_score: float = Field(..., description="Validation score")
    project_context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Project structure and constraints"
    )


class ConversationMessage(BaseModel):
    """Model for conversation messages"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[datetime] = None


class IdeaAssistantCrew(BaseCrew):
    """Crew for processing ideas through refinement, validation, and task generation"""
    
    def __init__(self):
        super().__init__()
        # Load specific configuration files for idea assistant
        self.idea_agents_config = self._load_yaml('idea_assistant_agents.yaml')
        self.idea_tasks_config = self._load_yaml('idea_assistant_tasks.yaml')
        self.idea_crews_config = self._load_yaml('idea_assistant_crews.yaml')
        
        # Create agent instances
        self.agents = {}
        for agent_name, agent_config in self.idea_agents_config.items():
            self.agents[agent_name] = self._create_agent_from_config(agent_name, agent_config)
        
        # Store tasks and crews configuration
        self.tasks = self.idea_tasks_config
        self.crews_config = self.idea_crews_config  # Make crews config available to parent
        self.conversation_history: List[ConversationMessage] = []
    
    def _create_agent_from_config(self, agent_name: str, config: Dict[str, Any]) -> Any:
        """Create an agent from configuration"""
        from crewai import Agent
        from langchain_openai import ChatOpenAI
        from app.core.config import settings
        
        llm = ChatOpenAI(
            model=config.get('llm', {}).get('model', 'gpt-4o-mini'),
            temperature=config.get('llm', {}).get('temperature', 0.7),
            api_key=settings.OPENAI_API_KEY
        )
        
        return Agent(
            role=config['role'],
            goal=config['goal'],
            backstory=config['backstory'],
            llm=llm,
            allow_delegation=config.get('allow_delegation', False),
            verbose=config.get('verbose', True),
            max_iter=config.get('max_iter', 5)
        )
    
    def refine_idea(self, input_data: IdeaRefinementInput) -> CrewOutput:
        """
        Refine a raw idea through conversational interaction
        """
        logger.info(f"Refining idea: {input_data.idea_description[:100]}...")
        
        # Build conversation context
        conversation_text = self._format_conversation_history(input_data.conversation_history)
        
        # Create the refinement task
        refine_task = Task(
            description=f"""
            Current idea: {input_data.idea_description}
            
            Previous conversation:
            {conversation_text}
            
            Context:
            - Organization: {input_data.context.get('organization_name', 'N/A')}
            - Project: {input_data.context.get('project_name', 'N/A')}
            - Goals: {json.dumps(input_data.context.get('goals', []))}
            
            Continue the conversation to refine this idea. Ask clarifying questions
            and help the user develop a clear, actionable proposal.
            """,
            agent=self.agents['idea_refiner'],
            expected_output=self.tasks['refine_idea']['expected_output']
        )
        
        crew = self.create_crew(
            crew_name='idea_assistant_crew',
            agents=[self.agents['idea_refiner']],
            tasks=[refine_task]
        )
        
        result = crew.kickoff()
        
        return CrewOutput(
            success=True,
            result={
                'task': 'refine_idea',
                'output': result.raw,
                'questions': self._extract_questions(result.raw)
            },
            message="Idea refined successfully"
        )
    
    def validate_idea(self, input_data: IdeaValidationInput) -> CrewOutput:
        """
        Validate a refined idea against multiple criteria
        """
        logger.info("Validating refined idea...")
        
        validate_task = Task(
            description=f"""
            Validate this idea: {input_data.refined_idea}
            
            Organization context:
            - Name: {input_data.context.get('organization_name', 'N/A')}
            - Industry: {input_data.context.get('industry', 'N/A')}
            - Size: {input_data.context.get('company_size', 'N/A')}
            - Goals: {json.dumps(input_data.context.get('goals', []))}
            
            Project context (if applicable):
            - Name: {input_data.context.get('project_name', 'N/A')}
            - Budget: {input_data.context.get('budget', 'N/A')}
            - Timeline: {input_data.context.get('timeline', 'N/A')}
            - Resources: {json.dumps(input_data.context.get('resources', []))}
            
            Provide a comprehensive validation with scoring.
            """,
            agent=self.agents['idea_validator'],
            expected_output=self.tasks['validate_idea']['expected_output']
        )
        
        crew = self.create_crew(
            crew_name='idea_assistant_crew',
            agents=[self.agents['idea_validator']],
            tasks=[validate_task]
        )
        
        result = crew.kickoff()
        
        # Extract validation score and reasons
        validation_data = self._parse_validation_result(result.raw)
        
        return CrewOutput(
            success=True,
            result={
                'task': 'validate_idea',
                'output': result.raw,
                'validation_score': validation_data['score'],
                'validation_reasons': validation_data['reasons']
            },
            message="Idea validated successfully"
        )
    
    def generate_tasks(self, input_data: TaskGenerationInput) -> CrewOutput:
        """
        Generate tasks from a validated idea
        """
        logger.info("Generating tasks from validated idea...")
        
        generate_task = Task(
            description=f"""
            Convert this validated idea into actionable tasks:
            {input_data.validated_idea}
            
            Validation score: {input_data.validation_score}
            
            Project constraints:
            - Timeline: {input_data.project_context.get('timeline', 'Flexible')}
            - Budget: {input_data.project_context.get('budget', 'To be determined')}
            - Team size: {input_data.project_context.get('team_size', 'Unknown')}
            - Existing tasks: {len(input_data.project_context.get('existing_tasks', []))}
            
            Create a comprehensive task breakdown with all required details.
            """,
            agent=self.agents['task_generator'],
            expected_output=self.tasks['generate_tasks']['expected_output']
        )
        
        crew = self.create_crew(
            crew_name='idea_assistant_crew',
            agents=[self.agents['task_generator']],
            tasks=[generate_task]
        )
        
        result = crew.kickoff()
        
        # Parse tasks from the result
        tasks = self._parse_generated_tasks(result.raw)
        
        return CrewOutput(
            success=True,
            result={
                'task': 'generate_tasks',
                'output': result.raw,
                'generated_tasks': tasks
            },
            message="Tasks generated successfully"
        )
    
    def process_idea_workflow(
        self, 
        idea_description: str, 
        context: Dict[str, Any],
        skip_validation: bool = False
    ) -> CrewOutput:
        """
        Process an idea through the complete workflow
        """
        logger.info("Starting complete idea workflow...")
        
        # Step 1: Refine the idea
        refinement_input = IdeaRefinementInput(
            idea_description=idea_description,
            conversation_history=[],
            context=context
        )
        refinement_result = self.refine_idea(refinement_input)
        refined_idea = refinement_result.tasks_output[0]['output']
        
        # Step 2: Validate the idea (unless skipped)
        if not skip_validation:
            validation_input = IdeaValidationInput(
                refined_idea=refined_idea,
                context=context
            )
            validation_result = self.validate_idea(validation_input)
            validation_score = validation_result.tasks_output[0]['validation_score']
            
            # Only proceed to task generation if validation score is high enough
            if validation_score < 0.6:
                return CrewOutput(
                    raw=f"Idea validation failed with score {validation_score}",
                    tasks_output=[
                        refinement_result.tasks_output[0],
                        validation_result.tasks_output[0]
                    ]
                )
        else:
            validation_score = 0.8  # Default score if validation is skipped
            validation_result = None
        
        # Step 3: Generate tasks
        task_input = TaskGenerationInput(
            validated_idea=refined_idea,
            validation_score=validation_score,
            project_context=context
        )
        task_result = self.generate_tasks(task_input)
        
        # Combine all results
        all_outputs = [refinement_result.tasks_output[0]]
        if validation_result:
            all_outputs.append(validation_result.tasks_output[0])
        all_outputs.append(task_result.tasks_output[0])
        
        return CrewOutput(
            raw=json.dumps({
                'refined_idea': refined_idea,
                'validation_score': validation_score,
                'generated_tasks': task_result.tasks_output[0]['generated_tasks']
            }),
            tasks_output=all_outputs
        )
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format conversation history for context"""
        if not history:
            return "No previous conversation"
        
        formatted = []
        for msg in history:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            formatted.append(f"{role.upper()}: {content}")
        
        return "\n".join(formatted)
    
    def _extract_questions(self, response: str) -> List[str]:
        """Extract questions from the refiner's response"""
        questions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.endswith('?'):
                questions.append(line)
        
        return questions
    
    def _parse_validation_result(self, result: str) -> Dict[str, Any]:
        """Parse validation score and reasons from the result"""
        try:
            # Look for score in the format "score: X.X" or "Score: X.X"
            import re
            score_match = re.search(r'(?:score|Score):\s*(\d+\.?\d*)', result)
            score = float(score_match.group(1)) if score_match else 0.5
            
            # Normalize score to 0-1 range if needed
            if score > 1:
                score = score / 100
            
            # Extract reasons (simplified - could be enhanced)
            reasons = {
                'alignment': 'Good' if 'align' in result.lower() else 'Unknown',
                'feasibility': 'High' if 'feasible' in result.lower() else 'Unknown',
                'resources': 'Available' if 'resource' in result.lower() else 'Unknown',
                'risks': 'Low' if 'low risk' in result.lower() else 'Unknown'
            }
            
            return {
                'score': score,
                'reasons': reasons
            }
        except Exception as e:
            logger.error(f"Error parsing validation result: {e}")
            return {
                'score': 0.5,
                'reasons': {'error': 'Failed to parse validation result'}
            }
    
    def _parse_generated_tasks(self, result: str) -> List[Dict[str, Any]]:
        """Parse generated tasks from the result"""
        tasks = []
        
        try:
            # Simple parser - looks for numbered tasks
            lines = result.split('\n')
            current_task = None
            
            for line in lines:
                line = line.strip()
                
                # Check if this is a new task (starts with number)
                if re.match(r'^\d+\.?\s+', line):
                    if current_task:
                        tasks.append(current_task)
                    
                    # Extract task title
                    title_match = re.match(r'^\d+\.?\s+(.+)', line)
                    current_task = {
                        'title': title_match.group(1) if title_match else line,
                        'description': '',
                        'effort': 'TBD',
                        'priority': 'medium'
                    }
                elif current_task and line:
                    # Add to current task description
                    current_task['description'] += line + ' '
            
            # Don't forget the last task
            if current_task:
                tasks.append(current_task)
            
            # Clean up descriptions
            for task in tasks:
                task['description'] = task['description'].strip()
                
                # Try to extract effort if mentioned
                effort_match = re.search(r'(\d+)\s*(hours?|days?|weeks?)', task['description'])
                if effort_match:
                    task['effort'] = effort_match.group(0)
                
                # Try to extract priority if mentioned
                if any(word in task['description'].lower() for word in ['high', 'critical', 'urgent']):
                    task['priority'] = 'high'
                elif any(word in task['description'].lower() for word in ['low', 'optional']):
                    task['priority'] = 'low'
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error parsing generated tasks: {e}")
            return [{
                'title': 'Failed to parse tasks',
                'description': result,
                'effort': 'Unknown',
                'priority': 'medium'
            }]
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for the idea assistant"""
        return {
            "status": "healthy",
            "crew": "IdeaAssistantCrew",
            "agents": list(self.agents.keys()),
            "tasks": list(self.tasks.keys())
        }