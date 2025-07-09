"""Image processing utility functions"""
from PIL import Image, ImageDraw, ImageFont
import os
from typing import Tuple, Optional

def get_image_dimensions(image_path: str) -> Tuple[int, int]:
    """Get image dimensions (width, height)"""
    with Image.open(image_path) as img:
        return img.size

def resize_image(image_path: str, target_size: Tuple[int, int], output_path: Optional[str] = None) -> str:
    """Resize image to target size"""
    if not output_path:
        output_path = image_path
    
    with Image.open(image_path) as img:
        resized = img.resize(target_size, Image.Resampling.LANCZOS)
        resized.save(output_path)
    
    return output_path

def add_text_overlay(
    image_path: str, 
    text: str, 
    position: Tuple[int, int], 
    font_size: int = 24,
    color: str = "white",
    output_path: Optional[str] = None
) -> str:
    """Add text overlay to image"""
    if not output_path:
        output_path = image_path
    
    with Image.open(image_path) as img:
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        draw.text(position, text, fill=color, font=font)
        img.save(output_path)
    
    return output_path

def create_thumbnail(image_path: str, size: Tuple[int, int] = (150, 150)) -> str:
    """Create thumbnail version of image"""
    directory = os.path.dirname(image_path)
    filename = os.path.basename(image_path)
    name, ext = os.path.splitext(filename)
    
    thumbnail_path = os.path.join(directory, f"{name}_thumb{ext}")
    
    with Image.open(image_path) as img:
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(thumbnail_path)
    
    return thumbnail_path

def get_dominant_color(image_path: str) -> str:
    """Get dominant color from image as hex string"""
    with Image.open(image_path) as img:
        # Resize for faster processing
        img = img.resize((150, 150))
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get colors
        colors = img.getcolors(150 * 150)
        if colors:
            # Sort by frequency and get most common
            sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
            dominant = sorted_colors[0][1]
            # Convert to hex
            return '#{:02x}{:02x}{:02x}'.format(*dominant)
    
    return '#000000'  # Default to black