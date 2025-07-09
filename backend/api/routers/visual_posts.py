from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from schemas.visual_post import (
    DALLEVisualPostRequest, 
    ImageFeedbackRequest, 
    RegenerateWithFeedbackRequest,
    PostCompositionRequest,
    IntegratedPostCompositionRequest
)
from schemas.instagram import InstagramAIImageRequest
from core.dependencies import image_generator, post_composition_agent
from core.config import settings
from datetime import datetime
import json
import os
import uuid
import shutil
from typing import Optional

router = APIRouter(tags=["Visual Posts"])

# Ensure storage directories exist
os.makedirs(settings.get_storage_path(settings.GENERATED_DIR), exist_ok=True)
os.makedirs(settings.get_storage_path(settings.COMPOSED_DIR), exist_ok=True)

@router.post("/search-images")
async def search_images(tags: list[str], period: str, count: int = 10):
    if not image_generator:
        raise HTTPException(status_code=503, detail="Image Generator not initialized")
    
    try:
        # Search for images based on tags
        images = image_generator.search_images(tags, count)
        
        # Enrich with period-based filtering if needed
        period_colors = {
            "Image": "#FF6B6B",
            "Veränderung": "#4ECDC4", 
            "Energie": "#FFE66D",
            "Kreativität": "#A8E6CF",
            "Erfolg": "#C7CEEA",
            "Entspannung": "#FFDAB9",
            "Umsicht": "#B4A0E5"
        }
        
        # Add period color to results
        for image in images:
            image['period'] = period
            image['period_color'] = period_colors.get(period, '#999999')
        
        return {
            "status": "success",
            "images": images,
            "count": len(images),
            "search_tags": tags,
            "period": period
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-visual-post")
async def create_visual_post(
    text: str,
    period: str,
    tags: Optional[list[str]] = None,
    image_style: str = "minimal",
    post_format: str = "post",
    force_new: bool = True
):
    if not image_generator:
        raise HTTPException(status_code=503, detail="Image Generator not initialized")
    
    try:
        # Generate visual post
        result = image_generator.create_affirmation_image(
            text=text,
            period=period,
            tags=tags or [],
            style=image_style,
            post_format=post_format
        )
        
        # Save metadata
        metadata_path = result['file_path'].replace('.jpg', '_metadata.json').replace('.png', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump({
                "text": text,
                "period": period,
                "tags": tags or [],
                "image_style": image_style,
                "post_format": post_format,
                "created_at": datetime.now().isoformat(),
                "background_image": result.get('background_image', {}),
                "dimensions": result.get('dimensions', {})
            }, f, indent=2)
        
        return {
            "status": "success",
            "message": "Visual post created successfully",
            "visual_post": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-dalle-visual-post")
async def create_dalle_visual_post(request: DALLEVisualPostRequest):
    if not image_generator:
        raise HTTPException(status_code=503, detail="Image Generator not initialized")
    
    try:
        # Generate DALL-E image
        result = image_generator.create_dalle_affirmation_image(
            text=request.text,
            period=request.period,
            tags=request.tags or [],
            style="dalle",
            post_format=request.post_format,
            ai_context=request.ai_context
        )
        
        return {
            "status": "success",
            "message": "DALL-E visual post created successfully",
            "visual_post": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-instagram-ai-image")
async def create_instagram_ai_image(request: InstagramAIImageRequest):
    # Implementation would go here
    # This is a placeholder showing the structure
    pass

@router.get("/visual-posts")
async def get_visual_posts(period: Optional[str] = None):
    generated_dir = settings.get_storage_path(settings.GENERATED_DIR)
    
    if not os.path.exists(generated_dir):
        return {"status": "success", "posts": []}
    
    posts = []
    
    for filename in os.listdir(generated_dir):
        if filename.endswith('_metadata.json'):
            with open(os.path.join(generated_dir, filename), 'r') as f:
                metadata = json.load(f)
                
                # Filter by period if specified
                if period and metadata.get('period') != period:
                    continue
                
                image_filename = filename.replace('_metadata.json', '.jpg')
                if not os.path.exists(os.path.join(generated_dir, image_filename)):
                    image_filename = filename.replace('_metadata.json', '.png')
                
                post_id = filename.replace('_metadata.json', '')
                
                posts.append({
                    "id": post_id,
                    "text": metadata.get('text', ''),
                    "period": metadata.get('period', ''),
                    "tags": metadata.get('tags', []),
                    "period_color": get_period_color(metadata.get('period', '')),
                    "image_style": metadata.get('image_style', 'minimal'),
                    "post_format": metadata.get('post_format', 'post'),
                    "file_path": os.path.join(generated_dir, image_filename),
                    "file_url": f"/static/{settings.GENERATED_DIR}/{image_filename}",
                    "background_image": metadata.get('background_image', {}),
                    "created_at": metadata.get('created_at', ''),
                    "dimensions": metadata.get('dimensions', {"width": 1080, "height": 1350})
                })
    
    # Sort by creation date, newest first
    posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return {
        "status": "success",
        "posts": posts,
        "count": len(posts)
    }

@router.delete("/visual-posts/{post_id}")
async def delete_visual_post(post_id: str):
    generated_dir = settings.get_storage_path(settings.GENERATED_DIR)
    
    # Find and delete the image file and metadata
    deleted = False
    
    for ext in ['.jpg', '.png']:
        image_path = os.path.join(generated_dir, f"{post_id}{ext}")
        if os.path.exists(image_path):
            os.remove(image_path)
            deleted = True
    
    metadata_path = os.path.join(generated_dir, f"{post_id}_metadata.json")
    if os.path.exists(metadata_path):
        os.remove(metadata_path)
        deleted = True
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Visual post not found")
    
    return {
        "status": "success",
        "message": "Visual post deleted successfully"
    }

# Helper function
def get_period_color(period: str) -> str:
    period_colors = {
        "Image": "#FF6B6B",
        "Veränderung": "#4ECDC4",
        "Energie": "#FFE66D", 
        "Kreativität": "#A8E6CF",
        "Erfolg": "#C7CEEA",
        "Entspannung": "#FFDAB9",
        "Umsicht": "#B4A0E5"
    }
    return period_colors.get(period, "#999999")