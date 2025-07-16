"""Example of integrating storage layer with existing agents"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.storage import StorageFactory, StorageAdapter


class AffirmationAgentWithStorage:
    """Example of how to update the Affirmation Agent to use the storage layer"""
    
    def __init__(self):
        # Get storage adapter from factory
        self.storage: StorageAdapter = StorageFactory.get_adapter()
        self.collection = "affirmations"
    
    async def save_affirmation(self, 
                              theme: str,
                              period: int,
                              affirmation: str,
                              language: str = "de") -> str:
        """Save a new affirmation"""
        data = {
            "theme": theme,
            "period": period,
            "affirmation": affirmation,
            "language": language
        }
        
        # Save using storage adapter
        affirmation_id = await self.storage.save(self.collection, data)
        print(f"Saved affirmation with ID: {affirmation_id}")
        return affirmation_id
    
    async def get_affirmations_by_period(self, period: int) -> List[Dict[str, Any]]:
        """Get all affirmations for a specific period"""
        return await self.storage.list(
            self.collection,
            filters={"period": period},
            order_by="created_at",
            order_desc=True
        )
    
    async def get_affirmations_by_theme(self, theme: str) -> List[Dict[str, Any]]:
        """Get all affirmations for a specific theme"""
        return await self.storage.list(
            self.collection,
            filters={"theme": theme}
        )
    
    async def update_affirmation(self, affirmation_id: str, new_text: str) -> bool:
        """Update affirmation text"""
        return await self.storage.update(
            self.collection,
            affirmation_id,
            {"affirmation": new_text}
        )
    
    async def delete_affirmation(self, affirmation_id: str) -> bool:
        """Delete an affirmation"""
        return await self.storage.delete(self.collection, affirmation_id)
    
    async def get_affirmation_count(self, period: Optional[int] = None) -> int:
        """Get total count of affirmations"""
        filters = {"period": period} if period else None
        return await self.storage.count(self.collection, filters)


class InstagramAgentWithStorage:
    """Example of how to update the Instagram Agent to use the storage layer"""
    
    def __init__(self):
        self.storage: StorageAdapter = StorageFactory.get_adapter()
    
    async def save_post(self, content: str, hashtags: List[str], post_type: str = "feed") -> str:
        """Save a new Instagram post"""
        data = {
            "content": content,
            "hashtags": hashtags,
            "post_type": post_type,
            "status": "draft"
        }
        
        return await self.storage.save("instagram_posts", data)
    
    async def get_posts_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get posts by status (draft, scheduled, posted, failed)"""
        return await self.storage.list(
            "instagram_posts",
            filters={"status": status},
            order_by="created_at",
            order_desc=True
        )
    
    async def mark_post_as_posted(self, post_id: str, instagram_id: str) -> bool:
        """Update post status after successful posting"""
        return await self.storage.update(
            "instagram_posts",
            post_id,
            {
                "status": "posted",
                "posted_at": datetime.now().isoformat(),
                "instagram_post_id": instagram_id
            }
        )
    
    async def save_analysis(self, username: str, analysis_data: Dict[str, Any]) -> str:
        """Save Instagram account analysis"""
        data = {
            "account_username": username,
            "analysis_type": "profile",
            "analysis_data": analysis_data,
            "recommendations": self._generate_recommendations(analysis_data)
        }
        
        return await self.storage.save("instagram_analyses", data)
    
    def _generate_recommendations(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate recommendations based on analysis"""
        # Placeholder for recommendation logic
        return {
            "posting_times": ["9:00", "18:00"],
            "content_types": ["carousel", "reels"],
            "hashtag_suggestions": ["#7cycles", "#mindfulness"]
        }


# Example usage patterns for migration
async def example_usage():
    """Show how to use the storage layer in practice"""
    
    # 1. Using with environment-based configuration
    # Set STORAGE_ADAPTER=json for JSON storage
    # Set STORAGE_ADAPTER=supabase for Supabase storage
    
    affirmation_agent = AffirmationAgentWithStorage()
    
    # Save affirmations
    aff_id = await affirmation_agent.save_affirmation(
        theme="Selbstvertrauen",
        period=2,
        affirmation="Ich vertraue meinen Fähigkeiten und meiner Intuition."
    )
    
    # Get affirmations for period 2
    period_2_affirmations = await affirmation_agent.get_affirmations_by_period(2)
    print(f"Found {len(period_2_affirmations)} affirmations for period 2")
    
    # 2. Using dual-write mode during migration
    from app.core.storage.migration import DualWriteAdapter
    from app.core.storage import JSONAdapter, SupabaseAdapter
    
    # Create dual-write adapter
    dual_adapter = DualWriteAdapter(
        primary=JSONAdapter(),
        secondary=SupabaseAdapter(
            url="your-supabase-url",
            key="your-supabase-key"
        ),
        read_from_primary=True  # Still read from JSON
    )
    
    # Replace the factory adapter temporarily
    StorageFactory._instance = dual_adapter
    
    # Now all agents will write to both JSON and Supabase
    # but still read from JSON for safety
    
    # 3. Gradual migration pattern
    # Step 1: Deploy with dual-write enabled
    # Step 2: Verify data integrity in Supabase
    # Step 3: Switch read_from_primary to False (read from Supabase)
    # Step 4: Monitor for issues
    # Step 5: Remove dual-write and use Supabase only


if __name__ == "__main__":
    asyncio.run(example_usage())