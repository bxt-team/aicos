import logging
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from functools import wraps

logger = logging.getLogger(__name__)


class TokenUsage(BaseModel):
    """Model for tracking token usage"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def add(self, other: 'TokenUsage'):
        """Add another TokenUsage to this one"""
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens


class CostEstimate(BaseModel):
    """Model for cost estimation"""
    model: str
    token_usage: TokenUsage
    estimated_cost: float
    currency: str = "USD"
    timestamp: str
    agent_name: str
    task_description: Optional[str] = None
    

class CostTracker:
    """Track costs for AI agent operations"""
    
    # Cost per 1M tokens for different models (as of 2024)
    MODEL_COSTS = {
        # OpenAI models (per 1M tokens)
        "gpt-4": {
            "input": 30.00,  # $30 per 1M input tokens
            "output": 60.00  # $60 per 1M output tokens
        },
        "gpt-4-turbo": {
            "input": 10.00,
            "output": 30.00
        },
        "gpt-3.5-turbo": {
            "input": 0.50,
            "output": 1.50
        },
        "gpt-3.5-turbo-16k": {
            "input": 3.00,
            "output": 4.00
        },
        "text-embedding-ada-002": {
            "input": 0.10,
            "output": 0.00  # Embeddings don't have output tokens
        },
        # Add more models as needed
    }
    
    def __init__(self, storage_dir: str = "storage/cost_tracking"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.session_costs: List[CostEstimate] = []
        
    def calculate_cost(self, model: str, token_usage: TokenUsage) -> float:
        """Calculate cost based on model and token usage"""
        if model not in self.MODEL_COSTS:
            logger.warning(f"Unknown model: {model}. Using default GPT-4 pricing.")
            model = "gpt-4"
            
        costs = self.MODEL_COSTS[model]
        input_cost = (token_usage.prompt_tokens / 1_000_000) * costs["input"]
        output_cost = (token_usage.completion_tokens / 1_000_000) * costs["output"]
        
        return round(input_cost + output_cost, 4)
    
    def track_usage(self, 
                   agent_name: str,
                   model: str,
                   token_usage: TokenUsage,
                   task_description: Optional[str] = None) -> CostEstimate:
        """Track token usage and calculate cost"""
        
        estimated_cost = self.calculate_cost(model, token_usage)
        
        cost_estimate = CostEstimate(
            model=model,
            token_usage=token_usage,
            estimated_cost=estimated_cost,
            timestamp=datetime.now().isoformat(),
            agent_name=agent_name,
            task_description=task_description
        )
        
        # Add to session costs
        self.session_costs.append(cost_estimate)
        
        # Log the cost
        logger.info(f"Cost tracking - Agent: {agent_name}, Model: {model}, "
                   f"Tokens: {token_usage.total_tokens}, Cost: ${estimated_cost:.4f}")
        
        # Save to file
        self._save_cost_record(cost_estimate)
        
        return cost_estimate
    
    def _save_cost_record(self, cost_estimate: CostEstimate):
        """Save cost record to file"""
        try:
            # Create daily file
            date_str = datetime.now().strftime("%Y-%m-%d")
            filename = os.path.join(self.storage_dir, f"costs_{date_str}.jsonl")
            
            with open(filename, "a") as f:
                f.write(cost_estimate.json() + "\n")
                
        except Exception as e:
            logger.error(f"Failed to save cost record: {e}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of costs for current session"""
        if not self.session_costs:
            return {
                "total_cost": 0.0,
                "total_tokens": 0,
                "requests": 0,
                "by_agent": {},
                "by_model": {}
            }
        
        total_cost = sum(cost.estimated_cost for cost in self.session_costs)
        total_tokens = sum(cost.token_usage.total_tokens for cost in self.session_costs)
        
        # Group by agent
        by_agent = {}
        for cost in self.session_costs:
            if cost.agent_name not in by_agent:
                by_agent[cost.agent_name] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "requests": 0
                }
            by_agent[cost.agent_name]["cost"] += cost.estimated_cost
            by_agent[cost.agent_name]["tokens"] += cost.token_usage.total_tokens
            by_agent[cost.agent_name]["requests"] += 1
        
        # Group by model
        by_model = {}
        for cost in self.session_costs:
            if cost.model not in by_model:
                by_model[cost.model] = {
                    "cost": 0.0,
                    "tokens": 0,
                    "requests": 0
                }
            by_model[cost.model]["cost"] += cost.estimated_cost
            by_model[cost.model]["tokens"] += cost.token_usage.total_tokens
            by_model[cost.model]["requests"] += 1
        
        return {
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "requests": len(self.session_costs),
            "by_agent": by_agent,
            "by_model": by_model,
            "currency": "USD"
        }
    
    def get_daily_costs(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get costs for a specific day"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        filename = os.path.join(self.storage_dir, f"costs_{date}.jsonl")
        if not os.path.exists(filename):
            return {
                "date": date,
                "total_cost": 0.0,
                "total_tokens": 0,
                "requests": 0,
                "details": []
            }
        
        costs = []
        total_cost = 0.0
        total_tokens = 0
        
        try:
            with open(filename, "r") as f:
                for line in f:
                    if line.strip():
                        cost_data = json.loads(line)
                        costs.append(cost_data)
                        total_cost += cost_data["estimated_cost"]
                        total_tokens += cost_data["token_usage"]["total_tokens"]
        except Exception as e:
            logger.error(f"Failed to read cost file: {e}")
        
        return {
            "date": date,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "requests": len(costs),
            "details": costs,
            "currency": "USD"
        }
    
    def get_monthly_summary(self, year: int, month: int) -> Dict[str, Any]:
        """Get monthly cost summary"""
        import calendar
        
        days_in_month = calendar.monthrange(year, month)[1]
        monthly_costs = []
        total_cost = 0.0
        total_tokens = 0
        total_requests = 0
        
        for day in range(1, days_in_month + 1):
            date_str = f"{year:04d}-{month:02d}-{day:02d}"
            daily = self.get_daily_costs(date_str)
            if daily["requests"] > 0:
                monthly_costs.append(daily)
                total_cost += daily["total_cost"]
                total_tokens += daily["total_tokens"]
                total_requests += daily["requests"]
        
        return {
            "year": year,
            "month": month,
            "total_cost": round(total_cost, 4),
            "total_tokens": total_tokens,
            "total_requests": total_requests,
            "daily_costs": monthly_costs,
            "currency": "USD"
        }


# Global cost tracker instance
cost_tracker = CostTracker()


def track_cost(agent_name: str):
    """Decorator to track costs for agent operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This is a placeholder - in real implementation,
            # you'd need to intercept the LLM calls to get token usage
            # For now, we'll add hooks in the agent methods
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator