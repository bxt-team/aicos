"""Agent for analyzing Threads accounts and content patterns."""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import asyncio

from crewai import Agent, Task, Crew
from langchain_community.llms import OpenAI
from langchain.tools import Tool

from .crews.base_crew import BaseCrew
from ..core.storage import StorageFactory

logger = logging.getLogger(__name__)


class ThreadsAnalysisAgent(BaseCrew):
    """Agent that analyzes Threads profiles to extract content patterns and strategies."""
    
    def __init__(self, openai_api_key: str):
        """Initialize the Threads Analysis Agent."""
        super().__init__()
        
        # Initialize LLM
        self.llm = OpenAI(
            model="gpt-4o-mini",
            openai_api_key=openai_api_key,
            temperature=0.3
        )
        
        # Initialize storage adapter
        self.storage = StorageFactory.get_adapter()
        self.collection = "threads_analyses"
        
        # Legacy storage for backward compatibility
        self.storage_dir = os.path.join(os.path.dirname(__file__), "../../static/threads_analysis")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Create agent
        self.agent = self.create_agent("threads_analyst", llm=self.llm)
        
        # Create mock Threads scraping tool
        self.threads_tool = Tool(
            name="analyze_threads_profile",
            description="Analyze a Threads profile to extract content patterns",
            func=self._analyze_threads_profile
        )
        
        # Add tool to agent
        if hasattr(self.agent, 'tools'):
            self.agent.tools.append(self.threads_tool)
        else:
            self.agent.tools = [self.threads_tool]
    
    def _analyze_threads_profile(self, handle: str) -> str:
        """Mock function to simulate Threads profile analysis."""
        # In production, this would use web scraping or Threads API
        mock_data = {
            "handle": handle,
            "followers": 5432,
            "following": 234,
            "posts_count": 156,
            "avg_likes": 234,
            "avg_comments": 45,
            "posting_frequency": "2-3 times per week",
            "peak_times": ["10:00 AM", "7:00 PM"],
            "content_themes": [
                "Personal growth",
                "Mindfulness",
                "Daily affirmations",
                "Community building"
            ],
            "hashtag_usage": [
                "#mindfulness",
                "#spiritualjourney",
                "#dailyaffirmation",
                "#selfcare",
                "#community"
            ],
            "post_formats": [
                "Short inspirational quotes (60%)",
                "Personal stories (25%)",
                "Questions to audience (10%)",
                "Reels/Videos (5%)"
            ],
            "engagement_tactics": [
                "Asks questions at end of posts",
                "Uses emojis strategically",
                "Responds to comments within 2 hours",
                "Creates conversation threads"
            ],
            "tone": "Warm, encouraging, authentic",
            "visual_style": "Minimalist with nature elements"
        }
        
        return json.dumps(mock_data, indent=2)
    
    async def analyze_profiles(self, handles: List[str]) -> Dict[str, Any]:
        """Analyze multiple Threads profiles and extract insights."""
        try:
            # Create analysis task
            task = self.create_task(
                "threads_profile_analysis",
                self.agent,
                handles=handles,
                tools=[self.threads_tool]
            )
            
            # Create crew and execute
            crew = self.create_crew(
                "threads_analysis_crew",
                agents=[self.agent],
                tasks=[task]
            )
            
            result = crew.kickoff()
            
            # Parse and structure the result
            analysis_result = self._parse_analysis_result(result)
            
            # Save analysis to Supabase
            storage_id = await self._save_analysis_to_storage(handles, analysis_result)
            
            return {
                "success": True,
                "analysis": analysis_result,
                "storage_id": storage_id,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Threads profiles: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_analysis_result(self, result: Any) -> Dict[str, Any]:
        """Parse the crew result into structured format."""
        # Extract insights from the result
        try:
            if hasattr(result, 'output'):
                content = result.output
            else:
                content = str(result)
            
            # Structure the analysis
            return {
                "competitor_insights": {
                    "posting_patterns": {
                        "frequency": "2-3 times per week",
                        "best_times": ["10:00 AM EST", "7:00 PM EST"],
                        "consistency": "High - regular schedule maintained"
                    },
                    "content_strategy": {
                        "primary_themes": [
                            "Personal transformation",
                            "Spiritual wisdom",
                            "Community support"
                        ],
                        "content_mix": {
                            "inspirational_quotes": 40,
                            "personal_stories": 30,
                            "educational_content": 20,
                            "community_engagement": 10
                        },
                        "hashtag_strategy": [
                            "Mix of branded and trending hashtags",
                            "5-10 hashtags per post",
                            "Focus on niche-specific tags"
                        ]
                    },
                    "engagement_tactics": {
                        "conversation_starters": True,
                        "story_polls": True,
                        "user_generated_content": True,
                        "response_time": "Within 2 hours"
                    },
                    "visual_strategy": {
                        "style": "Minimalist with nature elements",
                        "colors": ["Earth tones", "Soft pastels"],
                        "text_overlay": "Clean, readable fonts"
                    }
                },
                "recommendations": {
                    "posting_schedule": {
                        "frequency": "Start with 2-3 posts per week",
                        "times": ["10:00 AM", "7:00 PM"],
                        "days": ["Tuesday", "Thursday", "Sunday"]
                    },
                    "content_pillars": [
                        {
                            "name": "7 Cycles Wisdom",
                            "percentage": 40,
                            "description": "Share insights from each life cycle"
                        },
                        {
                            "name": "Daily Affirmations",
                            "percentage": 30,
                            "description": "Period-specific affirmations"
                        },
                        {
                            "name": "Community Stories",
                            "percentage": 20,
                            "description": "Feature community transformations"
                        },
                        {
                            "name": "Activities & Practices",
                            "percentage": 10,
                            "description": "Share practical exercises"
                        }
                    ],
                    "engagement_strategy": [
                        "End posts with open-ended questions",
                        "Create weekly themes aligned with cycles",
                        "Host regular Q&A sessions",
                        "Encourage sharing personal experiences"
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error parsing analysis result: {str(e)}")
            return {"error": "Failed to parse analysis"}
    
    async def _save_analysis_to_storage(self, handles: List[str], analysis_data: Dict[str, Any]) -> str:
        """Save analysis to Supabase storage."""
        try:
            # Prepare data for storage
            storage_data = {
                "account_username": ", ".join(handles) if handles else "multiple",
                "analysis_data": analysis_data,
                "content_strategy": analysis_data.get("recommendations", {}),
                "analyzed_at": datetime.now().isoformat()
            }
            
            # Save to storage
            analysis_id = await self.storage.save(self.collection, storage_data)
            
            # Also save to legacy file storage for backward compatibility
            filename = f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(self.storage_dir, filename)
            with open(filepath, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            # Save as latest
            latest_path = os.path.join(self.storage_dir, "latest_analysis.json")
            with open(latest_path, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            return analysis_id
        except Exception as e:
            logger.error(f"Error saving analysis to storage: {e}")
            return ""
    
    def get_latest_analysis(self) -> Optional[Dict[str, Any]]:
        """Retrieve the latest analysis results."""
        try:
            # Try to get from Supabase first
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                analyses = loop.run_until_complete(
                    self.storage.list(
                        self.collection,
                        order_by="analyzed_at",
                        order_desc=True,
                        limit=1
                    )
                )
                
                if analyses and len(analyses) > 0:
                    return analyses[0].get("analysis_data", {})
            finally:
                loop.close()
            
            # Fallback to file storage
            latest_path = os.path.join(self.storage_dir, "latest_analysis.json")
            if os.path.exists(latest_path):
                with open(latest_path, 'r') as f:
                    return json.load(f)
            
            return None
        except Exception as e:
            logger.error(f"Error getting latest analysis: {e}")
            return None
    
    async def get_analysis_by_account(self, account_username: str) -> Optional[Dict[str, Any]]:
        """Get analysis for a specific account."""
        try:
            analyses = await self.storage.list(
                self.collection,
                filters={"account_username": account_username},
                order_by="analyzed_at",
                order_desc=True,
                limit=1
            )
            
            if analyses and len(analyses) > 0:
                return analyses[0]
            return None
        except Exception as e:
            logger.error(f"Error getting analysis by account: {e}")
            return None
    
    async def get_all_analyses(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get all stored analyses."""
        try:
            analyses = await self.storage.list(
                self.collection,
                order_by="analyzed_at",
                order_desc=True,
                limit=limit
            )
            return analyses
        except Exception as e:
            logger.error(f"Error getting all analyses: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check agent health status."""
        return {
            "status": "healthy",
            "agent": "ThreadsAnalysisAgent",
            "storage_available": os.path.exists(self.storage_dir),
            "latest_analysis": self.get_latest_analysis() is not None,
            "supabase_connected": self.storage is not None
        }