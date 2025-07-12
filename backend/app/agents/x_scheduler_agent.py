from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta
from pathlib import Path
import uuid
from zoneinfo import ZoneInfo

from app.agents.crews.base_crew import BaseCrew
from app.services.supabase_client import supabase
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI


class XSchedulerAgent(BaseCrew):
    """Agent for scheduling and publishing X (Twitter) posts."""
    
    def __init__(self):
        super().__init__()
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.5
        )
        self.results_path = Path("storage/x_schedules")
        self.results_path.mkdir(parents=True, exist_ok=True)
        self.scheduled_posts = []
    
    def create_crew(self) -> Crew:
        """Create the X scheduling crew."""
        scheduler = Agent(
            role="X (Twitter) Content Scheduler",
            goal="Optimize post scheduling for maximum reach and engagement on X platform",
            backstory="""You are an expert X/Twitter scheduler with deep understanding of platform 
            algorithms, audience behavior patterns, and optimal posting times. You know how to 
            maximize reach by scheduling content when the target audience is most active and engaged. 
            You understand the importance of consistent posting while avoiding overwhelming followers. 
            You're skilled at creating content calendars that maintain momentum, build anticipation, 
            and capitalize on peak engagement windows. You consider time zones, global audience 
            distribution, and platform-specific factors like thread timing and poll duration. 
            Your scheduling strategies consistently result in higher impressions, engagement, and 
            follower growth.""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
        
        return Crew(
            agents=[scheduler],
            tasks=[],
            verbose=True
        )
    
    def schedule_posts(self, 
                      approved_posts: List[Dict[str, Any]], 
                      scheduling_strategy: str = "optimal",
                      start_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Schedule approved posts for publishing."""
        
        if not start_date:
            start_date = datetime.now(ZoneInfo("America/New_York"))
        
        # Create scheduling task
        scheduling_task = Task(
            description=f"""Create an optimal publishing schedule for the approved X/Twitter posts.
            
            Posts to schedule:
            {json.dumps(approved_posts, indent=2)}
            
            Scheduling Strategy: {scheduling_strategy}
            Start Date: {start_date.isoformat()}
            
            Consider the following when creating the schedule:
            
            1. Optimal Posting Times:
               - Peak engagement windows (9 AM, 12:30 PM, 3 PM, 7 PM, 9 PM EST)
               - Audience time zone distribution
               - Day of week patterns
               - Avoid posting during low-engagement hours
            
            2. Content Distribution:
               - Space posts appropriately (minimum 2-3 hours apart)
               - Threads should post during high-attention periods
               - Polls should launch when audience is most active
               - Balance content types throughout the day
            
            3. Platform-Specific Factors:
               - X algorithm favors consistent posting
               - Early engagement (first 30 min) is crucial
               - Thread tweets should post in sequence (1-2 min apart)
               - Consider quote tweet timing for maximum visibility
            
            4. Strategic Considerations:
               - Monday/Thursday for educational threads
               - Tuesday/Friday for engagement posts
               - Weekend for inspirational content
               - Avoid major holidays or events
            
            5. Engagement Optimization:
               - Schedule high-value content during peak hours
               - Use off-peak for experimental content
               - Plan for timezone coverage
               - Consider audience online patterns
            
            Create a schedule that maximizes reach and engagement while maintaining 
            consistent presence on the platform.""",
            expected_output="Detailed posting schedule with timestamps and rationale",
            agent=self.crew.agents[0]
        )
        
        # Execute scheduling
        self.crew.tasks = [scheduling_task]
        result = self.crew.kickoff()
        
        # Create scheduled posts
        scheduled_posts = []
        current_time = start_date
        
        for i, post in enumerate(approved_posts):
            # Determine optimal time based on post type
            if post.get("type") == "thread":
                # Threads get prime morning slot
                scheduled_time = current_time.replace(hour=9, minute=0, second=0)
                if scheduled_time < current_time:
                    scheduled_time += timedelta(days=1)
            elif post.get("type") == "poll":
                # Polls get afternoon engagement slot
                scheduled_time = current_time.replace(hour=15, minute=0, second=0)
                if scheduled_time < current_time:
                    scheduled_time += timedelta(days=1)
            else:
                # Regular posts distributed throughout the day
                hour_options = [9, 12, 15, 19, 21]
                hour = hour_options[i % len(hour_options)]
                scheduled_time = current_time.replace(hour=hour, minute=30, second=0)
                if scheduled_time < current_time:
                    scheduled_time += timedelta(days=1)
            
            # Ensure minimum spacing
            if scheduled_posts and scheduled_time < scheduled_posts[-1]["scheduled_for"] + timedelta(hours=2):
                scheduled_time = scheduled_posts[-1]["scheduled_for"] + timedelta(hours=3)
            
            scheduled_post = {
                "id": str(uuid.uuid4()),
                "post": post,
                "scheduled_for": scheduled_time.isoformat(),
                "timezone": "America/New_York",
                "status": "scheduled",
                "rationale": self._get_scheduling_rationale(post, scheduled_time),
                "expected_reach": self._estimate_reach(post, scheduled_time),
                "created_at": datetime.now().isoformat()
            }
            
            scheduled_posts.append(scheduled_post)
            current_time = scheduled_time
        
        # Create schedule summary
        schedule_data = {
            "schedule_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "scheduling_strategy": scheduling_strategy,
            "posts_count": len(scheduled_posts),
            "scheduled_posts": scheduled_posts,
            "schedule_summary": {
                "first_post": scheduled_posts[0]["scheduled_for"] if scheduled_posts else None,
                "last_post": scheduled_posts[-1]["scheduled_for"] if scheduled_posts else None,
                "daily_distribution": self._calculate_daily_distribution(scheduled_posts),
                "type_distribution": self._calculate_type_distribution(scheduled_posts)
            },
            "ai_scheduling_insights": str(result)
        }
        
        # Save to database
        for sp in scheduled_posts:
            self._save_to_database(sp)
        
        # Save schedule
        filename = f"x_schedule_{schedule_data['schedule_id']}.json"
        filepath = self.results_path / filename
        with open(filepath, 'w') as f:
            json.dump(schedule_data, f, indent=2)
        
        # Save latest
        latest_path = self.results_path / "latest_schedule.json"
        with open(latest_path, 'w') as f:
            json.dump(schedule_data, f, indent=2)
        
        self.scheduled_posts.extend(scheduled_posts)
        
        return schedule_data
    
    def _get_scheduling_rationale(self, post: Dict[str, Any], scheduled_time: datetime) -> str:
        """Generate rationale for scheduling decision."""
        hour = scheduled_time.hour
        day_name = scheduled_time.strftime("%A")
        
        rationales = {
            "thread": f"Scheduled for {hour}:00 on {day_name} - optimal time for thread engagement and completion rates",
            "poll": f"Poll scheduled for {hour}:00 to maximize participation during active hours",
            "single": f"Posted at {hour}:00 for high visibility in feed during peak scrolling time"
        }
        
        return rationales.get(post.get("type", "single"), f"Scheduled for optimal engagement at {hour}:00")
    
    def _estimate_reach(self, post: Dict[str, Any], scheduled_time: datetime) -> Dict[str, Any]:
        """Estimate potential reach based on scheduling."""
        hour = scheduled_time.hour
        
        # Base reach estimates by hour (mock data)
        hourly_multipliers = {
            9: 1.5, 12: 1.8, 15: 1.6, 19: 2.0, 21: 1.7
        }
        
        base_reach = 1000
        multiplier = hourly_multipliers.get(hour, 1.0)
        
        # Type bonuses
        type_bonuses = {
            "thread": 1.5,
            "poll": 1.3,
            "single": 1.0
        }
        
        type_multiplier = type_bonuses.get(post.get("type", "single"), 1.0)
        
        estimated_reach = int(base_reach * multiplier * type_multiplier)
        
        return {
            "impressions": estimated_reach,
            "engagements": int(estimated_reach * 0.05),  # 5% engagement rate
            "profile_clicks": int(estimated_reach * 0.02),  # 2% CTR
            "confidence": "high" if multiplier > 1.5 else "medium"
        }
    
    def _calculate_daily_distribution(self, scheduled_posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate how posts are distributed across days."""
        distribution = {}
        for post in scheduled_posts:
            date = datetime.fromisoformat(post["scheduled_for"]).date().isoformat()
            distribution[date] = distribution.get(date, 0) + 1
        return distribution
    
    def _calculate_type_distribution(self, scheduled_posts: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of post types."""
        distribution = {}
        for post in scheduled_posts:
            post_type = post["post"].get("type", "single")
            distribution[post_type] = distribution.get(post_type, 0) + 1
        return distribution
    
    def _save_to_database(self, scheduled_post: Dict[str, Any]) -> None:
        """Save scheduled post to database."""
        try:
            post_data = {
                "platform": "x",
                "content": scheduled_post["post"].get("content", ""),
                "post_type": scheduled_post["post"].get("type", "single"),
                "hashtags": scheduled_post["post"].get("hashtags", []),
                "period": scheduled_post["post"].get("period", 1),
                "scheduled_for": scheduled_post["scheduled_for"],
                "status": "scheduled",
                "metadata": {
                    "visual_prompt": scheduled_post["post"].get("visual_prompt", ""),
                    "thread_content": scheduled_post["post"].get("thread_content", []),
                    "poll_options": scheduled_post["post"].get("poll_options", []),
                    "expected_reach": scheduled_post["expected_reach"]
                }
            }
            
            # Mock database save
            print(f"Saving X post to database: {post_data['content'][:50]}...")
            
        except Exception as e:
            print(f"Error saving to database: {e}")
    
    def get_latest_schedule(self) -> Dict[str, Any]:
        """Retrieve the most recent schedule."""
        latest_path = self.results_path / "latest_schedule.json"
        if latest_path.exists():
            with open(latest_path, 'r') as f:
                return json.load(f)
        return {"error": "No schedule found"}
    
    def get_upcoming_posts(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get posts scheduled for the next N days."""
        cutoff_date = datetime.now(ZoneInfo("America/New_York")) + timedelta(days=days)
        
        upcoming = []
        for post in self.scheduled_posts:
            scheduled_time = datetime.fromisoformat(post["scheduled_for"])
            if scheduled_time <= cutoff_date and post["status"] == "scheduled":
                upcoming.append(post)
        
        return sorted(upcoming, key=lambda x: x["scheduled_for"])
    
    def publish_scheduled_posts(self) -> Dict[str, Any]:
        """Publish posts that are due."""
        current_time = datetime.now(ZoneInfo("America/New_York"))
        published = []
        
        for post in self.scheduled_posts:
            scheduled_time = datetime.fromisoformat(post["scheduled_for"])
            
            # Convert to timezone-aware if needed
            if scheduled_time.tzinfo is None:
                scheduled_time = scheduled_time.replace(tzinfo=ZoneInfo("America/New_York"))
            
            if scheduled_time <= current_time and post["status"] == "scheduled":
                # Mock publishing
                post["status"] = "published"
                post["published_at"] = current_time.isoformat()
                post["publish_result"] = {
                    "success": True,
                    "tweet_id": f"mock_tweet_{uuid.uuid4().hex[:8]}",
                    "url": f"https://twitter.com/7cycles/status/{uuid.uuid4().hex[:15]}"
                }
                published.append(post)
                
                print(f"Published tweet: {post['post']['content'][:50]}...")
        
        return {
            "published_count": len(published),
            "published_posts": published,
            "timestamp": current_time.isoformat()
        }
    
    def reschedule_post(self, post_id: str, new_time: datetime) -> Dict[str, Any]:
        """Reschedule a specific post."""
        for post in self.scheduled_posts:
            if post["id"] == post_id:
                old_time = post["scheduled_for"]
                post["scheduled_for"] = new_time.isoformat()
                post["rescheduled"] = True
                post["reschedule_history"] = post.get("reschedule_history", [])
                post["reschedule_history"].append({
                    "from": old_time,
                    "to": new_time.isoformat(),
                    "rescheduled_at": datetime.now().isoformat()
                })
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "old_time": old_time,
                    "new_time": new_time.isoformat()
                }
        
        return {"success": False, "error": "Post not found"}
    
    def health_check(self) -> Dict[str, Any]:
        """Check if the X scheduler agent is functioning properly."""
        try:
            # Test LLM connection
            test_response = self.llm.invoke("Test X scheduler connection")
            
            # Count scheduled vs published
            scheduled_count = sum(1 for p in self.scheduled_posts if p["status"] == "scheduled")
            published_count = sum(1 for p in self.scheduled_posts if p["status"] == "published")
            
            return {
                "status": "healthy",
                "agent": "XSchedulerAgent",
                "llm_connected": bool(test_response),
                "storage_accessible": self.results_path.exists(),
                "scheduled_posts": scheduled_count,
                "published_posts": published_count,
                "total_posts": len(self.scheduled_posts)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "agent": "XSchedulerAgent",
                "error": str(e)
            }