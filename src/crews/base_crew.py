from crewai import Agent, Task, Crew
from crewai.agent import Agent
from langchain_openai import ChatOpenAI
import yaml
import os
from typing import Dict, Any, List

class BaseCrew:
    """Base class for loading CrewAI configurations from YAML files"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "../config")
        
        self.config_dir = config_dir
        self.agents_config = self._load_yaml("agents.yaml")
        self.tasks_config = self._load_yaml("tasks.yaml")
        self.crews_config = self._load_yaml("crews.yaml")
        
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