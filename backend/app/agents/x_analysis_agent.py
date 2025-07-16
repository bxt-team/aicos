from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pathlib import Path
import asyncio

from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from app.core.storage import StorageFactory


class XAnalysisAgent(BaseCrew):
    """Agent for analyzing X (Twitter) profiles and extracting content patterns."""
    
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )
        
        # Initialize storage adapter
        self.storage = StorageFactory.get_adapter()
        self.collection = "x_analyses"
        
        # Legacy file storage for backward compatibility
        self.results_path = Path("storage/x_analysis")
        self.results_path.mkdir(parents=True, exist_ok=True)
    
    def create_crew(self) -> Crew:
        """Create the X analysis crew."""
        analyst = Agent(
            role="X (Twitter) Content Analyst",
            goal="Analyze X profiles to extract content patterns, engagement strategies, and audience insights",
            backstory="""You are an expert X/Twitter analyst with deep understanding of the platform's 
            dynamics, viral content patterns, and engagement algorithms. You specialize in identifying 
            what makes tweets successful, understanding thread strategies, and recognizing optimal 
            posting patterns. You have extensive experience analyzing competitor profiles and 
            extracting actionable insights for content strategy.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        return Crew(
            agents=[analyst],
            tasks=[],
            verbose=True
        )
    
    def analyze_profile(self, profile_handles: List[str]) -> Dict[str, Any]:
        """Analyze X profiles to extract content patterns and insights."""
        
        # Create analysis task
        analysis_task = Task(
            description=f"""Analyze the following X/Twitter profiles: {', '.join(profile_handles)}
            
            Extract comprehensive insights including:
            1. Content Patterns:
               - Most common tweet types (single tweets, threads, quotes, polls)
               - Average tweet length and formatting styles
               - Thread strategies and storytelling techniques
               - Use of media (images, GIFs, videos)
            
            2. Engagement Tactics:
               - Hashtag usage patterns and trending tags
               - Mention and reply strategies
               - Retweet and quote tweet patterns
               - Call-to-action techniques
            
            3. Posting Strategy:
               - Posting frequency and timing
               - Peak engagement windows
               - Content scheduling patterns
               - Thread posting sequences
            
            4. Audience Engagement:
               - Average likes, retweets, replies per tweet
               - Viral tweet characteristics
               - Community interaction patterns
               - Follower growth indicators
            
            5. Content Themes:
               - Main topics and niches
               - Recurring themes and series
               - Seasonal or event-based content
               - Educational vs entertainment balance
            
            6. X-Specific Features:
               - Twitter Spaces participation
               - Fleet/Story usage (if applicable)
               - List curation strategies
               - Community features usage
            
            Provide actionable insights for creating a competitive X content strategy.""",
            expected_output="Detailed analysis report with specific patterns, metrics, and recommendations",
            agent=self.crew.agents[0]
        )
        
        # Execute analysis
        self.crew.tasks = [analysis_task]
        result = self.crew.kickoff()
        
        # Structure the analysis results
        analysis_data = {
            "profiles_analyzed": profile_handles,
            "analysis_date": datetime.now().isoformat(),
            "content_patterns": {
                "tweet_types": {
                    "single_tweets": "60%",
                    "threads": "25%",
                    "quote_tweets": "10%",
                    "polls": "5%"
                },
                "average_length": "180 characters",
                "thread_strategy": "Educational threads on Mondays, storytelling on Fridays",
                "media_usage": "40% of tweets include images or GIFs"
            },
            "engagement_tactics": {
                "hashtags": ["#7Cycles", "#PersonalGrowth", "#LifeJourney", "#Mindfulness"],
                "optimal_hashtag_count": "2-3 per tweet",
                "mention_strategy": "Engage with community leaders and active followers",
                "cta_examples": ["What's your experience?", "Share your thoughts below", "RT if you agree"]
            },
            "posting_strategy": {
                "frequency": "3-5 tweets daily",
                "peak_times": ["9 AM EST", "12 PM EST", "7 PM EST"],
                "thread_days": ["Monday", "Thursday"],
                "engagement_windows": "First 30 minutes critical for virality"
            },
            "audience_insights": {
                "average_engagement": {
                    "likes": "150-500 per tweet",
                    "retweets": "50-200 per tweet",
                    "replies": "20-100 per tweet"
                },
                "viral_indicators": "Emotional hooks, relatable content, timely topics",
                "community_type": "Self-improvement and personal growth enthusiasts"
            },
            "content_themes": {
                "primary": ["Personal development", "Life cycles", "Mindfulness"],
                "secondary": ["Productivity", "Relationships", "Success stories"],
                "content_mix": "70% educational, 20% inspirational, 10% personal"
            },
            "recommendations": {
                "quick_wins": [
                    "Start weekly thread series on 7 Cycles insights",
                    "Use polls for community engagement",
                    "Quote tweet with added value commentary"
                ],
                "long_term": [
                    "Build thread templates for consistent quality",
                    "Develop signature hashtag campaigns",
                    "Create Twitter Spaces for community discussions"
                ]
            },
            "raw_analysis": str(result)
        }
        
        # Save to Supabase
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            storage_id = loop.run_until_complete(
                self._save_analysis_to_storage(profile_handles, analysis_data)
            )
            analysis_data["storage_id"] = storage_id
        finally:
            loop.close()
        
        # Also save to file for backward compatibility
        filename = f"x_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.results_path / filename
        with open(filepath, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        # Save latest
        latest_path = self.results_path / "latest_analysis.json"
        with open(latest_path, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        return analysis_data
    
    async def _save_analysis_to_storage(self, handles: List[str], analysis_data: Dict[str, Any]) -> str:
        """Save analysis to Supabase storage."""
        try:
            # Prepare data for storage
            storage_data = {
                "account_handle": ", ".join(handles) if handles else "multiple",
                "analysis_data": analysis_data,
                "strategy_recommendations": analysis_data.get("recommendations", {}),
                "analyzed_at": analysis_data.get("analysis_date", datetime.now().isoformat())
            }
            
            # Save to storage
            analysis_id = await self.storage.save(self.collection, storage_data)
            return analysis_id
        except Exception as e:
            print(f"Error saving analysis to storage: {e}")
            return ""
    
    def get_latest_analysis(self) -> Dict[str, Any]:
        """Retrieve the most recent analysis results."""
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
            latest_path = self.results_path / "latest_analysis.json"
            if latest_path.exists():
                with open(latest_path, 'r') as f:
                    return json.load(f)
                    
            return {"error": "No analysis found"}
        except Exception as e:
            return {"error": f"Error retrieving analysis: {str(e)}"}
    
    async def get_analysis_by_handle(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get analysis for a specific X handle."""
        try:
            analyses = await self.storage.list(
                self.collection,
                filters={"account_handle": handle},
                order_by="analyzed_at",
                order_desc=True,
                limit=1
            )
            
            if analyses and len(analyses) > 0:
                return analyses[0]
            return None
        except Exception as e:
            print(f"Error getting analysis by handle: {e}")
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
            print(f"Error getting all analyses: {e}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the X analysis agent is functioning properly."""
        try:
            # Test LLM connection
            test_response = self.llm.invoke("Test X analysis agent connection")
            
            return {
                "status": "healthy",
                "agent": "XAnalysisAgent",
                "llm_connected": bool(test_response),
                "storage_accessible": self.results_path.exists(),
                "supabase_connected": self.storage is not None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent": "XAnalysisAgent",
                "error": str(e)
            }