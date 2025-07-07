import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests
from io import BytesIO
from src.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM
from src.agents.image_search_agent import ImageSearchAgent

class VisualPostCreatorAgent(BaseCrew):
    """Agent for finding and generating background images for visual posts"""
    
    def __init__(self, openai_api_key: str, pexels_api_key: str = None):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.pexels_api_key = pexels_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize image search agent
        self.image_search_agent = ImageSearchAgent(openai_api_key, pexels_api_key)
        
        # Storage for created posts
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/visual_posts_storage.json")
        self.posts_storage = self._load_posts_storage()
        
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
        
        # Instagram dimensions
        self.story_width = 1080
        self.story_height = 1920
        
        # Instagram Post dimensions (4:5 aspect ratio)
        self.post_width = 1080
        self.post_height = 1350
        
    def _load_posts_storage(self) -> Dict[str, Any]:
        """Load previously created posts"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading posts storage: {e}")
        return {"posts": [], "by_period": {}}
    
    def _save_posts_storage(self):
        """Save created posts to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.posts_storage, f, indent=2)
        except Exception as e:
            print(f"Error saving posts storage: {e}")
    
    def _generate_post_hash(self, text: str, period: str, tags: List[str]) -> str:
        """Generate a hash for the post parameters"""
        post_key = f"{text}_{period}_{','.join(sorted(tags))}"
        return hashlib.md5(post_key.encode()).hexdigest()
    
    def find_background_image(self, tags: List[str], period: str, image_style: str = "minimal", 
                             count: int = 3, force_new: bool = False) -> Dict[str, Any]:
        """Find and prepare background images for visual posts"""
        try:
            # Check if images already exist in cache
            search_hash = self._generate_post_hash("", period, tags)
            
            if not force_new and search_hash in self.posts_storage.get("by_period", {}):
                existing_images = self.posts_storage["by_period"][search_hash]
                return {
                    "success": True,
                    "images": existing_images,
                    "source": "existing",
                    "message": "Bestehende Hintergrundbilder abgerufen"
                }
            
            # Search for background images
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
                    processed_images.append({
                        "id": image["id"],
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
                    })
            
            if not processed_images:
                return {
                    "success": False,
                    "error": "Failed to process any images",
                    "message": "Fehler beim Verarbeiten der Bilder"
                }
            
            # Store image information
            image_info = {
                "search_hash": search_hash,
                "period": period,
                "tags": tags,
                "image_style": image_style,
                "images": processed_images,
                "created_at": datetime.now().isoformat(),
                "search_query": image_search_result.get("search_query", "")
            }
            
            # Save to storage
            self.posts_storage["by_period"][search_hash] = image_info
            self._save_posts_storage()
            
            return {
                "success": True,
                "images": processed_images,
                "search_info": image_info,
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
        """Resize image to Instagram Post format (4:5 ratio - 1080x1350)"""
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
    
    def get_period_color(self, period: str) -> str:
        """Get period-specific color"""
        return self.period_colors.get(period, "#808080")
    
    def get_images_by_period(self, period: str = None) -> Dict[str, Any]:
        """Get all background images, optionally filtered by period"""
        try:
            if period:
                filtered_images = {
                    k: v for k, v in self.posts_storage.get("by_period", {}).items()
                    if v.get("period") == period
                }
            else:
                filtered_images = self.posts_storage.get("by_period", {})
            
            return {
                "success": True,
                "images": filtered_images,
                "count": len(filtered_images),
                "period": period
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Abrufen der Hintergrundbilder"
            }
    
    def delete_image_set(self, search_hash: str) -> Dict[str, Any]:
        """Delete a set of background images"""
        try:
            # Find and remove from storage
            if search_hash not in self.posts_storage.get("by_period", {}):
                return {
                    "success": False,
                    "error": "Image set not found",
                    "message": "Bildset nicht gefunden"
                }
            
            image_set = self.posts_storage["by_period"][search_hash]
            
            # Delete all image files
            for image in image_set.get("images", []):
                if os.path.exists(image["local_path"]):
                    os.remove(image["local_path"])
            
            # Remove from storage
            del self.posts_storage["by_period"][search_hash]
            
            # Save updated storage
            self._save_posts_storage()
            
            return {
                "success": True,
                "message": "Bildset erfolgreich gelöscht"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Löschen des Bildsets"
            }