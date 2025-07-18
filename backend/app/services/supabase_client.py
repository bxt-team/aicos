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
    id: Optional[str] = None  # UUID in database
    content: str
    hashtags: List[str] = []  # Changed from tags to hashtags
    media_urls: List[str] = []  # Added media_urls field
    thread_parent_id: Optional[str] = None  # For thread replies
    status: str = "draft"  # draft, approved, scheduled, published, needs_revision, rejected
    scheduled_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None  # Changed from published_at
    threads_post_id: Optional[str] = None  # External Threads ID
    created_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}  # JSONB field
    
    # Legacy fields kept for compatibility
    tags: Optional[List[str]] = None  # Maps to hashtags
    period: Optional[int] = None  # Can be stored in metadata
    visual_prompt: Optional[str] = None  # Can be stored in metadata
    approval_requested_at: Optional[datetime] = None  # Can be stored in metadata
    approved_by: Optional[str] = None  # Can be stored in metadata
    updated_at: Optional[datetime] = None  # Not in DB but kept for compatibility
    published_at: Optional[datetime] = None  # Maps to posted_at
    
    def __init__(self, **data):
        # Map legacy fields
        if 'tags' in data and 'hashtags' not in data:
            data['hashtags'] = data.get('tags', [])
        if 'published_at' in data and 'posted_at' not in data:
            data['posted_at'] = data.get('published_at')
        if 'hashtags' in data and 'tags' not in data:
            data['tags'] = data.get('hashtags', [])
        if 'posted_at' in data and 'published_at' not in data:
            data['published_at'] = data.get('posted_at')
            
        # Store extra fields in metadata
        metadata = data.get('metadata', {})
        if 'period' in data and data['period'] is not None:
            metadata['period'] = data['period']
        if 'visual_prompt' in data and data['visual_prompt'] is not None:
            metadata['visual_prompt'] = data['visual_prompt']
        if 'approval_requested_at' in data and data['approval_requested_at'] is not None:
            metadata['approval_requested_at'] = data['approval_requested_at'].isoformat() if isinstance(data['approval_requested_at'], datetime) else data['approval_requested_at']
        if 'approved_by' in data and data['approved_by'] is not None:
            metadata['approved_by'] = data['approved_by']
        if metadata:
            data['metadata'] = metadata
            
        super().__init__(**data)


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
            query = self.client.table("agent_threads_posts").select("*")
            
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
            post_dict["id"] = str(len(self._mock_data["threads_posts"]) + 1)
            post_dict["created_at"] = datetime.now()
            post_dict["updated_at"] = datetime.now()
            self._mock_data["threads_posts"].append(post_dict)
            return ThreadsPost(**post_dict)
        
        try:
            # Prepare data for database
            data = post.dict(exclude_none=True, exclude={"id", "created_at", "updated_at", "tags", "period", "visual_prompt", "approval_requested_at", "approved_by", "published_at"})
            
            # Map legacy fields
            if post.tags:
                data["hashtags"] = post.tags
            if post.published_at:
                data["posted_at"] = post.published_at
                
            # Store extra fields in metadata
            metadata = data.get("metadata", {})
            if post.period is not None:
                metadata["period"] = post.period
            if post.visual_prompt:
                metadata["visual_prompt"] = post.visual_prompt
            if post.approval_requested_at:
                metadata["approval_requested_at"] = post.approval_requested_at.isoformat()
            if post.approved_by:
                metadata["approved_by"] = post.approved_by
            if metadata:
                data["metadata"] = metadata
            
            response = self.client.table("agent_threads_posts").insert(data).execute()
            return ThreadsPost(**response.data[0])
        except Exception as e:
            logger.error(f"Error creating threads post: {str(e)}")
            raise
    
    async def update_threads_post(self, post_id: Any, updates: Dict[str, Any]) -> ThreadsPost:
        """Update a Threads post."""
        # post_id is already a string (UUID) in the database
        
        if not self.client:
            # Mock implementation
            for i, post in enumerate(self._mock_data["threads_posts"]):
                if post.get("id") == str(post_id):
                    post.update(updates)
                    post["updated_at"] = datetime.now()
                    return ThreadsPost(**post)
            raise ValueError(f"Post with id {post_id} not found")
        
        try:
            # Prepare updates for database
            db_updates = {}
            metadata_updates = {}
            
            for key, value in updates.items():
                if key == "tags":
                    db_updates["hashtags"] = value
                elif key == "published_at":
                    db_updates["posted_at"] = value
                elif key in ["period", "visual_prompt", "approval_requested_at", "approved_by"]:
                    # Store in metadata
                    metadata_updates[key] = value.isoformat() if isinstance(value, datetime) else value
                elif key not in ["updated_at"]:  # Skip fields not in DB
                    db_updates[key] = value
            
            # If we have metadata updates, fetch current metadata and merge
            if metadata_updates:
                current = await self.get_threads_posts()
                current_post = next((p for p in current if str(p.id) == str(post_id)), None)
                if current_post:
                    current_metadata = current_post.metadata or {}
                    current_metadata.update(metadata_updates)
                    db_updates["metadata"] = current_metadata
            
            response = self.client.table("agent_threads_posts").update(db_updates).eq("id", post_id).execute()
            return ThreadsPost(**response.data[0])
        except Exception as e:
            logger.error(f"Error updating threads post: {str(e)}")
            raise
    
    async def delete_threads_post(self, post_id: Any) -> bool:
        """Delete a Threads post."""
        # post_id is already a string (UUID) in the database
        
        if not self.client:
            # Mock implementation
            for i, post in enumerate(self._mock_data["threads_posts"]):
                if post.get("id") == str(post_id):
                    del self._mock_data["threads_posts"][i]
                    return True
            return False
        
        try:
            response = self.client.table("agent_threads_posts").delete().eq("id", post_id).execute()
            return len(response.data) > 0
        except Exception as e:
            logger.error(f"Error deleting threads post: {str(e)}")
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