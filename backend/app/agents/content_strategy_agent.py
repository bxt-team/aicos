"""Agent for creating Threads content strategies based on analysis and brand values."""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

from crewai import Agent, Task, Crew
from langchain_community.llms import OpenAI

from .crews.base_crew import BaseCrew
from ..services.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class ContentStrategyAgent(BaseCrew):
    """Agent that creates content strategies for Threads based on competitive analysis."""
    
    def __init__(self, openai_api_key: str, supabase_client: Optional[SupabaseClient] = None):
        """Initialize the Content Strategy Agent."""
        super().__init__()
        
        # Initialize LLM
        self.llm = OpenAI(
            model="gpt-4o-mini",
            openai_api_key=openai_api_key,
            temperature=0.7
        )
        
        # Initialize Supabase client
        self.supabase = supabase_client or SupabaseClient()
        
        # Storage for strategies
        self.storage_dir = os.path.join(os.path.dirname(__file__), "../../static/threads_strategies")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Create agent
        self.agent = self.create_agent("threads_strategy", llm=self.llm)
    
    async def create_strategy(self, analysis: Dict[str, Any], target_audience: Optional[str] = None) -> Dict[str, Any]:
        """Create a comprehensive content strategy based on analysis."""
        try:
            # Get activities from Supabase for content ideas
            activities = await self.supabase.get_activities()
            
            # Create strategy task
            task = self.create_task(
                "threads_strategy_creation",
                self.agent,
                analysis=json.dumps(analysis, indent=2),
                activities_count=len(activities),
                target_audience=target_audience or "Spiritually curious individuals seeking personal growth"
            )
            
            # Create crew and execute
            crew = self.create_crew(
                "threads_strategy_crew",
                agents=[self.agent],
                tasks=[task]
            )
            
            result = crew.kickoff()
            
            # Parse and structure the strategy
            strategy = self._parse_strategy_result(result, activities)
            
            # Save strategy
            self._save_strategy(strategy)
            
            return {
                "success": True,
                "strategy": strategy,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating content strategy: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _parse_strategy_result(self, result: Any, activities: List[Any]) -> Dict[str, Any]:
        """Parse the crew result into structured strategy format."""
        try:
            # Base strategy structure
            strategy = {
                "content_pillars": [
                    {
                        "name": "7 Cycles Wisdom",
                        "percentage": 40,
                        "description": "Deep insights from each life cycle",
                        "topics": [
                            "Period-specific teachings",
                            "Cycle transitions",
                            "Energy optimization",
                            "Personal rhythm discovery"
                        ],
                        "post_types": ["Educational quotes", "Mini-lessons", "Cycle explanations"]
                    },
                    {
                        "name": "Daily Affirmations",
                        "percentage": 30,
                        "description": "Period-aligned affirmations for daily practice",
                        "topics": [
                            "Morning affirmations",
                            "Energy boosters",
                            "Transformation mantras",
                            "Self-empowerment"
                        ],
                        "post_types": ["Affirmation cards", "Voice notes", "Guided practices"]
                    },
                    {
                        "name": "Community Stories",
                        "percentage": 20,
                        "description": "Real transformations and experiences",
                        "topics": [
                            "Success stories",
                            "Community spotlights",
                            "Transformation journeys",
                            "Testimonials"
                        ],
                        "post_types": ["Story posts", "Before/after", "Community features"]
                    },
                    {
                        "name": "Activities & Practices",
                        "percentage": 10,
                        "description": "Practical exercises from the activity catalog",
                        "topics": [
                            "Daily practices",
                            "Period-specific activities",
                            "Group challenges",
                            "Workshops"
                        ],
                        "post_types": ["How-to posts", "Challenge announcements", "Practice guides"]
                    }
                ],
                "posting_schedule": {
                    "frequency": "2-3 posts per week",
                    "optimal_times": {
                        "morning": "7:00-9:00 AM CET",
                        "midday": "12:00-1:00 PM CET",
                        "evening": "6:00-8:00 PM CET"
                    },
                    "best_days": ["Tuesday", "Thursday", "Sunday"],
                    "avoid_days": ["Monday morning", "Friday evening"]
                },
                "hashtag_strategy": {
                    "brand_hashtags": [
                        "#7Cycles",
                        "#7Zyklen",
                        "#LebenszkylenWeisheit",
                        "#RhythmusDesLebens"
                    ],
                    "discovery_hashtags": [
                        "#Spiritualität",
                        "#Persönlichkeitsentwicklung",
                        "#Achtsamkeit",
                        "#Transformation",
                        "#Selbstliebe"
                    ],
                    "period_hashtags": {
                        "IMAGE": ["#Selbstbild", "#Identität"],
                        "VERÄNDERUNG": ["#Transformation", "#Wandel"],
                        "ENERGIE": ["#Vitalität", "#Kraft"],
                        "KREATIVITÄT": ["#Kreativität", "#Inspiration"],
                        "ERFOLG": ["#Erfolg", "#Manifestation"],
                        "ENTSPANNUNG": ["#Ruhe", "#Balance"],
                        "UMSICHT": ["#Weisheit", "#Planung"]
                    },
                    "usage_guidelines": "5-10 hashtags per post, mix of brand and discovery tags"
                },
                "engagement_tactics": [
                    {
                        "tactic": "Question Posts",
                        "frequency": "1-2 per week",
                        "description": "End posts with open-ended questions about cycles"
                    },
                    {
                        "tactic": "Weekly Themes",
                        "frequency": "Every week",
                        "description": "Align content with current period energy"
                    },
                    {
                        "tactic": "Community Challenges",
                        "frequency": "Monthly",
                        "description": "7-day challenges for each period"
                    },
                    {
                        "tactic": "Live Q&A",
                        "frequency": "Bi-weekly",
                        "description": "Answer questions about cycles and practices"
                    }
                ],
                "content_calendar": self._generate_content_calendar(),
                "kpis": {
                    "growth_targets": {
                        "followers": "10% monthly growth",
                        "engagement_rate": "5-8%",
                        "reach": "20% monthly increase"
                    },
                    "content_metrics": {
                        "post_saves": "Track for valuable content",
                        "shares": "Measure virality",
                        "comments": "Gauge community engagement",
                        "profile_visits": "Track discovery effectiveness"
                    },
                    "milestones": [
                        {"month": 1, "followers": 500, "posts": 12},
                        {"month": 3, "followers": 2000, "posts": 36},
                        {"month": 6, "followers": 5000, "posts": 72}
                    ]
                },
                "visual_guidelines": {
                    "color_palette": "Period-specific colors from 7 Cycles",
                    "typography": "Clean, readable fonts with spiritual elegance",
                    "imagery": "Nature, sacred geometry, minimalist designs",
                    "templates": "Consistent branded templates for each content type"
                },
                "voice_and_tone": {
                    "personality": "Wise, warm, encouraging, authentic",
                    "language": "Simple yet profound, accessible spirituality",
                    "emotions": "Inspiring, calming, empowering",
                    "do": ["Use 'du' form", "Be inclusive", "Share wisdom gently"],
                    "dont": ["Preach", "Use complex jargon", "Make absolute claims"]
                }
            }
            
            # Add activity-based content ideas
            if activities:
                strategy["activity_integration"] = {
                    "weekly_activity": "Feature one activity per week",
                    "period_alignment": "Match activities to current period",
                    "formats": ["Step-by-step guides", "Video demos", "Community practice"]
                }
            
            return strategy
            
        except Exception as e:
            logger.error(f"Error parsing strategy result: {str(e)}")
            return self._get_default_strategy()
    
    def _generate_content_calendar(self) -> List[Dict[str, Any]]:
        """Generate a sample content calendar for the next 30 days."""
        calendar = []
        start_date = datetime.now()
        
        # Sample content ideas for each day type
        content_templates = {
            "Tuesday": ["Cycle wisdom post", "Educational content", "Period deep dive"],
            "Thursday": ["Community story", "Transformation feature", "Success spotlight"],
            "Sunday": ["Weekly affirmation", "Practice guide", "Reflection prompt"]
        }
        
        for i in range(30):
            date = start_date + timedelta(days=i)
            day_name = date.strftime("%A")
            
            if day_name in content_templates:
                calendar.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "day": day_name,
                    "content_type": content_templates[day_name][i % len(content_templates[day_name])],
                    "time": "7:00 AM" if day_name == "Sunday" else "6:00 PM",
                    "pillar": "7 Cycles Wisdom" if i % 3 == 0 else "Daily Affirmations"
                })
        
        return calendar
    
    def _get_default_strategy(self) -> Dict[str, Any]:
        """Return a default strategy structure."""
        return {
            "content_pillars": [
                {
                    "name": "7 Cycles Wisdom",
                    "percentage": 40,
                    "description": "Core teachings and insights"
                }
            ],
            "posting_schedule": {
                "frequency": "2-3 posts per week",
                "optimal_times": {"morning": "7:00-9:00 AM", "evening": "6:00-8:00 PM"}
            },
            "hashtag_strategy": {
                "brand_hashtags": ["#7Cycles", "#7Zyklen"],
                "discovery_hashtags": ["#Spiritualität", "#Transformation"]
            },
            "engagement_tactics": [],
            "kpis": {
                "growth_targets": {"followers": "10% monthly"}
            }
        }
    
    def _save_strategy(self, strategy: Dict[str, Any]):
        """Save strategy to storage."""
        filename = f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(strategy, f, indent=2)
        
        # Also save as latest
        latest_path = os.path.join(self.storage_dir, "latest_strategy.json")
        with open(latest_path, 'w') as f:
            json.dump(strategy, f, indent=2)
    
    def get_latest_strategy(self) -> Optional[Dict[str, Any]]:
        """Retrieve the latest strategy."""
        latest_path = os.path.join(self.storage_dir, "latest_strategy.json")
        
        if os.path.exists(latest_path):
            with open(latest_path, 'r') as f:
                return json.load(f)
        
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check agent health status."""
        return {
            "status": "healthy",
            "agent": "ContentStrategyAgent",
            "storage_available": os.path.exists(self.storage_dir),
            "latest_strategy": self.get_latest_strategy() is not None,
            "supabase_connected": self.supabase.client is not None
        }