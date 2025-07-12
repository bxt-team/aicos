from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from pathlib import Path

from app.agents.crews.base_crew import BaseCrew
from app.agents.x_content_strategy_agent import XContentStrategyAgent
from app.services.supabase_client import get_activities_by_period
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI


class XPostGeneratorAgent(BaseCrew):
    """Agent for generating X (Twitter) posts based on content strategy."""
    
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.8
        )
        self.results_path = Path("storage/x_posts")
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.strategy_agent = XContentStrategyAgent()
    
    def create_crew(self) -> Crew:
        """Create the X post generation crew."""
        content_creator = Agent(
            role="X (Twitter) Content Creator",
            goal="Generate engaging, viral-worthy tweets that embody the 7 Cycles teachings while maximizing platform engagement",
            backstory="""You are a master X/Twitter content creator with a gift for crafting tweets 
            that stop the scroll. You understand the art of the 280-character limit, creating hooks 
            that demand attention, and building threads that keep readers engaged. You excel at 
            translating complex spiritual and personal development concepts from the 7 Cycles methodology 
            into bite-sized, shareable wisdom. You know how to use X's features - from polls to threads 
            to quote tweets - to maximize reach and engagement. Your content consistently goes viral 
            because it combines profound insights with perfect timing and formatting.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        return Crew(
            agents=[content_creator],
            tasks=[],
            verbose=True
        )
    
    def generate_posts(self, 
                      period: int, 
                      post_type: str = "mixed",
                      count: int = 5,
                      strategy_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Generate X posts based on strategy and period."""
        
        # Get latest strategy if not provided
        if not strategy_data:
            strategy_data = self.strategy_agent.get_latest_strategy()
        
        # Get activities for the period
        activities = get_activities_by_period(period)
        activities_context = "\n".join([
            f"- {act['title']}: {act['description']}"
            for act in activities[:5]  # Limit to 5 activities
        ])
        
        # Define period characteristics
        period_themes = {
            1: "New beginnings, infinite possibilities, pure potential",
            2: "Self-discovery, finding your voice, establishing identity",
            3: "Taking action, making impact, building momentum",
            4: "Deep connections, meaningful relationships, community building",
            5: "Transformation, letting go, profound change",
            6: "Integration, wisdom, teaching others",
            7: "Completion, reflection, preparing for renewal"
        }
        
        # Create post generation task
        generation_task = Task(
            description=f"""Generate {count} engaging X/Twitter posts for Period {period} of the 7 Cycles.
            
            Period Theme: {period_themes.get(period, 'Unknown period')}
            
            Available Activities:
            {activities_context}
            
            Content Strategy Context:
            - Content Pillars: {json.dumps(strategy_data.get('content_pillars', {}), indent=2)}
            - Tweet Templates: {json.dumps(strategy_data.get('tweet_templates', {}), indent=2)}
            
            Post Type: {post_type}
            
            Generate diverse content including:
            
            1. Single Tweets (280 chars max):
               - Use compelling hooks from the templates
               - Include 1-2 relevant hashtags
               - End with engaging CTAs
               - Optimize line breaks for readability
               - Consider emojis for visual appeal (sparingly)
            
            2. Thread Starters (if applicable):
               - Create opener tweet with strong hook
               - Outline 3-5 follow-up tweets
               - Each tweet should stand alone but connect
               - Include thread numbering (1/, 2/, etc.)
               - End thread with summary and CTA
            
            3. Poll Tweets (if applicable):
               - Ask engaging questions about the cycle
               - Provide 2-4 meaningful options
               - Frame to encourage participation
            
            4. Quote Tweet Ideas:
               - Identify tweetable quotes from activities
               - Add valuable commentary
               - Connect to current cycle theme
            
            For each post include:
            - Content (respecting character limits)
            - Type (single, thread, poll, quote)
            - Hashtags (2-3 relevant ones)
            - Best posting time
            - Visual suggestions (if applicable)
            - Expected engagement level
            
            Ensure all content:
            - Aligns with Period {period} energy
            - Provides genuine value
            - Encourages engagement
            - Feels authentic and relatable
            - Optimized for X algorithm
            
            Make the tweets shareable, saveable, and conversation-starting.""",
            expected_output=f"{count} fully crafted X posts with all specified elements",
            agent=self.crew.agents[0]
        )
        
        # Execute generation
        self.crew.tasks = [generation_task]
        result = self.crew.kickoff()
        
        # Structure the generated posts
        posts = []
        
        # Generate sample posts based on type and period
        if post_type in ["mixed", "single"]:
            posts.append({
                "type": "single",
                "content": f"Cycle {period} wisdom: {period_themes.get(period, '')}. What if the very thing you're resisting is the doorway to your next breakthrough? 🚪✨\n\n#7Cycles #Period{period} #PersonalGrowth",
                "character_count": 180,
                "hashtags": ["#7Cycles", f"#Period{period}", "#PersonalGrowth"],
                "visual_prompt": "Abstract doorway with light streaming through",
                "best_time": "9:00 AM",
                "expected_engagement": "high",
                "call_to_action": "What are you resisting?",
                "period": period
            })
        
        if post_type in ["mixed", "thread"]:
            posts.append({
                "type": "thread",
                "content": f"1/ Entering Cycle {period} can feel overwhelming. Here's your guide to navigating {period_themes.get(period, 'this phase')} with grace and purpose.\n\nA thread on transformation 🧵",
                "thread_content": [
                    f"2/ First, recognize that Cycle {period} isn't about forcing change. It's about aligning with the natural rhythm of {period_themes.get(period, 'growth')}.",
                    f"3/ The key practice for this cycle: {activities[0]['title'] if activities else 'Daily reflection'}. Start with just 5 minutes each morning.",
                    "4/ Common mistakes to avoid:\n- Rushing the process\n- Comparing your journey\n- Ignoring the signs\n- Skipping the inner work",
                    f"5/ Remember: Cycle {period} is temporary but transformative. What you learn here becomes the foundation for your next evolution.\n\nWhat's your biggest challenge in this cycle? Let's discuss below 👇"
                ],
                "character_count": 220,
                "hashtags": ["#7Cycles", f"#Cycle{period}", "#Thread"],
                "best_time": "12:30 PM",
                "expected_engagement": "very high",
                "period": period
            })
        
        if post_type in ["mixed", "poll"]:
            posts.append({
                "type": "poll",
                "content": f"Quick check-in: If you're in Cycle {period} ({period_themes.get(period, 'transformation')}), what's your biggest challenge right now? 🤔",
                "poll_options": [
                    "Letting go of the past",
                    "Trusting the process",
                    "Finding my direction",
                    "Staying motivated"
                ],
                "poll_duration": "1 day",
                "hashtags": ["#7Cycles", f"#Cycle{period}"],
                "best_time": "3:00 PM",
                "expected_engagement": "high",
                "period": period
            })
        
        # Add activity-based posts
        for i, activity in enumerate(activities[:2]):
            posts.append({
                "type": "single",
                "content": f"Today's Cycle {period} practice: {activity['title']}\n\n{activity['description'][:150]}...\n\nWho's trying this with me today? 🙋‍♀️\n\n#7Cycles #DailyPractice",
                "character_count": 235,
                "hashtags": ["#7Cycles", "#DailyPractice", f"#Cycle{period}"],
                "visual_prompt": activity.get('visual_prompt', 'Person practicing mindfulness'),
                "best_time": "7:00 PM",
                "expected_engagement": "medium",
                "activity_id": activity['id'],
                "period": period
            })
        
        # Add raw AI response
        posts.append({
            "type": "ai_generated",
            "content": str(result),
            "period": period,
            "metadata": {
                "generation_date": datetime.now().isoformat(),
                "strategy_version": strategy_data.get('strategy_date', 'unknown'),
                "post_type_requested": post_type,
                "count_requested": count
            }
        })
        
        # Save generated posts
        filename = f"x_posts_period{period}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.results_path / filename
        with open(filepath, 'w') as f:
            json.dump(posts, f, indent=2)
        
        # Also save latest
        latest_path = self.results_path / f"latest_posts_period{period}.json"
        with open(latest_path, 'w') as f:
            json.dump(posts, f, indent=2)
        
        return posts
    
    def get_latest_posts(self, period: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve the most recent generated posts."""
        if period:
            latest_path = self.results_path / f"latest_posts_period{period}.json"
        else:
            # Get most recent file
            files = sorted(self.results_path.glob("latest_posts_period*.json"))
            if not files:
                return []
            latest_path = files[-1]
        
        if latest_path.exists():
            with open(latest_path, 'r') as f:
                return json.load(f)
        return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the X post generator agent is functioning properly."""
        try:
            # Test LLM connection
            test_response = self.llm.invoke("Test X post generator connection")
            
            return {
                "status": "healthy",
                "agent": "XPostGeneratorAgent",
                "llm_connected": bool(test_response),
                "storage_accessible": self.results_path.exists()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent": "XPostGeneratorAgent",
                "error": str(e)
            }