import os
import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM
from app.core.storage import StorageFactory
import asyncio

class ImageSearchAgent(BaseCrew):
    """Agent for searching and retrieving background images from Pexels API"""
    
    def __init__(self, openai_api_key: str, pexels_api_key: str = None):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.pexels_api_key = pexels_api_key or os.getenv('PEXELS_API_KEY')
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize storage adapter for caching
        self.storage = StorageFactory.get_adapter()
        self.collection = "generic_storage"  # Use generic storage for image cache
        
        # Legacy file cache for backward compatibility
        self.cache_file = os.path.join(os.path.dirname(__file__), "../../static/image_cache.json")
        
        # Create the image search agent
        self.search_agent = self.create_agent("image_search_agent", llm=self.llm)
        
        # Pexels API base URL
        self.pexels_api_base = "https://api.pexels.com/v1"
        
    async def _get_cached_search(self, search_hash: str) -> Optional[Dict[str, Any]]:
        """Get cached search results from Supabase"""
        try:
            results = await self.storage.list(
                self.collection,
                filters={
                    "storage_type": "image_search_cache",
                    "storage_key": f"image_search_{search_hash}"
                },
                limit=1
            )
            
            if results and len(results) > 0:
                cached_data = results[0].get("data", {})
                # Check if cache is still valid (24 hours)
                cache_time = datetime.fromisoformat(cached_data.get("cached_at", ""))
                if (datetime.now() - cache_time).total_seconds() < 86400:  # 24 hours
                    return cached_data
            return None
        except Exception as e:
            print(f"Error getting cached search: {e}")
            return None
    
    async def _save_search_cache(self, search_hash: str, cache_data: Dict[str, Any]) -> str:
        """Save search results to Supabase cache"""
        try:
            storage_data = {
                "storage_key": f"image_search_{search_hash}",
                "storage_type": "image_search_cache",
                "data": cache_data
            }
            
            # Save to storage
            cache_id = await self.storage.save(self.collection, storage_data)
            return cache_id
        except Exception as e:
            print(f"Error saving search cache: {e}")
            return ""
    
    def _generate_search_hash(self, tags: List[str], period: str) -> str:
        """Generate a hash for search parameters to check cache"""
        search_key = f"{period}_{','.join(sorted(tags))}"
        return hashlib.md5(search_key.encode()).hexdigest()
    
    def search_images(self, tags: List[str], period: str, count: int = 5) -> Dict[str, Any]:
        """Search for images based on tags and period"""
        try:
            # Check cache first
            search_hash = self._generate_search_hash(tags, period)
            
            # Try to get from Supabase cache
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                cached_result = loop.run_until_complete(
                    self._get_cached_search(search_hash)
                )
                
                if cached_result:
                    return {
                        "success": True,
                        "images": cached_result["images"],
                        "source": "cache",
                        "search_hash": search_hash
                    }
            finally:
                loop.close()
            
            if not self.pexels_api_key:
                return {
                    "success": False,
                    "error": "Pexels API key not configured",
                    "message": "Pexels API Schlüssel fehlt"
                }
            
            # Prepare search query
            search_query = self._prepare_search_query(tags, period)
            
            # Search Pexels
            headers = {
                "Authorization": self.pexels_api_key
            }
            
            params = {
                "query": search_query,
                "per_page": count,
                "orientation": "portrait",  # Better for Instagram Stories
                "size": "large"
            }
            
            response = requests.get(
                f"{self.pexels_api_base}/search",
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Pexels API error: {response.status_code}",
                    "message": "Fehler beim Abrufen der Bilder"
                }
            
            data = response.json()
            images = []
            
            for photo in data.get("photos", []):
                # Get the best quality image for processing
                image_url = photo["src"]["large"]  # Good quality for processing
                if photo["width"] >= 1080:  # Prefer high resolution
                    image_url = photo["src"]["original"]
                
                image_info = {
                    "id": str(photo["id"]),
                    "url": image_url,
                    "download_url": photo["src"]["original"],  # Highest quality
                    "thumbnail_url": photo["src"]["medium"],
                    "width": photo["width"],
                    "height": photo["height"],
                    "alt_description": photo.get("alt", "Beautiful image"),
                    "description": f"High-quality image for {period} period",
                    "photographer": photo["photographer"],
                    "photographer_url": photo["photographer_url"],
                    "pexels_url": photo["url"],
                    "avg_color": photo.get("avg_color", "#CCCCCC")
                }
                images.append(image_info)
            
            # Cache the results in Supabase
            cache_entry = {
                "images": images,
                "cached_at": datetime.now().isoformat(),
                "search_query": search_query,
                "tags": tags,
                "period": period
            }
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    self._save_search_cache(search_hash, cache_entry)
                )
            finally:
                loop.close()
            
            return {
                "success": True,
                "images": images,
                "source": "pexels",
                "search_hash": search_hash,
                "search_query": search_query
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler bei der Bildsuche"
            }
    
    def _prepare_search_query(self, tags: List[str], period: str) -> str:
        """Prepare search query based on tags and period"""
        # Period-specific enhancements optimized for Pexels
        period_keywords = {
            "Image": ["portrait", "mirror", "reflection", "confidence", "self", "beautiful person"],
            "Veränderung": ["transformation", "butterfly", "sunrise", "growth", "new beginning", "change"],
            "Energie": ["energy", "lightning", "fire", "power", "dynamic", "vibrant", "active"],
            "Kreativität": ["creative", "colorful", "art", "paint", "inspiration", "artistic"],
            "Erfolg": ["success", "mountain peak", "achievement", "victory", "goal", "winner"],
            "Entspannung": ["peaceful", "calm", "meditation", "zen", "nature", "tranquil"],
            "Umsicht": ["wisdom", "thoughtful", "planning", "strategy", "contemplation", "mindful"]
        }
        
        # Combine tags with period-specific keywords
        base_tags = tags[:3]  # Limit to 3 main tags
        period_tags = period_keywords.get(period, [])[:2]  # Add 2 period-specific tags
        
        # Create search query
        all_tags = base_tags + period_tags
        search_query = " ".join(all_tags)
        
        return search_query
    
    def download_image(self, image_info: Dict[str, Any], local_path: str) -> Dict[str, Any]:
        """Download an image to local storage"""
        try:
            # Download the image directly from Pexels (no tracking required)
            response = requests.get(image_info["url"], timeout=30)
            
            if response.status_code == 200:
                # Ensure directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Save the image
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                
                return {
                    "success": True,
                    "local_path": local_path,
                    "size": len(response.content),
                    "image_info": image_info
                }
            else:
                return {
                    "success": False,
                    "error": f"Download failed: {response.status_code}",
                    "message": "Fehler beim Herunterladen des Bildes"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Herunterladen des Bildes"
            }
    
    def get_cached_searches(self) -> Dict[str, Any]:
        """Get all cached search results"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                cached_searches = loop.run_until_complete(
                    self.storage.list(
                        self.collection,
                        filters={"storage_type": "image_search_cache"},
                        order_by="created_at",
                        order_desc=True
                    )
                )
                
                # Extract the cache data
                searches = {}
                for item in cached_searches:
                    key = item.get("storage_key", "").replace("image_search_", "")
                    if key:
                        searches[key] = item.get("data", {})
                
                return {
                    "success": True,
                    "cached_searches": searches
                }
            finally:
                loop.close()
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "cached_searches": {}
            }
    
    def clear_cache(self) -> Dict[str, Any]:
        """Clear the image cache"""
        try:
            # Note: We can't delete from Supabase through the storage adapter
            # This would need to be implemented in the storage adapter
            # For now, cache entries will expire after 24 hours
            return {
                "success": True,
                "message": "Cache entries will expire after 24 hours",
                "note": "Manual cache clearing not yet implemented for Supabase storage"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Leeren des Caches"
            }