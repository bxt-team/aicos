"""Agent for scheduling and publishing approved Threads posts."""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, time
import logging
import random
from dataclasses import dataclass

from crewai import Agent, Task, Crew
from langchain_community.llms import OpenAI

from .crews.base_crew import BaseCrew
from ..services.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


@dataclass
class ScheduleSlot:
    """Represents a time slot for posting."""
    date: datetime
    time_category: str  # morning, midday, evening
    content_type: str   # affirmation, wisdom, activity, etc.
    is_peak_time: bool


class SchedulerAgent(BaseCrew):
    """Agent that schedules approved Threads posts for optimal engagement."""
    
    def __init__(self, openai_api_key: str, supabase_client: Optional[SupabaseClient] = None):
        """Initialize the Scheduler Agent."""
        super().__init__()
        
        # Initialize LLM
        self.llm = OpenAI(
            model="gpt-4o-mini",
            openai_api_key=openai_api_key,
            temperature=0.3
        )
        
        # Initialize Supabase client
        self.supabase = supabase_client or SupabaseClient()
        
        # Storage for schedules
        self.storage_dir = os.path.join(os.path.dirname(__file__), "../../static/threads_schedules")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Create agent
        self.agent = self.create_agent("threads_scheduler", llm=self.llm)
        
        # Define optimal posting times (CET/CEST)
        self.posting_times = {
            "morning": {
                "start": time(7, 0),
                "end": time(9, 0),
                "peak": time(8, 0),
                "content_types": ["affirmation", "inspiration", "motivation"]
            },
            "midday": {
                "start": time(12, 0),
                "end": time(13, 0),
                "peak": time(12, 30),
                "content_types": ["activity", "tip", "quick_wisdom"]
            },
            "evening": {
                "start": time(18, 0),
                "end": time(20, 0),
                "peak": time(19, 0),
                "content_types": ["reflection", "community", "wisdom", "story"]
            }
        }
        
        # Best posting days (ordered by preference)
        self.best_days = ["Tuesday", "Thursday", "Sunday", "Wednesday", "Saturday"]
        self.avoid_times = [
            ("Monday", "morning"),  # People catching up with work
            ("Friday", "evening")   # Weekend starts
        ]
    
    async def schedule_posts(
        self,
        posts: List[Dict[str, Any]],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        posts_per_week: int = 3
    ) -> Dict[str, Any]:
        """Schedule approved posts optimally within the given timeframe."""
        try:
            # Set default dates if not provided
            if not start_date:
                start_date = datetime.now() + timedelta(days=1)  # Start tomorrow
            if not end_date:
                end_date = start_date + timedelta(days=30)  # 30 days by default
            
            # Create scheduling task
            task = self.create_task(
                "threads_scheduling",
                self.agent,
                posts=json.dumps(posts, indent=2, ensure_ascii=False),
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat()
            )
            
            # Create crew and execute
            crew = self.create_crew(
                "threads_scheduling_crew",
                agents=[self.agent],
                tasks=[task]
            )
            
            result = crew.kickoff()
            
            # Generate optimal schedule
            schedule = self._generate_optimal_schedule(posts, start_date, end_date, posts_per_week)
            
            # Save schedule
            self._save_schedule(schedule)
            
            # Update posts in database
            await self._update_scheduled_posts(schedule)
            
            return {
                "success": True,
                "schedule": schedule,
                "summary": self._generate_schedule_summary(schedule),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling posts: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_optimal_schedule(
        self,
        posts: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
        posts_per_week: int
    ) -> Dict[str, Any]:
        """Generate an optimal posting schedule."""
        schedule = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "posts_per_week": posts_per_week,
            "scheduled_posts": [],
            "schedule_by_week": {}
        }
        
        # Generate available time slots
        slots = self._generate_time_slots(start_date, end_date, posts_per_week)
        
        # Assign posts to slots
        for i, post in enumerate(posts):
            if i >= len(slots):
                break
                
            slot = slots[i]
            scheduled_post = {
                "post": post,
                "scheduled_for": slot.date.isoformat(),
                "time_category": slot.time_category,
                "day_of_week": slot.date.strftime("%A"),
                "is_peak_time": slot.is_peak_time,
                "expected_reach": self._estimate_reach(slot, post)
            }
            
            schedule["scheduled_posts"].append(scheduled_post)
            
            # Group by week
            week_key = slot.date.strftime("%Y-W%V")
            if week_key not in schedule["schedule_by_week"]:
                schedule["schedule_by_week"][week_key] = []
            schedule["schedule_by_week"][week_key].append(scheduled_post)
        
        return schedule
    
    def _generate_time_slots(
        self,
        start_date: datetime,
        end_date: datetime,
        posts_per_week: int
    ) -> List[ScheduleSlot]:
        """Generate available time slots for posting."""
        slots = []
        current_date = start_date
        
        while current_date <= end_date:
            day_name = current_date.strftime("%A")
            
            # Skip if not a good posting day
            if day_name not in self.best_days:
                current_date += timedelta(days=1)
                continue
            
            # Check each time category
            for time_category, time_info in self.posting_times.items():
                # Skip avoided times
                if (day_name, time_category) in self.avoid_times:
                    continue
                
                # Create slot with peak time
                slot_time = datetime.combine(
                    current_date.date(),
                    time_info["peak"]
                )
                
                # Add some randomness to avoid being too predictable
                random_minutes = random.randint(-15, 15)
                slot_time += timedelta(minutes=random_minutes)
                
                slots.append(ScheduleSlot(
                    date=slot_time,
                    time_category=time_category,
                    content_type=random.choice(time_info["content_types"]),
                    is_peak_time=True
                ))
            
            current_date += timedelta(days=1)
        
        # Sort by date and limit to required posts per week
        slots.sort(key=lambda x: x.date)
        
        # Filter to maintain posts_per_week rate
        filtered_slots = []
        week_posts = {}
        
        for slot in slots:
            week_key = slot.date.strftime("%Y-W%V")
            if week_key not in week_posts:
                week_posts[week_key] = 0
            
            if week_posts[week_key] < posts_per_week:
                filtered_slots.append(slot)
                week_posts[week_key] += 1
        
        return filtered_slots
    
    def _estimate_reach(self, slot: ScheduleSlot, post: Dict[str, Any]) -> str:
        """Estimate the reach of a post based on scheduling."""
        score = 0
        
        # Peak time bonus
        if slot.is_peak_time:
            score += 30
        
        # Day of week bonus
        day_bonuses = {
            "Tuesday": 25,
            "Thursday": 25,
            "Sunday": 20,
            "Wednesday": 15,
            "Saturday": 10
        }
        score += day_bonuses.get(slot.date.strftime("%A"), 0)
        
        # Time category bonus
        time_bonuses = {
            "morning": 20,
            "evening": 25,
            "midday": 15
        }
        score += time_bonuses.get(slot.time_category, 0)
        
        # Content type bonus
        if post.get("post_type") == "affirmation" and slot.time_category == "morning":
            score += 10
        elif post.get("post_type") == "wisdom" and slot.time_category == "evening":
            score += 10
        
        # Convert score to reach estimate
        if score >= 80:
            return "very_high"
        elif score >= 60:
            return "high"
        elif score >= 40:
            return "medium"
        else:
            return "low"
    
    def _generate_schedule_summary(self, schedule: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the schedule."""
        scheduled_posts = schedule["scheduled_posts"]
        
        summary = {
            "total_posts": len(scheduled_posts),
            "date_range": f"{schedule['start_date']} to {schedule['end_date']}",
            "posts_per_week": schedule["posts_per_week"],
            "distribution": {
                "by_day": {},
                "by_time": {},
                "by_type": {}
            },
            "peak_time_percentage": 0,
            "estimated_high_reach_posts": 0
        }
        
        # Analyze distribution
        for post in scheduled_posts:
            # By day
            day = post["day_of_week"]
            summary["distribution"]["by_day"][day] = summary["distribution"]["by_day"].get(day, 0) + 1
            
            # By time
            time_cat = post["time_category"]
            summary["distribution"]["by_time"][time_cat] = summary["distribution"]["by_time"].get(time_cat, 0) + 1
            
            # By type
            post_type = post["post"].get("post_type", "general")
            summary["distribution"]["by_type"][post_type] = summary["distribution"]["by_type"].get(post_type, 0) + 1
            
            # Peak time
            if post["is_peak_time"]:
                summary["peak_time_percentage"] += 1
            
            # High reach
            if post["expected_reach"] in ["high", "very_high"]:
                summary["estimated_high_reach_posts"] += 1
        
        # Calculate percentages
        if scheduled_posts:
            summary["peak_time_percentage"] = (summary["peak_time_percentage"] / len(scheduled_posts)) * 100
        
        return summary
    
    async def _update_scheduled_posts(self, schedule: Dict[str, Any]):
        """Update posts in database with schedule information."""
        try:
            for scheduled_post in schedule["scheduled_posts"]:
                post = scheduled_post["post"]
                if "id" in post:
                    await self.supabase.update_threads_post(
                        post["id"],
                        {
                            "status": "scheduled",
                            "scheduled_at": scheduled_post["scheduled_for"],
                            "updated_at": datetime.now().isoformat()
                        }
                    )
        except Exception as e:
            logger.error(f"Error updating scheduled posts: {str(e)}")
    
    def _save_schedule(self, schedule: Dict[str, Any]):
        """Save schedule to storage."""
        filename = f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)
        
        # Also save as latest
        latest_path = os.path.join(self.storage_dir, "latest_schedule.json")
        with open(latest_path, 'w') as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)
    
    async def publish_scheduled_posts(self) -> Dict[str, Any]:
        """Check for posts ready to publish and simulate publishing."""
        try:
            # Get scheduled posts from database
            scheduled_posts = await self.supabase.get_threads_posts(status="scheduled")
            
            published_count = 0
            current_time = datetime.now()
            
            for post in scheduled_posts:
                if post.scheduled_at and datetime.fromisoformat(post.scheduled_at) <= current_time:
                    # Simulate publishing to Threads
                    logger.info(f"Publishing post to Threads: {post.content[:50]}...")
                    
                    # Update status
                    await self.supabase.update_threads_post(
                        post.id,
                        {
                            "status": "published",
                            "published_at": current_time.isoformat()
                        }
                    )
                    
                    published_count += 1
            
            return {
                "success": True,
                "published_count": published_count,
                "message": f"Published {published_count} posts to Threads"
            }
            
        except Exception as e:
            logger.error(f"Error publishing scheduled posts: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_upcoming_posts(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get posts scheduled for the next N days."""
        latest_schedule = self.get_latest_schedule()
        
        if not latest_schedule:
            return []
        
        upcoming = []
        cutoff_date = datetime.now() + timedelta(days=days)
        
        for post in latest_schedule.get("scheduled_posts", []):
            scheduled_date = datetime.fromisoformat(post["scheduled_for"])
            if datetime.now() <= scheduled_date <= cutoff_date:
                upcoming.append(post)
        
        return upcoming
    
    def get_latest_schedule(self) -> Optional[Dict[str, Any]]:
        """Retrieve the latest schedule."""
        latest_path = os.path.join(self.storage_dir, "latest_schedule.json")
        
        if os.path.exists(latest_path):
            with open(latest_path, 'r') as f:
                return json.load(f)
        
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check agent health status."""
        upcoming = self.get_upcoming_posts(7)
        
        return {
            "status": "healthy",
            "agent": "SchedulerAgent",
            "storage_available": os.path.exists(self.storage_dir),
            "latest_schedule": self.get_latest_schedule() is not None,
            "upcoming_posts_7days": len(upcoming),
            "supabase_connected": self.supabase.client is not None
        }