"""
Video template tools for creating dynamic videos with replaceable elements
Uses MoviePy for video manipulation without requiring Canva API
"""

import os
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from moviepy.editor import (
    VideoFileClip, TextClip, CompositeVideoClip, 
    ColorClip, ImageClip, concatenate_videoclips,
    AudioFileClip, CompositeAudioClip
)
from moviepy.video.fx import resize, crop
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import tempfile
import logging

logger = logging.getLogger(__name__)


@dataclass
class VideoTemplate:
    """Video template configuration"""
    name: str
    description: str
    duration: float
    resolution: Tuple[int, int] = (1080, 1920)  # Instagram Reel format
    background_color: str = "#000000"
    text_zones: List[Dict[str, Any]] = None
    video_zones: List[Dict[str, Any]] = None
    color_overlays: List[Dict[str, Any]] = None
    transitions: List[Dict[str, Any]] = None


class VideoTemplateProcessor:
    """Process video templates with dynamic content replacement"""
    
    def __init__(self):
        self.templates_dir = os.path.join(os.path.dirname(__file__), "../../static/video_templates")
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Instagram video specifications
        self.reel_width = 1080
        self.reel_height = 1920
        self.story_width = 1080
        self.story_height = 1920
        self.post_width = 1080
        self.post_height = 1080
        
        # Load or create default templates
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, VideoTemplate]:
        """Load video templates from configuration"""
        templates = {
            "energy_burst": VideoTemplate(
                name="Energy Burst",
                description="Dynamic energy-themed video with color transitions",
                duration=15.0,
                text_zones=[
                    {
                        "id": "main_text",
                        "position": ("center", "center"),
                        "size": 80,
                        "color": "white",
                        "font": "Arial-Bold",
                        "start_time": 1,
                        "duration": 4,
                        "animation": "fade_in"
                    },
                    {
                        "id": "subtitle",
                        "position": ("center", 1200),
                        "size": 40,
                        "color": "white",
                        "font": "Arial",
                        "start_time": 5,
                        "duration": 8,
                        "animation": "slide_up"
                    }
                ],
                video_zones=[
                    {
                        "id": "background_video",
                        "position": (0, 0),
                        "size": "full",
                        "start_time": 0,
                        "duration": 15,
                        "blend_mode": "normal"
                    }
                ],
                color_overlays=[
                    {
                        "id": "primary_overlay",
                        "color": "#2196F3",
                        "opacity": 0.3,
                        "start_time": 0,
                        "duration": 15,
                        "animation": "pulse"
                    }
                ]
            ),
            
            "quote_carousel": VideoTemplate(
                name="Quote Carousel",
                description="Animated quote presentation with background video",
                duration=20.0,
                text_zones=[
                    {
                        "id": "quote_1",
                        "position": ("center", "center"),
                        "size": 60,
                        "color": "white",
                        "start_time": 2,
                        "duration": 5,
                        "animation": "fade_in_out"
                    },
                    {
                        "id": "quote_2",
                        "position": ("center", "center"),
                        "size": 60,
                        "color": "white",
                        "start_time": 8,
                        "duration": 5,
                        "animation": "fade_in_out"
                    },
                    {
                        "id": "quote_3",
                        "position": ("center", "center"),
                        "size": 60,
                        "color": "white",
                        "start_time": 14,
                        "duration": 5,
                        "animation": "fade_in_out"
                    }
                ],
                video_zones=[
                    {
                        "id": "background_loop",
                        "position": (0, 0),
                        "size": "full",
                        "start_time": 0,
                        "duration": 20,
                        "loop": True
                    }
                ]
            ),
            
            "period_showcase": VideoTemplate(
                name="Period Showcase",
                description="7 Cycles period presentation with dynamic colors",
                duration=10.0,
                text_zones=[
                    {
                        "id": "period_name",
                        "position": ("center", 400),
                        "size": 100,
                        "color": "white",
                        "font": "Arial-Bold",
                        "start_time": 1,
                        "duration": 8,
                        "animation": "zoom_in"
                    },
                    {
                        "id": "period_description",
                        "position": ("center", 1000),
                        "size": 45,
                        "color": "white",
                        "font": "Arial",
                        "start_time": 2,
                        "duration": 7,
                        "animation": "fade_in"
                    }
                ],
                color_overlays=[
                    {
                        "id": "period_color",
                        "color": "#FF0000",
                        "opacity": 0.4,
                        "start_time": 0,
                        "duration": 10,
                        "gradient": True
                    }
                ]
            )
        }
        
        return templates
    
    def create_video_from_template(
        self, 
        template_name: str,
        replacements: Dict[str, Any],
        output_path: str
    ) -> Dict[str, Any]:
        """Create a video from template with dynamic replacements"""
        try:
            template = self.templates.get(template_name)
            if not template:
                return {"success": False, "error": f"Template '{template_name}' not found"}
            
            # Create video composition
            clips = []
            
            # 1. Add background (color or video)
            background_clip = self._create_background(template, replacements)
            clips.append(background_clip)
            
            # 2. Add video zones
            for video_zone in template.video_zones or []:
                video_clip = self._add_video_zone(video_zone, replacements, template)
                if video_clip:
                    clips.append(video_clip)
            
            # 3. Add color overlays
            for overlay in template.color_overlays or []:
                overlay_clip = self._add_color_overlay(overlay, replacements, template)
                if overlay_clip:
                    clips.append(overlay_clip)
            
            # 4. Add text zones
            for text_zone in template.text_zones or []:
                text_clip = self._add_text_zone(text_zone, replacements, template)
                if text_clip:
                    clips.append(text_clip)
            
            # Composite all clips
            final_video = CompositeVideoClip(
                clips, 
                size=(template.resolution[0], template.resolution[1])
            ).set_duration(template.duration)
            
            # Add audio if provided
            if "audio_path" in replacements:
                audio_clip = AudioFileClip(replacements["audio_path"])
                final_video = final_video.set_audio(audio_clip)
            
            # Export video
            final_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac',
                bitrate="5000k"
            )
            
            # Clean up
            final_video.close()
            
            return {
                "success": True,
                "output_path": output_path,
                "template": template_name,
                "duration": template.duration
            }
            
        except Exception as e:
            logger.error(f"Error creating video from template: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _create_background(self, template: VideoTemplate, replacements: Dict) -> VideoFileClip:
        """Create background clip (solid color)"""
        bg_color = replacements.get("background_color", template.background_color)
        return ColorClip(
            size=template.resolution,
            color=self._hex_to_rgb(bg_color),
            duration=template.duration
        )
    
    def _add_video_zone(self, zone: Dict, replacements: Dict, template: VideoTemplate) -> Optional[VideoFileClip]:
        """Add a video to a specific zone"""
        video_key = f"video_{zone['id']}"
        if video_key not in replacements:
            return None
        
        try:
            video_path = replacements[video_key]
            video_clip = VideoFileClip(video_path)
            
            # Resize to fit zone
            if zone['size'] == 'full':
                video_clip = video_clip.resize(template.resolution)
            else:
                # Custom size handling
                pass
            
            # Set position and duration
            video_clip = video_clip.set_position(zone['position'])
            video_clip = video_clip.set_start(zone['start_time'])
            
            # Handle looping
            if zone.get('loop') and video_clip.duration < zone['duration']:
                video_clip = video_clip.loop(duration=zone['duration'])
            else:
                video_clip = video_clip.set_duration(zone['duration'])
            
            return video_clip
            
        except Exception as e:
            logger.error(f"Error adding video zone: {str(e)}")
            return None
    
    def _add_color_overlay(self, overlay: Dict, replacements: Dict, template: VideoTemplate) -> Optional[ColorClip]:
        """Add color overlay with opacity"""
        color_key = f"color_{overlay['id']}"
        color = replacements.get(color_key, overlay['color'])
        
        try:
            if overlay.get('gradient'):
                # Create gradient overlay
                overlay_clip = self._create_gradient_clip(
                    color, 
                    template.resolution,
                    overlay['duration']
                )
            else:
                # Solid color overlay
                rgb_color = self._hex_to_rgb(color)
                overlay_clip = ColorClip(
                    size=template.resolution,
                    color=rgb_color,
                    duration=overlay['duration']
                )
            
            # Set opacity
            overlay_clip = overlay_clip.set_opacity(overlay['opacity'])
            overlay_clip = overlay_clip.set_start(overlay['start_time'])
            
            # Add animation if specified
            if overlay.get('animation') == 'pulse':
                # Add pulsing effect
                pass
            
            return overlay_clip
            
        except Exception as e:
            logger.error(f"Error adding color overlay: {str(e)}")
            return None
    
    def _add_text_zone(self, zone: Dict, replacements: Dict, template: VideoTemplate) -> Optional[TextClip]:
        """Add text to a specific zone"""
        text_key = f"text_{zone['id']}"
        if text_key not in replacements:
            return None
        
        try:
            text = replacements[text_key]
            
            # Create text clip
            text_clip = TextClip(
                text,
                fontsize=zone['size'],
                color=zone['color'],
                font=zone.get('font', 'Arial'),
                method='caption',
                size=(template.resolution[0] - 100, None),
                align='center'
            )
            
            # Set position
            if zone['position'] == ("center", "center"):
                text_clip = text_clip.set_position('center')
            else:
                text_clip = text_clip.set_position(zone['position'])
            
            # Set timing
            text_clip = text_clip.set_start(zone['start_time'])
            text_clip = text_clip.set_duration(zone['duration'])
            
            # Add animation
            text_clip = self._apply_text_animation(text_clip, zone.get('animation'))
            
            return text_clip
            
        except Exception as e:
            logger.error(f"Error adding text zone: {str(e)}")
            return None
    
    def _apply_text_animation(self, clip: TextClip, animation: str) -> TextClip:
        """Apply animation to text clip"""
        if animation == 'fade_in':
            clip = clip.crossfadein(1)
        elif animation == 'fade_in_out':
            clip = clip.crossfadein(1).crossfadeout(1)
        elif animation == 'slide_up':
            # Implement slide up animation
            pass
        elif animation == 'zoom_in':
            # Implement zoom in animation
            pass
        
        return clip
    
    def _create_gradient_clip(self, color: str, size: Tuple[int, int], duration: float) -> ColorClip:
        """Create a gradient color clip"""
        # Create gradient image using PIL
        gradient = Image.new('RGBA', size)
        draw = ImageDraw.Draw(gradient)
        
        base_color = self._hex_to_rgb(color)
        
        # Create vertical gradient
        for y in range(size[1]):
            alpha = int(255 * (1 - y / size[1]))
            color_with_alpha = base_color + (alpha,)
            draw.line([(0, y), (size[0], y)], fill=color_with_alpha)
        
        # Convert to numpy array and create clip
        gradient_array = np.array(gradient)
        return ImageClip(gradient_array, duration=duration)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available video templates"""
        return [
            {
                "id": template_id,
                "name": template.name,
                "description": template.description,
                "duration": template.duration,
                "replaceable_elements": {
                    "text": [zone["id"] for zone in template.text_zones or []],
                    "videos": [zone["id"] for zone in template.video_zones or []],
                    "colors": [overlay["id"] for overlay in template.color_overlays or []]
                }
            }
            for template_id, template in self.templates.items()
        ]