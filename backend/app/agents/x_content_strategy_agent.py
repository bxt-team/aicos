from typing import Dict, Any, Optional
import json
from datetime import datetime
from pathlib import Path

from app.agents.crews.base_crew import BaseCrew
from app.agents.x_analysis_agent import XAnalysisAgent
from app.services.supabase_client import get_all_activities
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI


class XContentStrategyAgent(BaseCrew):
    """Agent for creating X (Twitter) content strategies based on analysis."""
    
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.7
        )
        self.results_path = Path("storage/x_strategy")
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.analysis_agent = XAnalysisAgent()
    
    def create_crew(self) -> Crew:
        """Create the X content strategy crew."""
        strategist = Agent(
            role="X (Twitter) Content Strategist",
            goal="Create comprehensive X content strategies that maximize engagement and align with the 7 Cycles methodology",
            backstory="""You are a seasoned X/Twitter content strategist with expertise in viral content 
            creation, audience growth, and platform algorithms. You understand how to leverage X's unique 
            features like threads, polls, and real-time engagement to build communities. You excel at 
            creating content strategies that balance educational value with entertainment, optimize for 
            the platform's character limits, and drive meaningful engagement. You have deep knowledge 
            of the 7 Cycles of Life methodology and how to adapt it for X's fast-paced environment.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        return Crew(
            agents=[strategist],
            tasks=[],
            verbose=True
        )
    
    def create_strategy(self, analysis_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a comprehensive X content strategy."""
        
        # Get latest analysis if not provided
        if not analysis_data:
            analysis_data = self.analysis_agent.get_latest_analysis()
        
        # Get activities from database
        activities = get_all_activities()
        activities_summary = [
            f"Period {act['period']}: {act['title']} - {act['description'][:100]}..."
            for act in activities[:10]  # Limit to first 10 for context
        ]
        
        # Create strategy task
        strategy_task = Task(
            description=f"""Based on the X profile analysis, create a comprehensive content strategy 
            that incorporates the 7 Cycles of Life methodology.
            
            Analysis Insights:
            {json.dumps(analysis_data, indent=2)}
            
            Available Activities:
            {chr(10).join(activities_summary)}
            
            Create a strategy that includes:
            
            1. Content Pillars (aligned with 7 Cycles):
               - Define 4-5 main content themes
               - Map each pillar to specific life cycles
               - Balance educational and inspirational content
               - Include activity-based content from the database
            
            2. Tweet Formats & Types:
               - Single tweet templates (280 chars)
               - Thread structures for deep dives
               - Poll ideas for engagement
               - Quote tweet strategies
               - Visual content recommendations
            
            3. Posting Schedule:
               - Daily posting frequency
               - Optimal times based on analysis
               - Thread publishing days
               - Special series or campaigns
               - Live-tweeting opportunities
            
            4. Engagement Strategy:
               - Reply and interaction guidelines
               - Community building tactics
               - Hashtag campaigns (#7Cycles variations)
               - Influencer engagement plan
               - User-generated content ideas
            
            5. Growth Tactics:
               - Follower acquisition strategies
               - Viral content formulas
               - Twitter Spaces planning
               - Cross-promotion opportunities
               - Algorithm optimization tips
            
            6. Content Calendar Framework:
               - Weekly themes aligned with cycles
               - Monthly focus areas
               - Seasonal content planning
               - Event-based content
               - Evergreen content bank
            
            7. Performance Metrics:
               - KPIs to track
               - Engagement benchmarks
               - Growth targets
               - Content performance indicators
            
            Ensure the strategy is actionable, measurable, and specifically optimized for X's platform.""",
            expected_output="Complete X content strategy with specific tactics, templates, and schedules",
            agent=self.crew.agents[0]
        )
        
        # Execute strategy creation
        self.crew.tasks = [strategy_task]
        result = self.crew.kickoff()
        
        # Structure the strategy
        strategy_data = {
            "strategy_date": datetime.now().isoformat(),
            "based_on_analysis": analysis_data.get("analysis_date", "N/A"),
            "content_pillars": {
                "pillar_1": {
                    "name": "7 Cycles Wisdom",
                    "description": "Daily insights and teachings from each life cycle",
                    "cycles": [1, 2, 3, 4, 5, 6, 7],
                    "content_ratio": "25%",
                    "formats": ["Single tweets", "Weekly wisdom threads", "Quote graphics"]
                },
                "pillar_2": {
                    "name": "Transformation Stories",
                    "description": "Real-life examples of people navigating their cycles",
                    "cycles": [3, 4, 5],
                    "content_ratio": "20%",
                    "formats": ["Story threads", "Before/after posts", "Testimonials"]
                },
                "pillar_3": {
                    "name": "Daily Practices",
                    "description": "Actionable activities from the 7 Cycles methodology",
                    "cycles": [1, 2, 6, 7],
                    "content_ratio": "30%",
                    "formats": ["How-to tweets", "Step-by-step threads", "Video tutorials"]
                },
                "pillar_4": {
                    "name": "Community Conversations",
                    "description": "Engaging the community in cycle-related discussions",
                    "cycles": [1, 2, 3, 4, 5, 6, 7],
                    "content_ratio": "15%",
                    "formats": ["Polls", "Q&A threads", "Twitter Spaces"]
                },
                "pillar_5": {
                    "name": "Cycle Challenges",
                    "description": "Weekly challenges to help followers apply the teachings",
                    "cycles": [2, 3, 4, 5],
                    "content_ratio": "10%",
                    "formats": ["Challenge announcements", "Progress check-ins", "Winner spotlights"]
                }
            },
            "tweet_templates": {
                "single_tweet": {
                    "hook_formulas": [
                        "[Cycle {number}] taught me that...",
                        "The secret to {benefit} lies in understanding...",
                        "Most people don't realize that {cycle concept}..."
                    ],
                    "structure": "Hook + Insight + Call-to-action",
                    "character_optimization": "Use line breaks for readability, emojis sparingly"
                },
                "thread_structure": {
                    "opener": "Strong hook tweet with promise of value",
                    "body": "3-7 tweets with one key point each",
                    "closer": "Summary + CTA + invitation to share",
                    "formatting": "Number tweets, use emojis as bullet points"
                },
                "poll_ideas": [
                    "Which life cycle are you currently in?",
                    "What's your biggest challenge right now?",
                    "Which practice resonates most with you?"
                ]
            },
            "posting_schedule": {
                "frequency": "4-5 tweets daily",
                "times": ["9:00 AM", "12:30 PM", "3:00 PM", "7:00 PM", "9:00 PM"],
                "thread_days": ["Monday", "Thursday"],
                "poll_days": ["Wednesday", "Saturday"],
                "spaces_schedule": "Bi-weekly on Tuesdays at 8 PM"
            },
            "engagement_tactics": {
                "reply_strategy": "Respond within 2 hours to boost algorithm favor",
                "retweet_strategy": "RT with commentary to add value",
                "hashtag_strategy": {
                    "primary": ["#7Cycles", "#LifeCycles", "#PersonalGrowth"],
                    "secondary": ["#Transformation", "#DailyPractice", "#Mindfulness"],
                    "trending": "Monitor and join relevant trending topics"
                },
                "community_building": [
                    "Host weekly #7CyclesChat",
                    "Feature follower transformations",
                    "Create cycle-buddy matching threads"
                ]
            },
            "growth_tactics": {
                "follower_acquisition": [
                    "Engage with personal development influencers",
                    "Share valuable threads in relevant communities",
                    "Cross-promote with complementary accounts"
                ],
                "viral_formulas": [
                    "Counterintuitive insights from the cycles",
                    "Before/after transformation threads",
                    "Universal truths packaged uniquely"
                ],
                "algorithm_optimization": [
                    "Post when followers are most active",
                    "Encourage replies over likes",
                    "Use native video over links"
                ]
            },
            "content_calendar": {
                "monday": "Motivation Monday - New cycle beginnings",
                "tuesday": "Transformation Tuesday - Success stories",
                "wednesday": "Wisdom Wednesday - Deep cycle insights",
                "thursday": "Thoughtful Thursday - Reflection threads",
                "friday": "Focus Friday - Practical exercises",
                "saturday": "Share Saturday - Community spotlight",
                "sunday": "Sunday Synthesis - Week recap & preview"
            },
            "performance_metrics": {
                "engagement_rate": "Target: 5-8%",
                "follower_growth": "Target: 10% monthly",
                "thread_completion": "Target: 60% read-through",
                "profile_visits": "Target: 20% click-through from tweets",
                "key_metrics": ["Impressions", "Engagements", "Profile clicks", "Follows"]
            },
            "raw_strategy": str(result)
        }
        
        # Save strategy
        filename = f"x_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.results_path / filename
        with open(filepath, 'w') as f:
            json.dump(strategy_data, f, indent=2)
        
        # Also save latest
        latest_path = self.results_path / "latest_strategy.json"
        with open(latest_path, 'w') as f:
            json.dump(strategy_data, f, indent=2)
        
        return strategy_data
    
    def get_latest_strategy(self) -> Dict[str, Any]:
        """Retrieve the most recent strategy."""
        latest_path = self.results_path / "latest_strategy.json"
        if latest_path.exists():
            with open(latest_path, 'r') as f:
                return json.load(f)
        return {"error": "No strategy found"}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the X content strategy agent is functioning properly."""
        try:
            # Test LLM connection
            test_response = self.llm.invoke("Test X strategy agent connection")
            
            return {
                "status": "healthy",
                "agent": "XContentStrategyAgent",
                "llm_connected": bool(test_response),
                "storage_accessible": self.results_path.exists()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent": "XContentStrategyAgent",
                "error": str(e)
            }