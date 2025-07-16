from crewai import Agent
from crewai_tools import DirectoryReadTool, FileReadTool
from textwrap import dedent
from app.core.storage import StorageFactory
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
import hashlib

class ResearcherAgent:
    def __init__(self):
        self.directory_tool = DirectoryReadTool(directory='knowledge/')
        self.file_read_tool = FileReadTool()
        
        # Initialize storage adapter
        self.storage = StorageFactory.get_adapter()
        self.collection = "generic_storage"  # Use generic storage for research results
    
    def create_agent(self):
        return Agent(
            role="Content Researcher",
            goal="Extract and analyze relevant information from knowledge files to identify affirmation themes for the 7 periods of the 7 Cycles app",
            backstory=dedent("""
                You are an expert researcher specializing in the 7 Cycles system. You have 
                deep knowledge of the 7 periods: Image (#DAA520), Change (#2196F3), Energy (#F44336), 
                Creativity (#FFD700), Success (#CC0066), Relaxation (#4CAF50), and Prudence (#9C27B0). 
                You analyze knowledge files to extract key themes and concepts for each period 
                to create personalized affirmations that align with each period's unique energy.
            """),
            tools=[self.directory_tool, self.file_read_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def get_tasks(self):
        return [
            {
                "description": dedent("""
                    Analyze the knowledge files in the knowledge directory to extract key themes and concepts for each of the 7 periods 
                    of the 7 Cycles system. Use the DirectoryReadTool to explore the directory and FileReadTool to read individual files.
                    
                    Focus on:
                    1. Use DirectoryReadTool to list all files in the knowledge directory
                    2. Read the introduction files (01_introduction_en.txt through 06_lifecyle_en.txt) for context
                    3. Extract core themes from each period's knowledge file (07_image_en.txt through 13_prudence_en.txt)
                    4. Identify the unique characteristics and energy of each period
                    5. Find key concepts that would make powerful affirmations for each period
                    6. Understand the emotional and spiritual aspects of each period
                    7. Analyze the holistic development approach of the 7 Cycles system
                    
                    Your research should result in a comprehensive analysis that includes:
                    - Core themes for each of the 7 periods
                    - Unique characteristics of each period's energy
                    - Key concepts suitable for affirmation generation
                    - Emotional and spiritual development aspects
                    - Color associations for each period
                """),
                "expected_output": dedent("""
                    A detailed research report containing:
                    - Core themes and concepts for each of the 7 periods:
                      * Image (#DAA520): Recognition, professional development, self-presentation
                      * Change (#2196F3): Transformation, flexibility, growth
                      * Energy (#F44336): Dynamic power, strength, achievement
                      * Creativity (#FFD700): Innovation, artistic expression, openness
                      * Success (#CC0066): Holistic achievement, fulfillment, authentic living
                      * Relaxation (#4CAF50): Well-being, balance, harmony
                      * Prudence (#9C27B0): Conscious action, reflection, strategic planning
                    - Key affirmation themes for each period
                    - Emotional and spiritual development aspects
                    - Unique characteristics of each period's energy
                    - Color symbolism and associations for each period
                """),
                "agent": "researcher"
            }
        ]
    
    def _generate_research_key(self, research_type: str, params: Dict[str, Any]) -> str:
        """Generate a unique key for research results"""
        key_data = f"{research_type}_{json.dumps(params, sort_keys=True)}"
        return f"research_{hashlib.md5(key_data.encode()).hexdigest()}"
    
    async def save_research_results(self, research_type: str, results: Dict[str, Any], params: Optional[Dict[str, Any]] = None) -> str:
        """Save research results to Supabase for caching and reuse"""
        try:
            storage_key = self._generate_research_key(research_type, params or {})
            
            data = {
                "storage_key": storage_key,
                "storage_type": "research_results",
                "data": {
                    "research_type": research_type,
                    "results": results,
                    "params": params or {},
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # Save to storage
            result_id = await self.storage.save(self.collection, data)
            return result_id
        except Exception as e:
            print(f"Error saving research results: {e}")
            return ""
    
    async def get_cached_research(self, research_type: str, params: Optional[Dict[str, Any]] = None, max_age_hours: int = 24) -> Optional[Dict[str, Any]]:
        """Retrieve cached research results if available and not too old"""
        try:
            storage_key = self._generate_research_key(research_type, params or {})
            
            # Query by storage_key
            results = await self.storage.list(
                self.collection,
                filters={"storage_key": storage_key, "storage_type": "research_results"},
                limit=1
            )
            
            if results and len(results) > 0:
                result = results[0]
                data = result.get("data", {})
                
                # Check age
                timestamp_str = data.get("timestamp")
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
                    
                    if age_hours <= max_age_hours:
                        return data.get("results")
            
            return None
        except Exception as e:
            print(f"Error retrieving cached research: {e}")
            return None
    
    def analyze_periods(self, crew_result: Any) -> Dict[str, Any]:
        """Analyze crew results and save to storage"""
        try:
            # Parse the research results
            results = {
                "periods": {
                    "Image": {
                        "themes": ["Recognition", "Professional development", "Self-presentation"],
                        "color": "#DAA520",
                        "energy": "Self-awareness and authentic expression"
                    },
                    "Change": {
                        "themes": ["Transformation", "Flexibility", "Growth"],
                        "color": "#2196F3",
                        "energy": "Adaptive transformation and renewal"
                    },
                    "Energy": {
                        "themes": ["Dynamic power", "Strength", "Achievement"],
                        "color": "#F44336",
                        "energy": "Vital force and motivation"
                    },
                    "Creativity": {
                        "themes": ["Innovation", "Artistic expression", "Openness"],
                        "color": "#FFD700",
                        "energy": "Creative flow and inspiration"
                    },
                    "Success": {
                        "themes": ["Holistic achievement", "Fulfillment", "Authentic living"],
                        "color": "#CC0066",
                        "energy": "Manifestation and accomplishment"
                    },
                    "Relaxation": {
                        "themes": ["Well-being", "Balance", "Harmony"],
                        "color": "#4CAF50",
                        "energy": "Inner peace and restoration"
                    },
                    "Prudence": {
                        "themes": ["Conscious action", "Reflection", "Strategic planning"],
                        "color": "#9C27B0",
                        "energy": "Wisdom and thoughtful decision-making"
                    }
                },
                "analysis_timestamp": datetime.now().isoformat(),
                "crew_result": str(crew_result) if crew_result else None
            }
            
            # Save results asynchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result_id = loop.run_until_complete(
                    self.save_research_results("7cycles_periods_analysis", results)
                )
            finally:
                loop.close()
            
            return results
        except Exception as e:
            print(f"Error analyzing periods: {e}")
            return {}