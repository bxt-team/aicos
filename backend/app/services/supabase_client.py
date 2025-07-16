"""Supabase client for database operations."""

import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class Activity(BaseModel):
    """Model for activities stored in Supabase."""
    id: Optional[int] = None
    title: str
    description: str
    period: int  # 1-7 representing the 7 cycles
    tags: List[str]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ThreadsPost(BaseModel):
    """Model for Threads posts stored in Supabase."""
    id: Optional[int] = None
    content: str
    tags: List[str]
    period: int
    visual_prompt: Optional[str] = None
    status: str = "draft"  # draft, approved, scheduled, published
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    approval_requested_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SupabaseClient:
    """Client for interacting with Supabase database."""
    
    def __init__(self, url: Optional[str] = None, key: Optional[str] = None):
        """Initialize Supabase client."""
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_ANON_KEY")
        
        if not self.url or not self.key:
            logger.warning("Supabase credentials not found. Running in mock mode.")
            self.client = None
            self._mock_data = {
                "activities": [],
                "threads_posts": []
            }
        else:
            self.client: Client = create_client(self.url, self.key)
    
    async def get_activities(self, period: Optional[int] = None, tags: Optional[List[str]] = None) -> List[Activity]:
        """Get activities filtered by period and/or tags."""
        if not self.client:
            # Mock implementation
            activities = self._mock_data["activities"]
            if period:
                activities = [a for a in activities if a.get("period") == period]
            if tags:
                activities = [a for a in activities if any(tag in a.get("tags", []) for tag in tags)]
            return [Activity(**a) for a in activities]
        
        try:
            query = self.client.table("activities").select("*")
            
            if period:
                query = query.eq("period", period)
            
            if tags:
                # PostgreSQL array contains any of the tags
                query = query.contains("tags", tags)
            
            response = query.execute()
            return [Activity(**item) for item in response.data]
        except Exception as e:
            logger.error(f"Error fetching activities: {str(e)}")
            return []
    
    async def create_activity(self, activity: Activity) -> Activity:
        """Create a new activity."""
        if not self.client:
            # Mock implementation
            activity_dict = activity.dict(exclude_none=True)
            activity_dict["id"] = len(self._mock_data["activities"]) + 1
            activity_dict["created_at"] = datetime.now()
            activity_dict["updated_at"] = datetime.now()
            self._mock_data["activities"].append(activity_dict)
            return Activity(**activity_dict)
        
        try:
            data = activity.dict(exclude_none=True, exclude={"id", "created_at", "updated_at"})
            response = self.client.table("activities").insert(data).execute()
            return Activity(**response.data[0])
        except Exception as e:
            logger.error(f"Error creating activity: {str(e)}")
            raise
    
    async def get_threads_posts(self, status: Optional[str] = None, limit: int = 50) -> List[ThreadsPost]:
        """Get Threads posts filtered by status."""
        if not self.client:
            # Mock implementation
            posts = self._mock_data["threads_posts"]
            if status:
                posts = [p for p in posts if p.get("status") == status]
            return [ThreadsPost(**p) for p in posts[:limit]]
        
        try:
            query = self.client.table("threads_posts").select("*")
            
            if status:
                query = query.eq("status", status)
            
            query = query.limit(limit).order("created_at", desc=True)
            
            response = query.execute()
            return [ThreadsPost(**item) for item in response.data]
        except Exception as e:
            logger.error(f"Error fetching threads posts: {str(e)}")
            return []
    
    async def create_threads_post(self, post: ThreadsPost) -> ThreadsPost:
        """Create a new Threads post."""
        if not self.client:
            # Mock implementation
            post_dict = post.dict(exclude_none=True)
            post_dict["id"] = len(self._mock_data["threads_posts"]) + 1
            post_dict["created_at"] = datetime.now()
            post_dict["updated_at"] = datetime.now()
            self._mock_data["threads_posts"].append(post_dict)
            return ThreadsPost(**post_dict)
        
        try:
            data = post.dict(exclude_none=True, exclude={"id", "created_at", "updated_at"})
            response = self.client.table("threads_posts").insert(data).execute()
            return ThreadsPost(**response.data[0])
        except Exception as e:
            logger.error(f"Error creating threads post: {str(e)}")
            raise
    
    async def update_threads_post(self, post_id: int, updates: Dict[str, Any]) -> ThreadsPost:
        """Update a Threads post."""
        if not self.client:
            # Mock implementation
            for i, post in enumerate(self._mock_data["threads_posts"]):
                if post.get("id") == post_id:
                    post.update(updates)
                    post["updated_at"] = datetime.now()
                    return ThreadsPost(**post)
            raise ValueError(f"Post with id {post_id} not found")
        
        try:
            response = self.client.table("threads_posts").update(updates).eq("id", post_id).execute()
            return ThreadsPost(**response.data[0])
        except Exception as e:
            logger.error(f"Error updating threads post: {str(e)}")
            raise
    
    # Mock data initialization for testing
    def add_mock_activities(self):
        """Add sample activities for testing."""
        if not self.client:
            self._mock_data["activities"] = [
                {
                    "id": 1,
                    "title": "Meditation Practice",
                    "description": "Daily meditation to connect with inner wisdom",
                    "period": 1,
                    "tags": ["mindfulness", "spirituality", "healing"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                {
                    "id": 2,
                    "title": "Creative Expression Workshop",
                    "description": "Explore your creativity through art and movement",
                    "period": 3,
                    "tags": ["creativity", "self-expression", "workshop"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                {
                    "id": 3,
                    "title": "Community Circle",
                    "description": "Connect with like-minded souls in sacred space",
                    "period": 5,
                    "tags": ["community", "connection", "support"],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
            ]


# Convenience functions for backward compatibility
import asyncio

def get_all_activities() -> List[Dict[str, Any]]:
    """Get all activities from the database (synchronous wrapper)."""
    client = SupabaseClient()
    if not client.client:
        # Return mock data
        client.add_mock_activities()
        return client._mock_data["activities"]
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        activities = loop.run_until_complete(client.get_activities())
        return [activity.dict() for activity in activities]
    finally:
        loop.close()


def get_activities_by_period(period: int) -> List[Dict[str, Any]]:
    """Get activities for a specific period (synchronous wrapper)."""
    client = SupabaseClient()
    if not client.client:
        # Return mock data
        client.add_mock_activities()
        return [a for a in client._mock_data["activities"] if a.get("period") == period]
    
    # Run async function in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        activities = loop.run_until_complete(client.get_activities(period=period))
        return [activity.dict() for activity in activities]
    finally:
        loop.close()


# Global instance for backward compatibility
supabase = SupabaseClient()