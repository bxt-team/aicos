from fastapi import APIRouter, HTTPException
from app.models.instagram import (
    InstagramPostRequest, 
    InstagramPostingRequest,
    InstagramContentPrepareRequest,
    InstagramAnalyzeRequest,
    InstagramStrategyRequest,
    InstagramMultipleAnalyzeRequest
)
from app.core.dependencies import get_agent
from app.core.config import settings
from datetime import datetime
import json
import os
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Instagram"])

@router.post("/generate-instagram-post")
async def generate_instagram_post(request: InstagramPostRequest):
    write_hashtag_agent = get_agent('write_hashtag_agent')
    if not write_hashtag_agent:
        raise HTTPException(status_code=503, detail="Instagram Agent not initialized")
    
    try:
        # Generate Instagram post
        result = write_hashtag_agent.generate_instagram_post(
            affirmation=request.affirmation,
            period_name=request.period_name,
            style=request.style
        )
        
        # Check if generation was successful
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate Instagram post"))
        
        # Extract the post data
        post_data = result.get("post", {})
        
        # The agent already stores the post, just return it
        return {
            "status": "success",
            "instagram_post": post_data,
            "message": result.get('message', 'Instagram post generated successfully')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instagram-posts")
async def get_instagram_posts(period_name: str = None):
    write_hashtag_agent = get_agent('write_hashtag_agent')
    if not write_hashtag_agent:
        return {"status": "success", "posts": []}
    
    try:
        result = write_hashtag_agent.get_generated_posts(period_name)
        
        if not result.get("success", False):
            return {"status": "success", "posts": []}
        
        posts = result.get("posts", [])
        
        # Sort by creation date, newest first
        posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "status": "success",
            "posts": posts,
            "count": len(posts)
        }
    except Exception as e:
        logger.error(f"Error retrieving Instagram posts: {e}")
        return {"status": "success", "posts": []}

@router.post("/post-to-instagram")
async def post_to_instagram(request: InstagramPostingRequest):
    instagram_poster_agent = get_agent('instagram_poster_agent')
    if not instagram_poster_agent:
        raise HTTPException(status_code=503, detail="Instagram Poster Agent not initialized")
    
    try:
        # Get Instagram post from agent
        write_hashtag_agent = get_agent('write_hashtag_agent')
        if not write_hashtag_agent:
            raise HTTPException(status_code=503, detail="Write Hashtag Agent not initialized")
        
        result = write_hashtag_agent.get_generated_posts()
        posts = result.get("posts", [])
        
        # Find the specific post by ID
        instagram_post = None
        for post in posts:
            if post.get("id") == request.instagram_post_id:
                instagram_post = post
                break
        
        if not instagram_post:
            raise HTTPException(status_code=404, detail="Instagram post not found")
        
        # Load visual post data if provided
        visual_post = None
        if request.visual_post_id:
            # Logic to load visual post
            pass
        
        # Post to Instagram
        result = instagram_poster_agent.post_to_instagram(
            post_text=instagram_post['post_text'],
            hashtags=instagram_post['hashtags'],
            image_path=visual_post['file_path'] if visual_post else None,
            post_type=request.post_type,
            schedule_time=request.schedule_time
        )
        
        # Save posting history
        history_dir = "storage/instagram_posting_history"
        os.makedirs(history_dir, exist_ok=True)
        
        history_id = str(uuid.uuid4())
        with open(f"{history_dir}/{history_id}.json", 'w') as f:
            json.dump({
                "id": history_id,
                "instagram_post_id": request.instagram_post_id,
                "visual_post_id": request.visual_post_id,
                "posted_at": datetime.now().isoformat(),
                "instagram_media_id": result.get('media_id'),
                "status": result.get('status'),
                "result": result
            }, f, indent=2)
        
        return {
            "status": "success",
            "message": "Posted to Instagram successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/analyze-instagram-account")
async def analyze_instagram_account(request: InstagramAnalyzeRequest):
    instagram_analyzer_agent = get_agent('instagram_analyzer_agent')
    if not instagram_analyzer_agent:
        raise HTTPException(status_code=503, detail="Instagram Analyzer Agent not initialized")
    
    try:
        analysis = instagram_analyzer_agent.analyze_account(
            account_url_or_username=request.account_url_or_username,
            analysis_focus=request.analysis_focus
        )
        
        # Save analysis
        analysis_dir = "storage/instagram_analyses"
        os.makedirs(analysis_dir, exist_ok=True)
        
        analysis_id = str(uuid.uuid4())
        with open(f"{analysis_dir}/{analysis_id}.json", 'w') as f:
            json.dump({
                "id": analysis_id,
                "account": request.account_url_or_username,
                "analysis": analysis,
                "created_at": datetime.now().isoformat()
            }, f, indent=2)
        
        return {
            "status": "success",
            "analysis_id": analysis_id,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prepare-instagram-content")
async def prepare_instagram_content(request: InstagramContentPrepareRequest):
    """Prepare Instagram content for posting"""
    try:
        # Get Instagram post from agent
        write_hashtag_agent = get_agent('write_hashtag_agent')
        if not write_hashtag_agent:
            raise HTTPException(status_code=503, detail="Write Hashtag Agent not initialized")
        
        result = write_hashtag_agent.get_generated_posts()
        posts = result.get("posts", [])
        
        # Find the specific post by ID
        instagram_post = None
        for post in posts:
            if post.get("id") == request.instagram_post_id:
                instagram_post = post
                break
        
        if not instagram_post:
            raise HTTPException(status_code=404, detail="Instagram post not found")
        
        # Load visual post data if provided
        visual_post = None
        if request.visual_post_id:
            visual_posts_file = "static/visual_posts_storage.json"
            if os.path.exists(visual_posts_file):
                with open(visual_posts_file, 'r') as f:
                    visual_posts_data = json.load(f)
                    visual_post = visual_posts_data.get("posts", {}).get(request.visual_post_id)
        
        # Prepare content preview
        preview = {
            "post_text": instagram_post['post_text'],
            "hashtags": instagram_post['hashtags'],
            "call_to_action": instagram_post.get('call_to_action', ''),
            "image_url": visual_post.get('file_path') if visual_post else None,
            "period": instagram_post.get('period_name'),
            "ready_to_post": bool(visual_post)
        }
        
        return {
            "status": "success",
            "preview": preview,
            "instagram_post": instagram_post,
            "visual_post": visual_post
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-visual-from-instagram-post")
async def create_visual_from_instagram_post(request: dict):
    """Create a visual post from an Instagram post"""
    instagram_ai_prompt_agent = get_agent('instagram_ai_prompt_agent')
    if not instagram_ai_prompt_agent:
        raise HTTPException(status_code=503, detail="Instagram AI Prompt Agent not initialized")
    
    try:
        instagram_post_id = request.get("instagram_post_id")
        if not instagram_post_id:
            raise HTTPException(status_code=400, detail="instagram_post_id is required")
        
        # Get Instagram post from agent
        write_hashtag_agent = get_agent('write_hashtag_agent')
        if not write_hashtag_agent:
            raise HTTPException(status_code=503, detail="Write Hashtag Agent not initialized")
        
        result = write_hashtag_agent.get_generated_posts()
        posts = result.get("posts", [])
        
        # Find the specific post by ID
        instagram_post = None
        for post in posts:
            if post.get("id") == instagram_post_id:
                instagram_post = post
                break
        
        if not instagram_post:
            raise HTTPException(status_code=404, detail="Instagram post not found")
        
        # Generate AI prompt for visual creation
        ai_prompt_result = instagram_ai_prompt_agent.generate_ai_prompt(
            text=instagram_post['affirmation'],
            period=instagram_post['period_name'],
            tags=[],
            image_style="inspirational",
            post_format="post"
        )
        
        return {
            "status": "success",
            "ai_prompt": ai_prompt_result,
            "instagram_post": instagram_post,
            "message": "Use this AI prompt to create a visual post"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/instagram-posting-status")
async def get_instagram_posting_status():
    """Get current Instagram posting status"""
    instagram_poster_agent = get_agent('instagram_poster_agent')
    if not instagram_poster_agent:
        return {
            "status": "error",
            "message": "Instagram posting not configured",
            "configured": False
        }
    
    # Check if Instagram credentials are valid
    validation = instagram_poster_agent.validate_instagram_credentials()
    
    return {
        "status": "success",
        "configured": validation["success"],
        "account_info": validation.get("account_info") if validation["success"] else None,
        "error": validation.get("error") if not validation["success"] else None
    }

@router.get("/instagram-posting-history")
async def get_instagram_posting_history():
    """Get Instagram posting history"""
    history_dir = "storage/instagram_posting_history"
    
    if not os.path.exists(history_dir):
        return {"status": "success", "history": []}
    
    history = []
    
    for filename in os.listdir(history_dir):
        if filename.endswith('.json'):
            with open(os.path.join(history_dir, filename), 'r', encoding='utf-8') as f:
                post_history = json.load(f)
                history.append(post_history)
    
    # Sort by posting date, newest first
    history.sort(key=lambda x: x.get('posted_at', ''), reverse=True)
    
    return {
        "status": "success",
        "history": history,
        "count": len(history)
    }

@router.get("/api/instagram-analyses")
async def get_instagram_analyses():
    """Get all Instagram analyses"""
    analysis_dir = "storage/instagram_analyses"
    
    if not os.path.exists(analysis_dir):
        return {"status": "success", "analyses": []}
    
    analyses = []
    
    for filename in os.listdir(analysis_dir):
        if filename.endswith('.json'):
            with open(os.path.join(analysis_dir, filename), 'r', encoding='utf-8') as f:
                analysis = json.load(f)
                analyses.append(analysis)
    
    # Sort by creation date, newest first
    analyses.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return {
        "status": "success",
        "analyses": analyses,
        "count": len(analyses)
    }

@router.get("/api/reel-themes")
async def get_reel_themes():
    """Get available Instagram Reel themes"""
    return {
        "themes": [
            {
                "id": "motivational",
                "name": "Motivational",
                "description": "Inspiring and uplifting content",
                "music_style": "upbeat",
                "visual_style": "dynamic"
            },
            {
                "id": "peaceful",
                "name": "Peaceful",
                "description": "Calm and serene content",
                "music_style": "ambient",
                "visual_style": "smooth"
            },
            {
                "id": "energetic",
                "name": "Energetic",
                "description": "High energy and exciting content",
                "music_style": "electronic",
                "visual_style": "fast-paced"
            },
            {
                "id": "spiritual",
                "name": "Spiritual",
                "description": "Deep and contemplative content",
                "music_style": "meditative",
                "visual_style": "ethereal"
            },
            {
                "id": "educational",
                "name": "Educational",
                "description": "Informative and teaching content",
                "music_style": "minimal",
                "visual_style": "clean"
            }
        ]
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