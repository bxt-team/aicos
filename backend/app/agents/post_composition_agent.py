import os
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM
from app.tools.video_template_tools import VideoTemplateProcessor
import requests
import tempfile

class PostCompositionAgent(BaseCrew):
    """Agent for composing visual posts using templates and Python code"""
    
    def __init__(self, openai_api_key: str):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Storage for composed posts - using separate file to avoid conflicts
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/composed_posts_storage.json")
        self.posts_storage = self._load_posts_storage()
        
        # Output directory for composed images
        self.output_dir = os.path.join(os.path.dirname(__file__), "../../static/composed")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize video template processor for advanced templates
        self.video_processor = VideoTemplateProcessor()
        
        # Create the post composition agent
        self.composer_agent = self.create_agent("post_composition_agent", llm=self.llm)
        
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
        """Load previously composed posts"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    # If the data has the old visual_posts_storage.json format, convert it
                    if "posts" in data and "by_period" in data:
                        return {
                            "posts": data["posts"],
                            "by_hash": data.get("by_period", {})
                        }
                    return data
        except Exception as e:
            print(f"Error loading posts storage: {e}")
        return {"posts": [], "by_hash": {}}
    
    def _save_posts_storage(self):
        """Save composed posts to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.posts_storage, f, indent=2)
        except Exception as e:
            print(f"Error saving posts storage: {e}")
    
    def _generate_composition_hash(self, background_path: str, text: str, period: str, template_name: str) -> str:
        """Generate a hash for the composition parameters"""
        composition_key = f"{background_path}_{text}_{period}_{template_name}"
        return hashlib.md5(composition_key.encode()).hexdigest()
    
    def compose_post(self, background_path: str, text: str, period: str, 
                    template_name: str = "default", post_format: str = "story", 
                    custom_options: Dict[str, Any] = None, force_new: bool = False) -> Dict[str, Any]:
        """Compose a visual post using a template"""
        try:
            # Check if composition already exists
            composition_hash = self._generate_composition_hash(background_path, text, period, template_name)
            
            if not force_new and composition_hash in self.posts_storage.get("by_hash", {}):
                existing_post = self.posts_storage["by_hash"][composition_hash]
                if os.path.exists(existing_post["file_path"]):
                    return {
                        "success": True,
                        "post": existing_post,
                        "source": "existing",
                        "message": "Bestehende Komposition abgerufen"
                    }
            
            # Validate background image exists
            if not os.path.exists(background_path):
                return {
                    "success": False,
                    "error": "Background image not found",
                    "message": "Hintergrundbild nicht gefunden"
                }
            
            # Compose the post based on template
            composition_result = self._compose_with_template(
                background_path,
                text,
                period,
                template_name,
                post_format,
                custom_options or {}
            )
            
            if not composition_result["success"]:
                return composition_result
            
            # Store composition information
            post_info = {
                "id": composition_hash,
                "text": text,
                "period": period,
                "tags": [],  # Add empty tags array for compatibility
                "template_name": template_name,
                "post_format": post_format,
                "period_color": self.period_colors.get(period, "#808080"),
                "image_style": "composed",  # Mark as composed image
                "background_path": background_path,
                "file_path": composition_result["output_path"],
                "file_url": composition_result["output_url"],
                "background_image": {},  # Add empty background_image for compatibility
                "custom_options": custom_options or {},
                "created_at": datetime.now().isoformat(),
                "dimensions": {
                    "width": self.post_width if post_format == "post" else self.story_width,
                    "height": self.post_height if post_format == "post" else self.story_height
                }
            }
            
            # Save to storage
            self.posts_storage["posts"].append(post_info)
            self.posts_storage["by_hash"][composition_hash] = post_info
            self._save_posts_storage()
            
            return {
                "success": True,
                "post": post_info,
                "source": "generated",
                "message": f"Post für {period} komponiert"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Komponieren des Posts"
            }
    
    def _compose_with_template(self, background_path: str, text: str, period: str, 
                              template_name: str, post_format: str, custom_options: Dict[str, Any]) -> Dict[str, Any]:
        """Compose post using specified template"""
        try:
            # Check if this is a video template
            if template_name.startswith("video:"):
                return self._apply_video_template(
                    background_path, text, period, template_name, post_format, custom_options
                )
            
            # Load background image for PIL templates
            background = Image.open(background_path)
            
            # Resize to appropriate Instagram format
            if post_format == "post":
                background = self._resize_to_post_format(background)
                canvas_width, canvas_height = self.post_width, self.post_height
            else:
                background = self._resize_to_story_format(background)
                canvas_width, canvas_height = self.story_width, self.story_height
            
            # Apply template based on template_name
            if template_name == "minimal":
                composed_image = self._apply_minimal_template(background, text, period, custom_options)
            elif template_name == "dramatic":
                composed_image = self._apply_dramatic_template(background, text, period, custom_options)
            elif template_name == "gradient":
                composed_image = self._apply_gradient_template(background, text, period, custom_options)
            elif template_name == "quote_card":
                composed_image = self._apply_quote_card_template(background, text, period, custom_options)
            elif template_name == "period_branding":
                composed_image = self._apply_period_branding_template(background, text, period, custom_options)
            else:
                # Default template
                composed_image = self._apply_default_template(background, text, period, custom_options)
            
            # Convert to RGB for JPEG
            composed_image = composed_image.convert('RGB')
            
            # Generate output filename
            format_suffix = "post" if post_format == "post" else "story"
            composition_hash = self._generate_composition_hash(background_path, text, period, template_name)
            output_filename = f"{period.lower()}_{template_name}_{format_suffix}_{composition_hash[:8]}.jpg"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Save final image
            composed_image.save(output_path, 'JPEG', quality=95)
            
            # Create URL for frontend access
            output_url = f"/static/composed/{output_filename}"
            
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
                "message": "Fehler beim Anwenden des Templates"
            }
    
    def _apply_minimal_template(self, background: Image.Image, text: str, period: str, options: Dict[str, Any]) -> Image.Image:
        """Apply minimal template with light overlay and simple text"""
        canvas_width, canvas_height = background.size
        
        # Create overlay
        overlay = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        
        # Light color overlay
        color_overlay = self._create_color_overlay(period, "minimal", canvas_width, canvas_height)
        overlay = Image.alpha_composite(overlay, color_overlay)
        
        # Simple text overlay
        text_overlay = self._create_text_overlay(text, period, "minimal", canvas_width, canvas_height, options)
        overlay = Image.alpha_composite(overlay, text_overlay)
        
        # Combine with background
        if background.mode != 'RGBA':
            background = background.convert('RGBA')
        
        return Image.alpha_composite(background, overlay)
    
    def _apply_dramatic_template(self, background: Image.Image, text: str, period: str, options: Dict[str, Any]) -> Image.Image:
        """Apply dramatic template with strong overlay and bold text"""
        canvas_width, canvas_height = background.size
        
        # Create overlay
        overlay = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        
        # Strong color overlay
        color_overlay = self._create_color_overlay(period, "dramatic", canvas_width, canvas_height)
        overlay = Image.alpha_composite(overlay, color_overlay)
        
        # Bold text overlay
        text_overlay = self._create_text_overlay(text, period, "dramatic", canvas_width, canvas_height, options)
        overlay = Image.alpha_composite(overlay, text_overlay)
        
        # Combine with background
        if background.mode != 'RGBA':
            background = background.convert('RGBA')
        
        return Image.alpha_composite(background, overlay)
    
    def _apply_gradient_template(self, background: Image.Image, text: str, period: str, options: Dict[str, Any]) -> Image.Image:
        """Apply gradient template with gradient overlay"""
        canvas_width, canvas_height = background.size
        
        # Create overlay
        overlay = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        
        # Gradient overlay
        gradient_overlay = self._create_gradient_overlay(period, canvas_width, canvas_height)
        overlay = Image.alpha_composite(overlay, gradient_overlay)
        
        # Text overlay
        text_overlay = self._create_text_overlay(text, period, "gradient", canvas_width, canvas_height, options)
        overlay = Image.alpha_composite(overlay, text_overlay)
        
        # Combine with background
        if background.mode != 'RGBA':
            background = background.convert('RGBA')
        
        return Image.alpha_composite(background, overlay)
    
    def _apply_quote_card_template(self, background: Image.Image, text: str, period: str, options: Dict[str, Any]) -> Image.Image:
        """Apply quote card template with card background"""
        canvas_width, canvas_height = background.size
        
        # Create overlay
        overlay = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        
        # Create card background
        card_overlay = self._create_card_overlay(period, canvas_width, canvas_height)
        overlay = Image.alpha_composite(overlay, card_overlay)
        
        # Quote text overlay
        text_overlay = self._create_quote_text_overlay(text, period, canvas_width, canvas_height, options)
        overlay = Image.alpha_composite(overlay, text_overlay)
        
        # Combine with background
        if background.mode != 'RGBA':
            background = background.convert('RGBA')
        
        return Image.alpha_composite(background, overlay)
    
    def _apply_period_branding_template(self, background: Image.Image, text: str, period: str, options: Dict[str, Any]) -> Image.Image:
        """Apply period branding template with period-specific elements"""
        canvas_width, canvas_height = background.size
        
        # Create overlay
        overlay = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
        
        # Period branding overlay
        branding_overlay = self._create_period_branding_overlay(period, canvas_width, canvas_height)
        overlay = Image.alpha_composite(overlay, branding_overlay)
        
        # Branded text overlay
        text_overlay = self._create_branded_text_overlay(text, period, canvas_width, canvas_height, options)
        overlay = Image.alpha_composite(overlay, text_overlay)
        
        # Combine with background
        if background.mode != 'RGBA':
            background = background.convert('RGBA')
        
        return Image.alpha_composite(background, overlay)
    
    def _apply_default_template(self, background: Image.Image, text: str, period: str, options: Dict[str, Any]) -> Image.Image:
        """Apply default template"""
        return self._apply_minimal_template(background, text, period, options)
    
    def _create_color_overlay(self, period: str, style: str, width: int, height: int) -> Image.Image:
        """Create color overlay based on period and style"""
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        
        # Get period color
        period_color = self.period_colors.get(period, "#808080")
        color_rgb = tuple(int(period_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Define overlay styles
        if style == "minimal":
            overlay_color = color_rgb + (76,)  # 30% opacity
        elif style == "dramatic":
            overlay_color = color_rgb + (127,)  # 50% opacity
        else:
            overlay_color = color_rgb + (102,)  # 40% opacity
        
        # Create solid color overlay
        color_layer = Image.new('RGBA', (width, height), overlay_color)
        return color_layer
    
    def _create_gradient_overlay(self, period: str, width: int, height: int) -> Image.Image:
        """Create gradient overlay"""
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Get period color
        period_color = self.period_colors.get(period, "#808080")
        color_rgb = tuple(int(period_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Create vertical gradient
        for y in range(height):
            # Stronger at top and bottom, lighter in middle
            if y < height // 3:
                alpha = int(127 * (1 - y / (height // 3)))
            elif y > 2 * height // 3:
                alpha = int(127 * (y - 2 * height // 3) / (height // 3))
            else:
                alpha = 51  # Light overlay in middle
            
            color = color_rgb + (alpha,)
            draw.line([(0, y), (width, y)], fill=color)
        
        return overlay
    
    def _create_card_overlay(self, period: str, width: int, height: int) -> Image.Image:
        """Create card background overlay"""
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Card dimensions
        card_margin = 100
        card_x = card_margin
        card_y = height // 4
        card_width = width - 2 * card_margin
        card_height = height // 2
        
        # Draw card background
        draw.rounded_rectangle(
            [card_x, card_y, card_x + card_width, card_y + card_height],
            radius=20,
            fill=(255, 255, 255, 200)
        )
        
        # Draw card border
        period_color = self.period_colors.get(period, "#808080")
        color_rgb = tuple(int(period_color[i:i+2], 16) for i in (1, 3, 5))
        draw.rounded_rectangle(
            [card_x, card_y, card_x + card_width, card_y + card_height],
            radius=20,
            outline=color_rgb + (255,),
            width=5
        )
        
        return overlay
    
    def _create_period_branding_overlay(self, period: str, width: int, height: int) -> Image.Image:
        """Create period-specific branding overlay"""
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Get period color
        period_color = self.period_colors.get(period, "#808080")
        color_rgb = tuple(int(period_color[i:i+2], 16) for i in (1, 3, 5))
        
        # Create branded header
        header_height = 100
        draw.rectangle([0, 0, width, header_height], fill=color_rgb + (200,))
        
        # Create branded footer
        footer_height = 80
        draw.rectangle([0, height - footer_height, width, height], fill=color_rgb + (150,))
        
        return overlay
    
    def _create_text_overlay(self, text: str, period: str, style: str, width: int, height: int, options: Dict[str, Any]) -> Image.Image:
        """Create text overlay"""
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Get font
        font = self._get_font(style, width, height, len(text))
        
        # Calculate text positioning
        margin = options.get("text_margin", 150)
        text_lines = self._wrap_text(text, font, width - margin)
        
        # Calculate total text height
        line_height = options.get("line_height", font.size + 10)
        total_height = len(text_lines) * line_height
        
        # Center vertically
        start_y = (height - total_height) // 2
        
        # Draw text with shadow
        for i, line in enumerate(text_lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            
            x = (width - text_width) // 2
            y = start_y + i * line_height
            
            # Draw shadow
            shadow_offset = options.get("shadow_offset", 3)
            draw.text((x + shadow_offset, y + shadow_offset), line, font=font, fill=(0, 0, 0, 128))
            
            # Draw main text
            text_color = options.get("text_color", (255, 255, 255, 255))
            draw.text((x, y), line, font=font, fill=text_color)
        
        return overlay
    
    def _create_quote_text_overlay(self, text: str, period: str, width: int, height: int, options: Dict[str, Any]) -> Image.Image:
        """Create quote-style text overlay"""
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Get font
        font = self._get_font("quote", width, height, len(text))
        
        # Add quote marks
        quote_text = f'"{text}"'
        
        # Calculate text positioning
        margin = 150
        text_lines = self._wrap_text(quote_text, font, width - margin)
        
        # Calculate total text height
        line_height = font.size + 15
        total_height = len(text_lines) * line_height
        
        # Center vertically
        start_y = (height - total_height) // 2
        
        # Draw text
        for i, line in enumerate(text_lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            
            x = (width - text_width) // 2
            y = start_y + i * line_height
            
            # Draw shadow
            draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 128))
            
            # Draw main text
            draw.text((x, y), line, font=font, fill=(50, 50, 50, 255))
        
        return overlay
    
    def _create_branded_text_overlay(self, text: str, period: str, width: int, height: int, options: Dict[str, Any]) -> Image.Image:
        """Create branded text overlay with period name"""
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Get fonts
        title_font = self._get_font("title", width, height, len(period))
        text_font = self._get_font("text", width, height, len(text))
        
        # Draw period name in header
        period_bbox = draw.textbbox((0, 0), period, font=title_font)
        period_width = period_bbox[2] - period_bbox[0]
        period_x = (width - period_width) // 2
        period_y = 30
        
        draw.text((period_x, period_y), period, font=title_font, fill=(255, 255, 255, 255))
        
        # Draw main text
        margin = 150
        text_lines = self._wrap_text(text, text_font, width - margin)
        
        # Calculate text positioning
        available_height = height - 200  # Account for header and footer
        line_height = text_font.size + 10
        total_height = len(text_lines) * line_height
        start_y = 150 + (available_height - total_height) // 2
        
        for i, line in enumerate(text_lines):
            bbox = draw.textbbox((0, 0), line, font=text_font)
            text_width = bbox[2] - bbox[0]
            
            x = (width - text_width) // 2
            y = start_y + i * line_height
            
            # Draw shadow
            draw.text((x + 2, y + 2), line, font=text_font, fill=(0, 0, 0, 128))
            
            # Draw main text
            draw.text((x, y), line, font=text_font, fill=(255, 255, 255, 255))
        
        return overlay
    
    def _get_font(self, style: str, width: int, height: int, text_length: int) -> ImageFont.ImageFont:
        """Get appropriate font based on style and dimensions"""
        # Determine base font size
        if style == "title":
            base_size = 80
        elif style == "quote":
            base_size = 60
        else:
            if text_length < 50:
                base_size = 72 if height > 1500 else 64
            elif text_length < 100:
                base_size = 60 if height > 1500 else 52
            else:
                base_size = 48 if height > 1500 else 42
        
        # Try to load system fonts
        font_paths = [
            "/System/Library/Fonts/Helvetica.ttc",  # macOS
            "/Windows/Fonts/arial.ttf",  # Windows
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, base_size)
                except:
                    continue
        
        return ImageFont.load_default()
    
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
                    lines.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _resize_to_story_format(self, image: Image.Image) -> Image.Image:
        """Resize image to Instagram Story format (1080x1920)"""
        img_ratio = image.width / image.height
        story_ratio = self.story_width / self.story_height
        
        if img_ratio > story_ratio:
            new_height = self.story_height
            new_width = int(new_height * img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = (new_width - self.story_width) // 2
            image = image.crop((left, 0, left + self.story_width, self.story_height))
        else:
            new_width = self.story_width
            new_height = int(new_width / img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            top = (new_height - self.story_height) // 2
            image = image.crop((0, top, self.story_width, top + self.story_height))
        
        return image
    
    def _apply_video_template(self, background_path: str, text: str, period: str, 
                             template_name: str, post_format: str, custom_options: Dict[str, Any]) -> Dict[str, Any]:
        """Apply video template to create dynamic video content"""
        try:
            # Extract template ID
            template_id = template_name.replace("video:", "")
            
            # Prepare replacements based on template and custom options
            replacements = {
                "background_color": custom_options.get("background_color", self.period_colors.get(period, "#000000")),
                "text_main_text": custom_options.get("main_text", text),
                "text_subtitle": custom_options.get("subtitle", f"7 Cycles - {period}"),
                "text_period_name": period,
                "text_period_description": custom_options.get("period_description", ""),
                "color_primary_overlay": self.period_colors.get(period, "#808080"),
                "color_period_color": self.period_colors.get(period, "#808080")
            }
            
            # Add custom text replacements
            if "text_replacements" in custom_options:
                for key, value in custom_options["text_replacements"].items():
                    replacements[f"text_{key}"] = value
            
            # Add custom color replacements
            if "color_replacements" in custom_options:
                for key, value in custom_options["color_replacements"].items():
                    replacements[f"color_{key}"] = value
            
            # Add video replacements
            if "video_replacements" in custom_options:
                for key, value in custom_options["video_replacements"].items():
                    replacements[f"video_{key}"] = value
            
            # Generate output filename
            composition_hash = self._generate_composition_hash(background_path, text, period, template_name)
            output_filename = f"{period.lower()}_video_{template_id}_{composition_hash[:8]}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Create video from template
            result = self.video_processor.create_video_from_template(
                template_id,
                replacements,
                output_path
            )
            
            if not result["success"]:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Fehler beim Erstellen des Videos: {result.get('error', 'Unknown error')}"
                }
            
            # Create URL for frontend access
            output_url = f"/static/composed/{output_filename}"
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": output_url,
                "filename": output_filename,
                "template": template_id,
                "duration": result.get("duration", 0)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Fehler beim Anwenden des Video-Templates: {str(e)}"
            }
    
    def _resize_to_post_format(self, image: Image.Image) -> Image.Image:
        """Resize image to Instagram Post format (4:5 ratio - 1080x1350)"""
        img_ratio = image.width / image.height
        post_ratio = self.post_width / self.post_height
        
        if img_ratio > post_ratio:
            new_height = self.post_height
            new_width = int(new_height * img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = (new_width - self.post_width) // 2
            image = image.crop((left, 0, left + self.post_width, self.post_height))
        else:
            new_width = self.post_width
            new_height = int(new_width / img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            top = (new_height - self.post_height) // 2
            image = image.crop((0, top, self.post_width, top + self.post_height))
        
        return image
    
    def get_composed_posts(self, period: str = None, template: str = None) -> Dict[str, Any]:
        """Get all composed posts, optionally filtered by period or template"""
        try:
            posts = self.posts_storage.get("posts", [])
            
            if period:
                posts = [post for post in posts if post.get("period") == period]
            
            if template:
                posts = [post for post in posts if post.get("template_name") == template]
            
            return {
                "success": True,
                "posts": posts,
                "count": len(posts),
                "filters": {"period": period, "template": template}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Abrufen der komponierten Posts"
            }
    
    def delete_composed_post(self, post_id: str) -> Dict[str, Any]:
        """Delete a composed post"""
        try:
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
            
            # Remove from hash index
            if post_id in self.posts_storage.get("by_hash", {}):
                del self.posts_storage["by_hash"][post_id]
            
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
    
    def get_available_templates(self) -> Dict[str, Any]:
        """Get list of available templates"""
        templates = {
            "default": {
                "name": "Standard",
                "description": "Einfaches Overlay mit Text",
                "options": ["text_margin", "shadow_offset", "text_color"],
                "type": "pil"
            },
            "minimal": {
                "name": "Minimal",
                "description": "Leichtes Overlay mit einfachem Text",
                "options": ["text_margin", "shadow_offset"],
                "type": "pil"
            },
            "dramatic": {
                "name": "Dramatisch",
                "description": "Starkes Overlay mit fettem Text",
                "options": ["text_margin", "shadow_offset", "text_color"],
                "type": "pil"
            },
            "gradient": {
                "name": "Gradient",
                "description": "Gradient-Overlay für dynamische Effekte",
                "options": ["text_margin", "line_height"],
                "type": "pil"
            },
            "quote_card": {
                "name": "Zitat-Karte",
                "description": "Kartenhintergrund für Zitate",
                "options": ["text_margin", "line_height"],
                "type": "pil"
            },
            "period_branding": {
                "name": "Perioden-Branding",
                "description": "Branding-Elemente für 7 Cycles Perioden",
                "options": ["text_margin", "line_height", "text_color"],
                "type": "pil"
            }
        }
        
        # Add video templates
        video_templates = self.video_processor.get_available_templates()
        for vt in video_templates:
            templates[f"video:{vt['id']}"] = {
                "name": vt["name"],
                "description": vt["description"],
                "options": ["text_replacements", "video_replacements", "color_replacements"],
                "type": "video",
                "duration": vt["duration"],
                "replaceable_elements": vt["replaceable_elements"]
            }
        
        return {
            "success": True,
            "templates": templates,
            "video_templates_enabled": True
        }
    
    def get_video_template_fields(self, template_id: str) -> Dict[str, Any]:
        """Get replaceable fields for a video template"""
        try:
            templates = self.video_processor.get_available_templates()
            for template in templates:
                if template["id"] == template_id:
                    return {
                        "success": True,
                        "fields": template["replaceable_elements"],
                        "template_id": template_id,
                        "duration": template["duration"]
                    }
            
            return {
                "success": False,
                "error": "Template not found",
                "message": f"Video-Template '{template_id}' nicht gefunden"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Fehler beim Abrufen der Template-Felder: {str(e)}"
            }
    
    def create_video_reel(self, template_id: str, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a reel/video using a video template"""
        try:
            # Prepare replacements
            replacements = {}
            
            # Add text replacements
            if "text_replacements" in content_data:
                for key, value in content_data["text_replacements"].items():
                    replacements[f"text_{key}"] = value
            
            # Add color replacements
            if "color_replacements" in content_data:
                for key, value in content_data["color_replacements"].items():
                    replacements[f"color_{key}"] = value
            
            # Add video replacements
            if "video_replacements" in content_data:
                for key, value in content_data["video_replacements"].items():
                    replacements[f"video_{key}"] = value
            
            # Add period information if provided
            if "period" in content_data:
                period = content_data["period"]
                replacements["color_period_color"] = self.period_colors.get(period, "#808080")
                replacements["text_period_name"] = period
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"video_reel_{template_id}_{timestamp}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Create video
            result = self.video_processor.create_video_from_template(
                template_id,
                replacements,
                output_path
            )
            
            if not result["success"]:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": f"Fehler beim Erstellen des Video-Reels: {result.get('error', 'Unknown error')}"
                }
            
            # Create URL for frontend access
            output_url = f"/static/composed/{output_filename}"
            
            # Store in posts storage
            post_info = {
                "id": hashlib.md5(f"{template_id}_{timestamp}".encode()).hexdigest(),
                "type": "reel",
                "template_id": template_id,
                "file_path": output_path,
                "file_url": output_url,
                "duration": result.get("duration", 0),
                "created_at": datetime.now().isoformat(),
                "content_data": content_data
            }
            
            self.posts_storage["posts"].append(post_info)
            self._save_posts_storage()
            
            return {
                "success": True,
                "reel": post_info,
                "message": "Video-Reel erfolgreich erstellt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Fehler beim Erstellen des Video-Reels: {str(e)}"
            }