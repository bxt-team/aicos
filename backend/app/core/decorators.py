"""Decorators for the application"""
import functools
import logging
from typing import Optional, Dict, Any
from app.services.credit_service import CreditService
from app.core.exceptions import InsufficientCreditsError

logger = logging.getLogger(__name__)

def consume_credits(
    agent_type: str, 
    action: str,
    metadata_extractor: Optional[callable] = None
):
    """
    Decorator to track credit consumption for agent actions
    
    Args:
        agent_type: Type of agent (e.g., 'ContentAgent')
        action: Action being performed (e.g., 'generate_content')
        metadata_extractor: Optional function to extract metadata from args/kwargs
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract organization_id and other context
            # This assumes the first argument is self and has access to context
            self = args[0] if args else None
            
            # Try to get context from various sources
            organization_id = None
            project_id = None
            department_id = None
            user_id = None
            
            # Check if context is passed in kwargs
            if 'context' in kwargs:
                context = kwargs['context']
                organization_id = context.get('organization_id')
                project_id = context.get('project_id')
                department_id = context.get('department_id')
                user_id = context.get('user_id')
            
            # Check if self has context attribute
            elif hasattr(self, 'context'):
                organization_id = getattr(self.context, 'organization_id', None)
                project_id = getattr(self.context, 'project_id', None)
                department_id = getattr(self.context, 'department_id', None)
                user_id = getattr(self.context, 'user_id', None)
            
            # Extract metadata if extractor provided
            metadata = {}
            if metadata_extractor:
                try:
                    metadata = metadata_extractor(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Failed to extract metadata: {str(e)}")
            
            # Only consume credits if we have an organization_id
            if organization_id:
                try:
                    credit_service = CreditService()
                    
                    # Get the cost for this action
                    cost = await credit_service.get_cost_for_action(agent_type, action)
                    
                    # Consume credits
                    success = await credit_service.consume_credits(
                        organization_id=organization_id,
                        amount=cost,
                        project_id=project_id,
                        department_id=department_id,
                        agent_type=agent_type,
                        action=action,
                        metadata=metadata,
                        user_id=user_id
                    )
                    
                    if not success:
                        raise InsufficientCreditsError(
                            f"Insufficient credits for {agent_type}.{action}"
                        )
                    
                    logger.info(
                        f"Consumed {cost} credits for {agent_type}.{action} "
                        f"(org: {organization_id}, project: {project_id})"
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to consume credits: {str(e)}")
                    # Decide whether to fail the operation or continue
                    # For now, we'll log but continue
                    # raise
            else:
                logger.debug(
                    f"No organization_id found for credit consumption "
                    f"({agent_type}.{action})"
                )
            
            # Execute the actual function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

def track_agent_usage(agent_type: str):
    """
    Class decorator to automatically add credit consumption to all agent methods
    
    Usage:
        @track_agent_usage("ContentAgent")
        class ContentAgent(BaseCrew):
            ...
    """
    def class_decorator(cls):
        # List of methods to track
        tracked_methods = [
            'generate_content',
            'create_visual_post', 
            'generate_voice',
            'generate_video',
            'research_topic',
            'answer_question',
            'execute_workflow'
        ]
        
        # Apply consume_credits decorator to tracked methods
        for method_name in tracked_methods:
            if hasattr(cls, method_name):
                method = getattr(cls, method_name)
                if callable(method) and not method_name.startswith('_'):
                    # Apply the decorator
                    decorated_method = consume_credits(
                        agent_type=agent_type,
                        action=method_name
                    )(method)
                    setattr(cls, method_name, decorated_method)
        
        return cls
    
    return class_decorator

def require_credits(min_credits: float = 0):
    """
    Decorator to check if user has minimum credits before executing
    
    Args:
        min_credits: Minimum credits required (0 means just check positive balance)
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract organization_id similar to consume_credits
            self = args[0] if args else None
            organization_id = None
            
            if 'context' in kwargs:
                organization_id = kwargs['context'].get('organization_id')
            elif hasattr(self, 'context'):
                organization_id = getattr(self.context, 'organization_id', None)
            
            if organization_id:
                try:
                    credit_service = CreditService()
                    balance = await credit_service.get_balance(organization_id)
                    
                    if balance['available'] < min_credits:
                        raise InsufficientCreditsError(
                            f"Insufficient credits. Required: {min_credits}, "
                            f"Available: {balance['available']}"
                        )
                except Exception as e:
                    logger.error(f"Failed to check credits: {str(e)}")
                    # Decide whether to fail or continue
                    # raise
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator