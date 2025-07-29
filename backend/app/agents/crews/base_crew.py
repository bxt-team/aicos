from crewai import Agent, Task, Crew
from crewai.agent import Agent
from langchain_openai import ChatOpenAI
from langchain.callbacks.base import BaseCallbackHandler
import yaml
import os
from typing import Dict, Any, List, Optional
import logging
from uuid import UUID

from app.core.cost_tracker import cost_tracker, TokenUsage
from app.models.auth import RequestContext
from app.core.storage.base import StorageAdapter
from app.services.credit_service import CreditService
from app.core.exceptions import InsufficientCreditsError

logger = logging.getLogger(__name__)


class CrewOutput:
    """Simple output wrapper for crew results"""
    def __init__(self, success: bool, result: Any, message: str = ""):
        self.success = success
        self.result = result
        self.message = message


class CostTrackingCallback(BaseCallbackHandler):
    """Callback handler to track token usage for cost estimation"""
    
    def __init__(self, agent_name: str, task_description: Optional[str] = None):
        self.agent_name = agent_name
        self.task_description = task_description
        self.token_usage = TokenUsage()
        
    def on_llm_end(self, response, **kwargs):
        """Called when an LLM call ends"""
        if hasattr(response, 'llm_output') and response.llm_output:
            usage = response.llm_output.get('token_usage', {})
            if usage:
                self.token_usage.prompt_tokens += usage.get('prompt_tokens', 0)
                self.token_usage.completion_tokens += usage.get('completion_tokens', 0)
                self.token_usage.total_tokens += usage.get('total_tokens', 0)


class BaseCrew:
    """Base class for loading CrewAI configurations from YAML files with multi-tenant support"""
    
    def __init__(self, config_dir: str = None, storage_adapter: Optional[StorageAdapter] = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "../config")
        
        self.config_dir = config_dir
        self.agents_config = self._load_yaml("agents.yaml")
        self.tasks_config = self._load_yaml("tasks.yaml")
        self.crews_config = self._load_yaml("crews.yaml")
        self.cost_tracking_enabled = True
        self.session_costs = []
        
        # Multi-tenant support
        self._context: Optional[RequestContext] = None
        self.storage_adapter = storage_adapter
        
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load a YAML configuration file"""
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return {}
    
    def create_agent(self, agent_name: str, llm=None) -> Agent:
        """Create an agent from YAML configuration"""
        if agent_name not in self.agents_config:
            raise ValueError(f"Agent '{agent_name}' not found in agents.yaml")
        
        config = self.agents_config[agent_name]
        
        return Agent(
            role=config.get("role"),
            goal=config.get("goal"),
            backstory=config.get("backstory"),
            verbose=config.get("verbose", True),
            allow_delegation=config.get("allow_delegation", False),
            max_iter=config.get("max_iter", 3),
            max_execution_time=config.get("max_execution_time", 300),
            llm=llm
        )
    
    def create_task(self, task_name: str, agent: Agent, **kwargs) -> Task:
        """Create a task from YAML configuration"""
        if task_name not in self.tasks_config:
            raise ValueError(f"Task '{task_name}' not found in tasks.yaml")
        
        config = self.tasks_config[task_name]
        
        # Format description with provided kwargs
        description = config.get("description", "").format(**kwargs)
        
        return Task(
            description=description,
            expected_output=config.get("expected_output"),
            agent=agent
        )
    
    def create_crew(self, crew_name: str, agents: List[Agent], tasks: List[Task]) -> Crew:
        """Create a crew from YAML configuration"""
        if crew_name not in self.crews_config:
            raise ValueError(f"Crew '{crew_name}' not found in crews.yaml")
        
        config = self.crews_config[crew_name]
        
        return Crew(
            agents=agents,
            tasks=tasks,
            process=config.get("process", "sequential"),
            verbose=config.get("verbose", True),
            memory=config.get("memory", False),
            cache=config.get("cache", True),
            max_rpm=config.get("max_rpm", 10),
            share_crew=config.get("share_crew", False)
        )
    
    def track_crew_costs(self, crew_result: Any, agent_name: str, model: str = "gpt-4", 
                        task_description: Optional[str] = None) -> Dict[str, Any]:
        """Track costs for a crew execution"""
        if not self.cost_tracking_enabled:
            return {}
        
        # Extract token usage from crew result if available
        # This is a simplified version - actual implementation would need to 
        # aggregate token usage from all agents in the crew
        token_usage = TokenUsage(
            prompt_tokens=1000,  # Placeholder - actual values would come from crew
            completion_tokens=500,
            total_tokens=1500
        )
        
        cost_estimate = cost_tracker.track_usage(
            agent_name=agent_name,
            model=model,
            token_usage=token_usage,
            task_description=task_description or "Crew execution"
        )
        
        self.session_costs.append(cost_estimate)
        
        return {
            "cost_estimate": cost_estimate.dict(),
            "session_total": self.get_session_cost_summary()
        }
    
    def get_session_cost_summary(self) -> Dict[str, Any]:
        """Get cost summary for current session"""
        if not self.session_costs:
            return {"total_cost": 0.0, "total_tokens": 0, "requests": 0}
        
        total_cost = sum(cost.estimated_cost for cost in self.session_costs)
        total_tokens = sum(cost.token_usage.total_tokens for cost in self.session_costs)
        
        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "requests": len(self.session_costs),
            "currency": "USD"
        }
    
    def enable_cost_tracking(self, enabled: bool = True):
        """Enable or disable cost tracking"""
        self.cost_tracking_enabled = enabled
        logger.info(f"Cost tracking {'enabled' if enabled else 'disabled'} for {self.__class__.__name__}")
    
    # Multi-tenant support methods
    def set_context(self, context: RequestContext):
        """Set organization/project context for the agent"""
        self._context = context
        logger.info(f"Context set for {self.__class__.__name__}: org={context.organization_id}, project={context.project_id}")
    
    def get_context(self) -> Optional[RequestContext]:
        """Get current context"""
        return self._context
    
    def get_scoped_storage(self) -> Optional['ScopedStorageAdapter']:
        """Get storage adapter with automatic scoping"""
        if not self.storage_adapter or not self._context:
            return None
        
        from app.core.storage.scoped_adapter import ScopedStorageAdapter
        return ScopedStorageAdapter(self.storage_adapter, self._context)
    
    async def save_result(self, collection: str, data: dict, id: Optional[str] = None) -> str:
        """Save data with automatic context injection"""
        storage = self.get_scoped_storage()
        if not storage:
            raise ValueError("No storage adapter or context available")
        
        # Add context information
        scoped_data = {
            **data,
            'organization_id': str(self._context.organization_id),
            'project_id': str(self._context.project_id) if self._context.project_id else None,
            'created_by': str(self._context.user_id)
        }
        
        return await storage.save(collection, scoped_data, id)
    
    async def list_results(self, collection: str, filters: Optional[Dict] = None, **kwargs) -> List[Dict[str, Any]]:
        """List data with automatic context filtering"""
        storage = self.get_scoped_storage()
        if not storage:
            raise ValueError("No storage adapter or context available")
        
        return await storage.list(collection, filters, **kwargs)
    
    async def get_result(self, collection: str, id: str) -> Optional[Dict[str, Any]]:
        """Get a specific result with context validation"""
        storage = self.get_scoped_storage()
        if not storage:
            raise ValueError("No storage adapter or context available")
        
        return await storage.load(collection, id)
    
    def validate_context(self) -> bool:
        """Validate that context is properly set"""
        if not self._context:
            logger.warning(f"No context set for {self.__class__.__name__}")
            return False
        
        if not self._context.organization_id:
            logger.warning(f"No organization_id in context for {self.__class__.__name__}")
            return False
        
        return True
    
    async def consume_credits_for_action(
        self, 
        action: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Consume credits for a specific action
        
        Args:
            action: The action being performed (e.g., 'generate_content')
            metadata: Additional metadata to track with the usage
            
        Returns:
            bool: True if credits were consumed successfully
            
        Raises:
            InsufficientCreditsError: If there are not enough credits
        """
        if not self.validate_context():
            logger.warning("No valid context for credit consumption")
            return True  # Allow operation to continue without context
        
        try:
            credit_service = CreditService()
            agent_type = self.__class__.__name__
            
            # Get the cost for this action
            cost = await credit_service.get_cost_for_action(agent_type, action)
            
            # Consume credits
            success = await credit_service.consume_credits(
                organization_id=str(self._context.organization_id),
                amount=cost,
                project_id=str(self._context.project_id) if self._context.project_id else None,
                department_id=str(self._context.department_id) if hasattr(self._context, 'department_id') and self._context.department_id else None,
                agent_type=agent_type,
                action=action,
                metadata=metadata,
                user_id=str(self._context.user_id) if self._context.user_id else None
            )
            
            if not success:
                raise InsufficientCreditsError(
                    f"Insufficient credits for {agent_type}.{action}"
                )
            
            logger.info(
                f"Consumed {cost} credits for {agent_type}.{action} "
                f"(org: {self._context.organization_id}, project: {self._context.project_id})"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to consume credits: {str(e)}")
            # Decide whether to fail the operation or continue
            # For now, we'll raise to prevent operation without credits
            raise
    
    async def check_credits_available(self, action: str) -> bool:
        """
        Check if there are enough credits for an action without consuming them
        
        Args:
            action: The action to check credits for
            
        Returns:
            bool: True if there are enough credits available
        """
        if not self.validate_context():
            return True  # Allow if no context
        
        try:
            credit_service = CreditService()
            agent_type = self.__class__.__name__
            
            # Get the cost for this action
            cost = await credit_service.get_cost_for_action(agent_type, action)
            
            # Get current balance
            balance = await credit_service.get_balance(str(self._context.organization_id))
            
            return balance['available'] >= cost
            
        except Exception as e:
            logger.error(f"Failed to check credits: {str(e)}")
            return True  # Allow on error