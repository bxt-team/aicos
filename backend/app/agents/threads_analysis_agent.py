"""Agent for analyzing Threads accounts and content patterns."""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import asyncio

from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from langchain_community.llms import OpenAI

from .crews.base_crew import BaseCrew
from ..core.storage import StorageFactory
from .tools.threads_scraper import scrape_threads_profile

logger = logging.getLogger(__name__)


class ThreadsProfileAnalyzerTool(BaseTool):
    """Tool for analyzing Threads profiles."""
    name: str = "Threads Profile Analyzer"
    description: str = "Analyze a Threads profile to extract content patterns, engagement metrics, and posting strategies"
    
    def _run(self, handle: str) -> str:
        """Analyze a real Threads profile using web scraping."""
        try:
            # Use the real scraper
            profile_data = scrape_threads_profile(handle)
            
            # Format the data for the agent
            formatted_data = {
                "handle": profile_data.get("handle", handle),
                "followers": profile_data.get("followers", 0),
                "following": profile_data.get("following", 0),
                "posts_count": profile_data.get("posts_count", 0),
                "posts_analyzed": profile_data.get("posts_analyzed", 0),
                "engagement_metrics": profile_data.get("engagement_metrics", {}),
                "content_patterns": profile_data.get("content_patterns", {}),
                "content_themes": profile_data.get("content_themes", []),
                "posting_behavior": profile_data.get("posting_behavior", {}),
                "error": profile_data.get("error", None)
            }
            
            # Add analysis insights
            if not formatted_data.get("error"):
                # Extract key insights
                patterns = formatted_data.get("content_patterns", {})
                
                formatted_data["insights"] = {
                    "uses_hashtags": patterns.get("uses_hashtags", False),
                    "top_hashtags": patterns.get("top_hashtags", []),
                    "hashtag_strategy": "Uses hashtags" if patterns.get("uses_hashtags") else "No hashtags used",
                    "avg_engagement": formatted_data.get("engagement_metrics", {}).get("total_engagement", 0),
                    "content_mix": self._analyze_content_mix(formatted_data),
                    "posting_consistency": formatted_data.get("posting_behavior", {}).get("has_consistent_style", False)
                }
            
            return json.dumps(formatted_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error analyzing Threads profile {handle}: {str(e)}")
            return json.dumps({
                "handle": handle,
                "error": f"Failed to analyze profile: {str(e)}"
            }, indent=2)
    
    def _analyze_content_mix(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the content mix from scraped data."""
        patterns = data.get("content_patterns", {})
        post_types = patterns.get("post_types", {})
        
        total_posts = sum(post_types.values())
        if total_posts == 0:
            return {"error": "No posts to analyze"}
        
        return {
            "text_posts": f"{(post_types.get('text', 0) / total_posts * 100):.0f}%",
            "media_posts": f"{(post_types.get('media', 0) / total_posts * 100):.0f}%",
            "avg_post_length": patterns.get("avg_post_length", 0)
        }


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
        
        # Create tool instance
        self.threads_tool = ThreadsProfileAnalyzerTool()
        
        # Create agent
        self.agent = self.create_agent("threads_analyst", llm=self.llm)
        
        # Add tools to agent
        self.agent.tools = [self.threads_tool]
    
    
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
            
            # Try to parse the actual scraped data from the result
            scraped_data = {}
            try:
                # Look for JSON data in the result
                import re
                logger.info(f"Parsing result content (first 500 chars): {content[:500]}")
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    scraped_data = json.loads(json_match.group())
                    logger.info(f"Successfully parsed scraped data with {len(scraped_data)} keys")
                else:
                    logger.warning("No JSON found in crew result")
            except Exception as e:
                logger.error(f"Error parsing JSON from result: {e}")
                pass
            
            # Build analysis based on real data
            engagement = scraped_data.get("engagement_metrics", {})
            patterns = scraped_data.get("content_patterns", {})
            themes = scraped_data.get("content_themes", [])
            insights = scraped_data.get("insights", {})
            
            # Create recommendations based on actual data
            uses_hashtags = patterns.get("uses_hashtags", False)
            top_hashtags = patterns.get("top_hashtags", [])
            avg_engagement = engagement.get("total_engagement", 0)
            
            # Structure the analysis with real insights
            return {
                "competitor_insights": {
                    "profile_metrics": {
                        "handle": scraped_data.get("handle", ""),
                        "followers": scraped_data.get("followers", 0),
                        "following": scraped_data.get("following", 0),
                        "posts_count": scraped_data.get("posts_count", 0),
                        "posts_analyzed": scraped_data.get("posts_analyzed", 0)
                    },
                    "engagement_analysis": {
                        "avg_likes": engagement.get("avg_likes", 0),
                        "avg_comments": engagement.get("avg_comments", 0),
                        "avg_reposts": engagement.get("avg_reposts", 0),
                        "total_avg_engagement": avg_engagement
                    },
                    "content_strategy": {
                        "primary_themes": themes if themes else ["Content themes not detected"],
                        "uses_hashtags": uses_hashtags,
                        "top_hashtags": top_hashtags if top_hashtags else ["No hashtags found"],
                        "hashtag_count": patterns.get("hashtag_count", 0),
                        "avg_post_length": patterns.get("avg_post_length", 0),
                        "content_mix": insights.get("content_mix", {}),
                        "mentions_others": patterns.get("mentions_others", False)
                    },
                    "posting_patterns": {
                        "posts_analyzed": scraped_data.get("posts_analyzed", 0),
                        "has_consistent_style": scraped_data.get("posting_behavior", {}).get("has_consistent_style", False),
                        "post_types": patterns.get("post_types", {})
                    }
                },
                "recommendations": self._generate_recommendations(scraped_data),
                "raw_data": scraped_data  # Include raw data for transparency
            }
        except Exception as e:
            logger.error(f"Error parsing analysis result: {str(e)}")
            return {"error": "Failed to parse analysis"}
    
    def _generate_recommendations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on analyzed data."""
        patterns = data.get("content_patterns", {})
        themes = data.get("content_themes", [])
        engagement = data.get("engagement_metrics", {})
        
        # Determine posting frequency recommendation
        if data.get("posts_count", 0) > 100:
            frequency = "2-3 times per week"
        else:
            frequency = "Start with 1-2 posts per week and gradually increase"
        
        # Hashtag recommendations
        if patterns.get("uses_hashtags"):
            hashtag_rec = f"Use {patterns.get('hashtag_count', 5)}-{patterns.get('hashtag_count', 5)+5} hashtags per post, focusing on: {', '.join(patterns.get('top_hashtags', [])[:5])}"
        else:
            hashtag_rec = "Consider adding 5-10 relevant hashtags to increase discoverability"
        
        return {
            "posting_schedule": {
                "frequency": frequency,
                "optimal_times": ["10:00 AM", "2:00 PM", "7:00 PM"],
                "consistency": "Maintain regular posting schedule"
            },
            "content_strategy": {
                "themes_to_explore": themes[:3] if themes else ["Affirmations", "Personal Growth", "Mindfulness"],
                "hashtag_strategy": hashtag_rec,
                "engagement_goal": f"Aim for {int(engagement.get('total_engagement', 50) * 1.2)} total engagement per post"
            },
            "content_pillars": [
                {
                    "name": "7 Cycles Wisdom",
                    "percentage": 40,
                    "description": "Share insights from each life cycle"
                },
                {
                    "name": "Period-Specific Content",
                    "percentage": 30,
                    "description": "Tailor content to current period themes"
                },
                {
                    "name": "Community Engagement",
                    "percentage": 20,
                    "description": "Ask questions and feature followers"
                },
                {
                    "name": "Visual Content",
                    "percentage": 10,
                    "description": "Share inspiring visuals with quotes"
                }
            ],
            "growth_tactics": [
                "Engage with similar accounts in your niche",
                "Reply to comments within 2-4 hours",
                "Create conversation-starting posts",
                "Share behind-the-scenes content"
            ]
        }
    
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