from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse
from app.models.visual_post import (
    VisualPostRequest,
    DALLEVisualPostRequest, 
    ImageFeedbackRequest, 
    RegenerateWithFeedbackRequest,
    PostCompositionRequest,
    IntegratedPostCompositionRequest
)
from app.models.instagram import InstagramAIImageRequest
from app.core.dependencies import get_agent
from app.core.config import settings
from app.core.auth import get_current_user
from app.models.auth import User
from app.core.middleware import RequestContext
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
async def search_images(
    tags: list[str], 
    period: str, 
    count: int = 10,
    current_user: User = Depends(get_current_user)
):
    """Search for images based on tags (requires authentication)"""
    image_generator = get_agent('image_generator')
    if not image_generator:
        raise HTTPException(status_code=503, detail="Image Generator not initialized")
    
    try:
        # Set context on agent
        if hasattr(image_generator, 'set_context'):
            context = RequestContext(
                user_id=current_user.id,
                organization_id=current_user.default_organization_id
            )
            image_generator.set_context(context)
        
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
            "success": True,
            "images": images,
            "count": len(images),
            "search_tags": tags,
            "period": period
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-visual-post")
async def create_visual_post(
    request: VisualPostRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a visual post (requires authentication)"""
    image_generator = get_agent('image_generator')
    if not image_generator:
        raise HTTPException(status_code=503, detail="Image Generator not initialized")
    
    try:
        # Set context on agent
        if hasattr(image_generator, 'set_context'):
            context = RequestContext(
                user_id=current_user.id,
                organization_id=current_user.default_organization_id
            )
            image_generator.set_context(context)
        
        # Generate visual post
        result = image_generator.create_affirmation_image(
            text=request.text,
            period=request.period,
            tags=request.tags or [],
            style=request.image_style,
            post_format=request.post_format
        )
        
        # Check if generation was successful
        if not result.get('success', False):
            error_msg = result.get('error', 'Unknown error during image generation')
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Save metadata
        metadata_path = result['file_path'].replace('.jpg', '_metadata.json').replace('.png', '_metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump({
                "text": request.text,
                "period": request.period,
                "tags": request.tags or [],
                "image_style": request.image_style,
                "post_format": request.post_format,
                "created_at": datetime.now().isoformat(),
                "background_image": result.get('background_image', {}),
                "dimensions": result.get('dimensions', {}),
                "file_path": result.get('file_path', ''),
                "file_url": result.get('file_url', '')
            }, f, indent=2)
        
        return {
            "success": True,
            "message": "Visual post created successfully",
            "visual_post": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-dalle-visual-post")
async def create_dalle_visual_post(request: DALLEVisualPostRequest):
    image_generator = get_agent('image_generator')
    if not image_generator:
        raise HTTPException(status_code=503, detail="Image Generator not initialized")
    
    try:
        # Generate DALL-E image
        result = image_generator.generate_image(
            prompt=request.text,
            style="dalle",
            size="1024x1024"
        )
        
        # Transform the response to match frontend expectations
        visual_post = {
            "id": f"dalle_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "text": request.text,
            "period": request.period,
            "tags": request.tags or [],
            "period_color": get_period_color(request.period),
            "image_style": "dalle",
            "post_format": request.post_format,
            "file_path": result.get("image_path", ""),
            "file_url": result.get("image_url", ""),  # This is the key field frontend expects
            "background_image": {
                "id": "ai_generated",
                "photographer": "DALL-E AI",
                "pexels_url": ""
            },
            "created_at": datetime.now().isoformat(),
            "dimensions": {
                "width": 1024,
                "height": 1024
            }
        }
        
        # Save metadata - this is required for the visual posts to show up in the list
        if result.get("success") and result.get("image_path"):
            metadata_path = result['image_path'].replace('.jpg', '_metadata.json').replace('.png', '_metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump({
                    "text": request.text,
                    "period": request.period,
                    "tags": request.tags or [],
                    "image_style": "dalle",
                    "post_format": request.post_format,
                    "created_at": datetime.now().isoformat(),
                    "background_image": visual_post["background_image"],
                    "dimensions": visual_post["dimensions"],
                    "file_path": result.get("image_path", ""),
                    "file_url": result.get("image_url", "")
                }, f, indent=2)
        
        return {
            "success": True,
            "message": "DALL-E visual post created successfully",
            "visual_post": visual_post
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-instagram-ai-image")
async def create_instagram_ai_image(request: InstagramAIImageRequest):
    # Implementation would go here
    # This is a placeholder showing the structure
    pass

@router.get("/visual-posts")
async def get_visual_posts(
    period: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get visual posts (requires authentication)"""
    # Try to use visual post creator agent if available
    visual_post_creator = get_agent('visual_post_creator')
    if visual_post_creator and hasattr(visual_post_creator, 'get_visual_posts_by_period'):
        # Set context on agent
        if hasattr(visual_post_creator, 'set_context'):
            context = RequestContext(
                user_id=current_user.id,
                organization_id=current_user.default_organization_id
            )
            visual_post_creator.set_context(context)
        
        # Get posts from agent
        result = visual_post_creator.get_visual_posts_by_period(period)
        if result.get('success', False):
            return result
    
    # Fallback to file system
    # Use the static/generated directory where images are actually saved
    generated_dir = os.path.join("static", "generated")
    
    # Add debug logging
    print(f"\n{'='*60}")
    print(f"Visual Posts Listing")
    print(f"Looking in directory: {generated_dir}")
    print(f"Directory exists: {os.path.exists(generated_dir)}")
    
    if not os.path.exists(generated_dir):
        print(f"Directory does not exist, returning empty list")
        print(f"{'='*60}\n")
        return {"success": True, "posts": []}
    
    posts = []
    files = os.listdir(generated_dir)
    print(f"Files in directory: {len(files)}")
    
    for filename in files:
        if filename.endswith('_metadata.json'):
            print(f"Found metadata file: {filename}")
            metadata_path = os.path.join(generated_dir, filename)
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Filter by period if specified
                if period and metadata.get('period') != period:
                    continue
                
                image_filename = filename.replace('_metadata.json', '.jpg')
                if not os.path.exists(os.path.join(generated_dir, image_filename)):
                    image_filename = filename.replace('_metadata.json', '.png')
                
                post_id = filename.replace('_metadata.json', '')
                
                # Use the file_url from metadata if available, otherwise construct it
                file_url = metadata.get('file_url', f"/static/generated/{image_filename}")
                
                posts.append({
                    "id": post_id,
                    "text": metadata.get('text', ''),
                    "period": metadata.get('period', ''),
                    "tags": metadata.get('tags', []),
                    "period_color": get_period_color(metadata.get('period', '')),
                    "image_style": metadata.get('image_style', 'minimal'),
                    "post_format": metadata.get('post_format', 'post'),
                    "file_path": metadata.get('file_path', os.path.join(generated_dir, image_filename)),
                    "file_url": file_url,
                    "background_image": metadata.get('background_image', {}),
                    "created_at": metadata.get('created_at', ''),
                    "dimensions": metadata.get('dimensions', {"width": 1080, "height": 1350})
                })
                print(f"Added post with id: {post_id}, file_url: {file_url}")
            except Exception as e:
                print(f"Error reading metadata file {filename}: {e}")
    
    # Sort by creation date, newest first
    posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    print(f"Total posts found: {len(posts)}")
    print(f"{'='*60}\n")
    
    return {
        "success": True,
        "posts": posts,
        "count": len(posts)
    }

@router.delete("/visual-posts/{post_id}")
async def delete_visual_post(
    post_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a visual post (requires authentication)"""
    generated_dir = os.path.join("static", "generated")
    
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
        "success": True,
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