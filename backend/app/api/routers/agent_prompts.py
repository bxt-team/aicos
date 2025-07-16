"""
Router for agent prompts and configurations
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import yaml
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["agent-prompts"]
)

@router.get("/agent-prompts")
async def get_agent_prompts() -> Dict[str, Any]:
    """
    Get all agent prompts and configurations from the YAML file
    """
    try:
        # Path to the agents YAML configuration
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "agents", "config", "agents.yaml"
        )
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Agent configuration file not found: {config_path}")
        
        # Load the YAML configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            agents_config = yaml.safe_load(f)
        
        # Format the response
        agents_data = {}
        for agent_key, agent_config in agents_config.items():
            agents_data[agent_key] = {
                "name": agent_config.get("role", "Unknown Agent"),
                "role": agent_config.get("role", ""),
                "goal": agent_config.get("goal", ""),
                "backstory": agent_config.get("backstory", ""),
                "settings": {
                    "verbose": agent_config.get("verbose", True),
                    "allow_delegation": agent_config.get("allow_delegation", False),
                    "max_iter": agent_config.get("max_iter", 3),
                    "max_execution_time": agent_config.get("max_execution_time", 300)
                }
            }
        
        return {
            "success": True,
            "agents": agents_data,
            "total_agents": len(agents_data)
        }
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        raise HTTPException(status_code=500, detail="Error parsing agent configuration")
    except Exception as e:
        logger.error(f"Error retrieving agent prompts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/agent-prompts/{agent_id}")
async def get_agent_prompt(agent_id: str) -> Dict[str, Any]:
    """
    Get a specific agent's prompt and configuration
    """
    try:
        # Path to the agents YAML configuration
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "agents", "config", "agents.yaml"
        )
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Agent configuration file not found: {config_path}")
        
        # Load the YAML configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            agents_config = yaml.safe_load(f)
        
        # Find the specific agent
        if agent_id not in agents_config:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
        
        agent_config = agents_config[agent_id]
        
        return {
            "success": True,
            "agent_id": agent_id,
            "agent": {
                "name": agent_config.get("role", "Unknown Agent"),
                "role": agent_config.get("role", ""),
                "goal": agent_config.get("goal", ""),
                "backstory": agent_config.get("backstory", ""),
                "settings": {
                    "verbose": agent_config.get("verbose", True),
                    "allow_delegation": agent_config.get("allow_delegation", False),
                    "max_iter": agent_config.get("max_iter", 3),
                    "max_execution_time": agent_config.get("max_execution_time", 300)
                }
            }
        }
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        raise HTTPException(status_code=500, detail="Error parsing agent configuration")
    except Exception as e:
        logger.error(f"Error retrieving agent prompt: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")