import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM
from app.agents.image_search_agent import ImageSearchAgent
from app.core.storage import StorageFactory
import asyncio

class VisualPostCreatorAgent(BaseCrew):
    """Agent for finding and generating background images for visual posts"""
    
    def __init__(self, openai_api_key: str, pexels_api_key: str = None):
        # Get storage adapter from factory for multi-tenant support
        storage_adapter = StorageFactory.get_adapter()
        super().__init__(storage_adapter=storage_adapter)
        
        self.openai_api_key = openai_api_key
        self.pexels_api_key = pexels_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize image search agent
        self.image_search_agent = ImageSearchAgent(openai_api_key, pexels_api_key)
        
        # Collection name for visual posts
        self.collection = "visual_posts"
        
        # Output directory for created images
        self.output_dir = os.path.join(os.path.dirname(__file__), "../../static/visuals")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create the visual post creator agent
        self.creator_agent = self.create_agent("visual_post_creator_agent", llm=self.llm)
        
        # 7 Cycles period colors with transparency
        self.period_colors = {
            "Image": "#DAA520",        # Gold
            "Veränderung": "#2196F3",  # Blue
            "Energie": "#F44336",      # Red
            "Kreativität": "#FFD700",  # Yellow
            "Erfolg": "#CC0066",       # Magenta
            "Entspannung": "#4CAF50",  # Green
            "Umsicht": "#9C27B0"       # Purple
        }
        
        # Period to number mapping
        self.period_numbers = {
            "Image": 1,
            "Veränderung": 2,
            "Energie": 3,
            "Kreativität": 4,
            "Erfolg": 5,
            "Entspannung": 6,
            "Umsicht": 7
        }
        
        # Instagram dimensions
        self.story_width = 1080
        self.story_height = 1920
        
        # Instagram Post dimensions (4:5 aspect ratio)
        self.post_width = 1080
        self.post_height = 1350
    
    def _run_async(self, coro):
        """Helper to run async code in sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
    
    def _generate_post_hash(self, text: str, period: str, tags: List[str]) -> str:
        """Generate a hash for the post parameters"""
        post_key = f"{text}_{period}_{','.join(sorted(tags))}"
        return hashlib.md5(post_key.encode()).hexdigest()
    
    def find_background_image(self, tags: List[str], period: str, image_style: str = "minimal", 
                             count: int = 3, force_new: bool = False) -> Dict[str, Any]:
        """Find and prepare background images for visual posts"""
        try:
            # Consume credits for this action
            if self.validate_context():
                self._run_async(self.consume_credits_for_action(
                    action='create_visual_post',
                    metadata={
                        'tags': tags,
                        'period': period,
                        'style': image_style,
                        'count': count
                    }
                ))
            
            # Propagate context to image search agent if needed
            if self.validate_context() and hasattr(self.image_search_agent, 'set_context'):
                self.image_search_agent.set_context(self._context)
            # Check if images already exist in storage
            search_hash = self._generate_post_hash("", period, tags)
            period_number = self.period_numbers.get(period, 1)
            
            if not force_new:
                # Look for existing posts with similar tags
                if self.validate_context():
                    existing_posts = self._run_async(
                        self.list_results(
                            self.collection,
                            filters={"period": period_number},
                            limit=count
                        )
                    )
                else:
                    existing_posts = self._run_async(
                        self.storage_adapter.list(
                            self.collection,
                            filters={"period": period_number},
                            limit=count
                        )
                    )
                
                # Filter by matching tags
                matching_posts = []
                for post in existing_posts:
                    post_tags = post.get("metadata", {}).get("tags", [])
                    if any(tag in post_tags for tag in tags):
                        matching_posts.append(post)
                
                if matching_posts:
                    # Transform to expected format
                    images = []
                    for post in matching_posts[:count]:
                        images.append({
                            "id": post.get("id"),
                            "local_path": post.get("image_path"),
                            "original_url": post.get("image_url"),
                            "thumbnail_url": post.get("metadata", {}).get("thumbnail_url"),
                            "photographer": post.get("metadata", {}).get("photographer"),
                            "pexels_url": post.get("metadata", {}).get("pexels_url"),
                            "dimensions": post.get("metadata", {}).get("dimensions", {}),
                            "avg_color": post.get("metadata", {}).get("avg_color", "#CCCCCC"),
                            "processed_at": post.get("created_at")
                        })
                    
                    return {
                        "success": True,
                        "images": images,
                        "source": "existing",
                        "message": "Bestehende Hintergrundbilder abgerufen"
                    }
            
            # Search for new background images
            image_search_result = self.image_search_agent.search_images(tags, period, count=count)
            
            if not image_search_result["success"] or not image_search_result["images"]:
                return {
                    "success": False,
                    "error": "No suitable background images found",
                    "message": "Keine passenden Hintergrundbilder gefunden"
                }
            
            # Process and prepare all images
            processed_images = []
            for i, image in enumerate(image_search_result["images"]):
                image_hash = f"{search_hash}_{i}"
                
                # Download and prepare the image
                background_result = self._download_and_process_image(image, image_hash)
                
                if background_result["success"]:
                    # Save to storage
                    visual_post_data = {
                        "post_type": "background",
                        "image_url": image["url"],
                        "image_path": background_result["image_path"],
                        "text_content": "",  # No text for background images
                        "period": period_number,
                        "theme": period,
                        "metadata": {
                            "tags": tags,
                            "image_style": image_style,
                            "search_hash": search_hash,
                            "photographer": image["photographer"],
                            "pexels_url": image["pexels_url"],
                            "thumbnail_url": image["thumbnail_url"],
                            "dimensions": {
                                "width": image["width"],
                                "height": image["height"]
                            },
                            "avg_color": image.get("avg_color", "#CCCCCC"),
                            "pexels_id": image["id"]
                        }
                    }
                    
                    # Save to storage with multi-tenant support
                    if self.validate_context():
                        post_id = self._run_async(
                            self.save_result(self.collection, visual_post_data)
                        )
                    else:
                        post_id = self._run_async(
                            self.storage_adapter.save(self.collection, visual_post_data)
                        )
                    
                    processed_image_info = {
                        "id": post_id,
                        "local_path": background_result["image_path"],
                        "original_url": image["url"],
                        "thumbnail_url": image["thumbnail_url"],
                        "photographer": image["photographer"],
                        "pexels_url": image["pexels_url"],
                        "dimensions": {
                            "width": image["width"],
                            "height": image["height"]
                        },
                        "avg_color": image.get("avg_color", "#CCCCCC"),
                        "processed_at": datetime.now().isoformat()
                    }
                    
                    processed_images.append(processed_image_info)
            
            if not processed_images:
                return {
                    "success": False,
                    "error": "Failed to process any images",
                    "message": "Fehler beim Verarbeiten der Bilder"
                }
            
            return {
                "success": True,
                "images": processed_images,
                "search_info": {
                    "search_hash": search_hash,
                    "period": period,
                    "tags": tags,
                    "image_style": image_style,
                    "created_at": datetime.now().isoformat(),
                    "search_query": image_search_result.get("search_query", "")
                },
                "source": "generated",
                "message": f"Hintergrundbilder für {period} gefunden"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Finden der Hintergrundbilder"
            }
    
    def _download_and_process_image(self, image_info: Dict[str, Any], post_hash: str) -> Dict[str, Any]:
        """Download and prepare background image"""
        try:
            # Create temporary path for background image
            temp_path = os.path.join(self.output_dir, f"temp_{post_hash}.jpg")
            
            # Download image
            download_result = self.image_search_agent.download_image(image_info, temp_path)
            
            if not download_result["success"]:
                return download_result
            
            return {
                "success": True,
                "image_path": temp_path,
                "image_info": image_info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Herunterladen des Hintergrundbildes"
            }
    
    def prepare_background_for_format(self, background_path: str, post_format: str = "story") -> Dict[str, Any]:
        """Prepare background image for specific Instagram format"""
        try:
            # Load background image
            background = Image.open(background_path)
            
            # Resize to appropriate Instagram format
            if post_format == "post":
                processed_background = self._resize_to_post_format(background)
            else:
                processed_background = self._resize_to_story_format(background)
            
            # Save processed image
            base_name = os.path.splitext(os.path.basename(background_path))[0]
            format_suffix = "post" if post_format == "post" else "story"
            output_filename = f"{base_name}_{format_suffix}_processed.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Convert to RGB for JPEG
            processed_background = processed_background.convert('RGB')
            processed_background.save(output_path, 'JPEG', quality=95)
            
            # Create URL for frontend access
            output_url = f"/static/visuals/{output_filename}"
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": output_url,
                "filename": output_filename,
                "dimensions": {
                    "width": processed_background.width,
                    "height": processed_background.height
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Verarbeiten des Hintergrundbildes"
            }
    
    def _resize_to_story_format(self, image: Image.Image) -> Image.Image:
        """Resize image to Instagram Story format (1080x1920)"""
        # Calculate aspect ratios
        img_ratio = image.width / image.height
        story_ratio = self.story_width / self.story_height
        
        if img_ratio > story_ratio:
            # Image is wider than story format - crop width
            new_height = self.story_height
            new_width = int(new_height * img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop
            left = (new_width - self.story_width) // 2
            image = image.crop((left, 0, left + self.story_width, self.story_height))
        else:
            # Image is taller than story format - crop height
            new_width = self.story_width
            new_height = int(new_width / img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop
            top = (new_height - self.story_height) // 2
            image = image.crop((0, top, self.story_width, top + self.story_height))
        
        return image
    
    def _resize_to_post_format(self, image: Image.Image) -> Image.Image:
        """Resize image to Instagram Post format (1080x1350)"""
        # Calculate aspect ratios
        img_ratio = image.width / image.height
        post_ratio = self.post_width / self.post_height
        
        if img_ratio > post_ratio:
            # Image is wider than post format - crop width
            new_height = self.post_height
            new_width = int(new_height * img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop
            left = (new_width - self.post_width) // 2
            image = image.crop((left, 0, left + self.post_width, self.post_height))
        else:
            # Image is taller than post format - crop height
            new_width = self.post_width
            new_height = int(new_width / img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop
            top = (new_height - self.post_height) // 2
            image = image.crop((0, top, self.post_width, top + self.post_height))
        
        return image
    
    def get_visual_posts_by_period(self, period: str = None) -> Dict[str, Any]:
        """Get all visual posts, optionally filtered by period"""
        try:
            filters = None
            if period:
                period_number = self.period_numbers.get(period)
                if period_number:
                    filters = {"period": period_number}
            
            # Get posts with multi-tenant support
            if self.validate_context():
                posts = self._run_async(
                    self.list_results(
                        self.collection,
                        filters=filters,
                        order_by="created_at",
                        order_desc=True
                    )
                )
            else:
                posts = self._run_async(
                    self.storage_adapter.list(
                        self.collection,
                        filters=filters,
                        order_by="created_at",
                        order_desc=True
                    )
                )
            
            # Transform to expected format
            formatted_posts = []
            for post in posts:
                formatted_post = {
                    "id": post.get("id"),
                    "post_type": post.get("post_type"),
                    "image_url": post.get("image_url"),
                    "image_path": post.get("image_path"),
                    "text_content": post.get("text_content"),
                    "period": post.get("period"),
                    "theme": post.get("theme"),
                    "created_at": post.get("created_at")
                }
                
                # Add metadata fields
                if "metadata" in post:
                    formatted_post.update(post["metadata"])
                
                formatted_posts.append(formatted_post)
            
            return {
                "success": True,
                "posts": formatted_posts,
                "count": len(formatted_posts),
                "period": period
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error retrieving visual posts"
            }
    
    # Backward compatibility methods
    def _load_posts_storage(self) -> Dict[str, Any]:
        """Legacy method - now uses storage adapter"""
        if self.validate_context():
            posts = self._run_async(
                self.list_results(self.collection)
            )
        else:
            posts = self._run_async(
                self.storage_adapter.list(self.collection)
            )
        
        # Convert to legacy format
        by_period = {}
        for post in posts:
            if "metadata" in post and "search_hash" in post["metadata"]:
                search_hash = post["metadata"]["search_hash"]
                if search_hash not in by_period:
                    by_period[search_hash] = {
                        "search_hash": search_hash,
                        "period": post.get("theme"),
                        "tags": post["metadata"].get("tags", []),
                        "images": []
                    }
                by_period[search_hash]["images"].append(post)
        
        return {"posts": posts, "by_period": by_period}
    
    def _save_posts_storage(self):
        """Legacy method - no longer needed with storage adapter"""
        pass  # Storage adapter handles persistence automatically