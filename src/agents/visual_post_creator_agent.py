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
    """Agent for creating visual affirmation posts with background images and text overlays"""
    
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
        
        # Instagram Story dimensions
        self.story_width = 1080
        self.story_height = 1920
        
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
    
    def create_visual_post(self, text: str, period: str, tags: List[str], 
                          image_style: str = "minimal", force_new: bool = False) -> Dict[str, Any]:
        """Create a visual affirmation post"""
        try:
            # Check if post already exists
            post_hash = self._generate_post_hash(text, period, tags)
            
            if not force_new and post_hash in self.posts_storage.get("by_period", {}):
                existing_post = self.posts_storage["by_period"][post_hash]
                if os.path.exists(existing_post["file_path"]):
                    return {
                        "success": True,
                        "post": existing_post,
                        "source": "existing",
                        "message": "Bestehender visueller Post abgerufen"
                    }
            
            # Search for background image
            image_search_result = self.image_search_agent.search_images(tags, period, count=3)
            
            if not image_search_result["success"] or not image_search_result["images"]:
                return {
                    "success": False,
                    "error": "No suitable background image found",
                    "message": "Kein passendes Hintergrundbild gefunden"
                }
            
            # Select the best image (first result)
            selected_image = image_search_result["images"][0]
            
            # Download and process the image
            background_result = self._download_and_process_image(selected_image, post_hash)
            
            if not background_result["success"]:
                return background_result
            
            # Create the visual post
            post_result = self._create_post_image(
                background_result["image_path"],
                text,
                period,
                post_hash,
                image_style
            )
            
            if not post_result["success"]:
                return post_result
            
            # Store post information
            post_info = {
                "id": post_hash,
                "text": text,
                "period": period,
                "tags": tags,
                "period_color": self.period_colors.get(period, "#808080"),
                "image_style": image_style,
                "file_path": post_result["output_path"],
                "file_url": post_result["output_url"],
                "background_image": {
                    "id": selected_image["id"],
                    "photographer": selected_image["photographer"],
                    "pexels_url": selected_image["pexels_url"]
                },
                "created_at": datetime.now().isoformat(),
                "dimensions": {
                    "width": self.story_width,
                    "height": self.story_height
                }
            }
            
            # Save to storage
            self.posts_storage["posts"].append(post_info)
            self.posts_storage["by_period"][post_hash] = post_info
            self._save_posts_storage()
            
            return {
                "success": True,
                "post": post_info,
                "source": "generated",
                "message": f"Visueller Post für {period} erstellt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des visuellen Posts"
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
    
    def _create_post_image(self, background_path: str, text: str, period: str, 
                          post_hash: str, image_style: str) -> Dict[str, Any]:
        """Create the final post image with text overlay"""
        try:
            # Load background image
            background = Image.open(background_path)
            
            # Resize to Instagram Story format
            background = self._resize_to_story_format(background)
            
            # Create overlay
            overlay = Image.new('RGBA', (self.story_width, self.story_height), (0, 0, 0, 0))
            
            # Add color overlay
            color_overlay = self._create_color_overlay(period, image_style)
            overlay = Image.alpha_composite(overlay, color_overlay)
            
            # Add text
            text_overlay = self._create_text_overlay(text, period, image_style)
            overlay = Image.alpha_composite(overlay, text_overlay)
            
            # Combine background and overlay
            if background.mode != 'RGBA':
                background = background.convert('RGBA')
            
            final_image = Image.alpha_composite(background, overlay)
            
            # Convert to RGB for JPEG
            final_image = final_image.convert('RGB')
            
            # Save final image
            output_filename = f"{period.lower()}_{post_hash[:8]}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            final_image.save(output_path, 'JPEG', quality=95)
            
            # Create URL for frontend access
            output_url = f"/static/visuals/{output_filename}"
            
            # Clean up temporary file
            if os.path.exists(background_path):
                os.remove(background_path)
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": output_url,
                "filename": output_filename
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des finalen Bildes"
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
    
    def _create_color_overlay(self, period: str, image_style: str) -> Image.Image:
        """Create color overlay based on period and style"""
        overlay = Image.new('RGBA', (self.story_width, self.story_height), (0, 0, 0, 0))
        
        # Get period color
        period_color = self.period_colors.get(period, "#808080")
        
        # Convert hex to RGB
        color_rgb = tuple(int(period_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Define overlay styles
        if image_style == "minimal":
            # Light overlay for minimal style
            overlay_color = color_rgb + (76,)  # 30% opacity
        elif image_style == "dramatic":
            # Stronger overlay for dramatic style
            overlay_color = color_rgb + (127,)  # 50% opacity
        elif image_style == "gradient":
            # Gradient overlay
            return self._create_gradient_overlay(color_rgb)
        else:
            # Default overlay
            overlay_color = color_rgb + (102,)  # 40% opacity
        
        # Create solid color overlay
        color_layer = Image.new('RGBA', (self.story_width, self.story_height), overlay_color)
        return color_layer
    
    def _create_gradient_overlay(self, color_rgb: Tuple[int, int, int]) -> Image.Image:
        """Create gradient overlay"""
        overlay = Image.new('RGBA', (self.story_width, self.story_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Create vertical gradient
        for y in range(self.story_height):
            # Stronger at top and bottom, lighter in middle
            if y < self.story_height // 3:
                alpha = int(127 * (1 - y / (self.story_height // 3)))
            elif y > 2 * self.story_height // 3:
                alpha = int(127 * (y - 2 * self.story_height // 3) / (self.story_height // 3))
            else:
                alpha = 51  # Light overlay in middle
            
            color = color_rgb + (alpha,)
            draw.line([(0, y), (self.story_width, y)], fill=color)
        
        return overlay
    
    def _create_text_overlay(self, text: str, period: str, image_style: str) -> Image.Image:
        """Create text overlay"""
        overlay = Image.new('RGBA', (self.story_width, self.story_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Try to load custom font, fallback to default
        try:
            # Try different font sizes based on text length
            if len(text) < 50:
                font_size = 72
            elif len(text) < 100:
                font_size = 60
            else:
                font_size = 48
            
            # Try to load a nice font (you may need to install fonts)
            font_paths = [
                "/System/Library/Fonts/Helvetica.ttc",  # macOS
                "/Windows/Fonts/arial.ttf",  # Windows
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font = ImageFont.truetype(font_path, font_size)
                    break
            
            if font is None:
                font = ImageFont.load_default()
                
        except Exception:
            font = ImageFont.load_default()
        
        # Calculate text positioning
        text_lines = self._wrap_text(text, font, self.story_width - 200)  # 100px margin each side
        
        # Calculate total text height
        total_height = len(text_lines) * (font_size + 10)
        
        # Center vertically
        start_y = (self.story_height - total_height) // 2
        
        # Draw text with shadow for better readability
        for i, line in enumerate(text_lines):
            # Get text bounding box
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            
            # Center horizontally
            x = (self.story_width - text_width) // 2
            y = start_y + i * (font_size + 10)
            
            # Draw shadow
            shadow_offset = 3
            draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=(0, 0, 0, 128))
            
            # Draw main text
            draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        
        return overlay
    
    def _wrap_text(self, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
        """Wrap text to fit within max width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = font.getbbox(test_line)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word is too long, add it anyway
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def get_posts_by_period(self, period: str = None) -> Dict[str, Any]:
        """Get all visual posts, optionally filtered by period"""
        try:
            if period:
                filtered_posts = [
                    post for post in self.posts_storage.get("posts", [])
                    if post.get("period") == period
                ]
            else:
                filtered_posts = self.posts_storage.get("posts", [])
            
            return {
                "success": True,
                "posts": filtered_posts,
                "count": len(filtered_posts),
                "period": period
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Abrufen der visuellen Posts"
            }
    
    def delete_post(self, post_id: str) -> Dict[str, Any]:
        """Delete a visual post"""
        try:
            # Find and remove from storage
            posts = self.posts_storage.get("posts", [])
            post_to_delete = None
            
            for i, post in enumerate(posts):
                if post["id"] == post_id:
                    post_to_delete = posts.pop(i)
                    break
            
            if not post_to_delete:
                return {
                    "success": False,
                    "error": "Post not found",
                    "message": "Post nicht gefunden"
                }
            
            # Remove from by_period index
            if post_id in self.posts_storage.get("by_period", {}):
                del self.posts_storage["by_period"][post_id]
            
            # Delete file
            if os.path.exists(post_to_delete["file_path"]):
                os.remove(post_to_delete["file_path"])
            
            # Save updated storage
            self._save_posts_storage()
            
            return {
                "success": True,
                "message": "Post erfolgreich gelöscht"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Löschen des Posts"
            }