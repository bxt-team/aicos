from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import yaml
import os
from pathlib import Path

from ...core.supabase_auth import get_current_user

router = APIRouter(prefix="/api/ai-agents", tags=["ai-agents"])


class AgentParameter(BaseModel):
    name: str
    value: Any
    type: str  # string, number, boolean, list, dict


class AgentConfig(BaseModel):
    id: str
    name: str
    role: str
    goal: str
    backstory: str
    verbose: bool = True
    allow_delegation: bool = False
    max_iter: int = 3
    max_execution_time: int = 300
    parameters: List[AgentParameter]
    category: str = "general"  # Category for grouping agents


def load_agents_config() -> Dict[str, Any]:
    """Load agents configuration from YAML file."""
    config_path = Path(__file__).parent.parent.parent / "agents" / "config" / "agents.yaml"
    
    if not config_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agents configuration file not found"
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load agents configuration: {str(e)}"
        )


def categorize_agent(agent_id: str, config: Dict[str, Any]) -> str:
    """Categorize agent based on its ID and configuration."""
    categories = {
        'qa': ['qa_agent'],
        'content': ['affirmations_agent', 'content_workflow_agent'],
        'visual': ['image_search_agent', 'visual_post_creator_agent', 'post_composition_agent'],
        'video': ['video_generation_agent', 'background_video_agent', 'voice_over_agent', 'caption_agent'],
        'instagram': ['instagram_ai_prompt_agent', 'instagram_poster_agent', 'instagram_analyzer_agent', 'write_hashtag_research_agent'],
        'threads': ['threads_analyst', 'threads_strategy', 'threads_generator', 'threads_approval', 'threads_scheduler'],
        'x': ['x_analyst', 'x_strategy', 'x_generator', 'x_approval', 'x_scheduler'],
        'testing': ['app_testing_agent']
    }
    
    for category, agent_list in categories.items():
        if agent_id in agent_list:
            return category
    
    return 'general'


def format_agent_name(agent_id: str) -> str:
    """Format agent ID into a human-readable name."""
    # Remove _agent suffix if present
    name = agent_id.replace('_agent', '')
    # Replace underscores with spaces and capitalize words
    name = ' '.join(word.capitalize() for word in name.split('_'))
    return name


@router.get("", response_model=List[AgentConfig])
async def list_agents(
    category: str = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all available AI agents with their configurations."""
    agents_config = load_agents_config()
    
    agents = []
    for agent_id, config in agents_config.items():
        # Create parameter list from all config items
        parameters = []
        
        # Add all configuration parameters
        for key, value in config.items():
            if key not in ['role', 'goal', 'backstory', 'verbose', 'allow_delegation', 'max_iter', 'max_execution_time']:
                param_type = type(value).__name__
                if param_type == 'NoneType':
                    param_type = 'null'
                
                parameters.append(AgentParameter(
                    name=key,
                    value=value,
                    type=param_type
                ))
        
        agent_category = categorize_agent(agent_id, config)
        
        # Filter by category if specified
        if category and agent_category != category:
            continue
        
        agent = AgentConfig(
            id=agent_id,
            name=format_agent_name(agent_id),
            role=config.get('role', ''),
            goal=config.get('goal', ''),
            backstory=config.get('backstory', ''),
            verbose=config.get('verbose', True),
            allow_delegation=config.get('allow_delegation', False),
            max_iter=config.get('max_iter', 3),
            max_execution_time=config.get('max_execution_time', 300),
            parameters=parameters,
            category=agent_category
        )
        agents.append(agent)
    
    # Sort agents by category and name
    agents.sort(key=lambda x: (x.category, x.name))
    
    return agents


@router.get("/categories", response_model=List[str])
async def list_agent_categories(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """List all available agent categories."""
    return [
        'qa',
        'content',
        'visual',
        'video',
        'instagram',
        'threads',
        'x',
        'testing',
        'general'
    ]


@router.get("/{agent_id}", response_model=AgentConfig)
async def get_agent(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get detailed configuration for a specific agent."""
    agents_config = load_agents_config()
    
    if agent_id not in agents_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    config = agents_config[agent_id]
    
    # Create parameter list
    parameters = []
    for key, value in config.items():
        if key not in ['role', 'goal', 'backstory', 'verbose', 'allow_delegation', 'max_iter', 'max_execution_time']:
            param_type = type(value).__name__
            if param_type == 'NoneType':
                param_type = 'null'
            
            parameters.append(AgentParameter(
                name=key,
                value=value,
                type=param_type
            ))
    
    return AgentConfig(
        id=agent_id,
        name=format_agent_name(agent_id),
        role=config.get('role', ''),
        goal=config.get('goal', ''),
        backstory=config.get('backstory', ''),
        verbose=config.get('verbose', True),
        allow_delegation=config.get('allow_delegation', False),
        max_iter=config.get('max_iter', 3),
        max_execution_time=config.get('max_execution_time', 300),
        parameters=parameters,
        category=categorize_agent(agent_id, config)
    )


@router.get("/{agent_id}/raw", response_model=Dict[str, Any])
async def get_agent_raw_config(
    agent_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get raw YAML configuration for a specific agent."""
    agents_config = load_agents_config()
    
    if agent_id not in agents_config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )
    
    return {
        "agent_id": agent_id,
        "configuration": agents_config[agent_id]
    }