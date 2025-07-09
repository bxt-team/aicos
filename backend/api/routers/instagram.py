from fastapi import APIRouter, HTTPException
from schemas.instagram import (
    InstagramPostRequest, 
    InstagramPostingRequest,
    InstagramContentPrepareRequest,
    InstagramAnalyzeRequest,
    InstagramStrategyRequest,
    InstagramMultipleAnalyzeRequest
)
from core.dependencies import (
    write_hashtag_agent, 
    instagram_ai_prompt_agent,
    instagram_poster_agent,
    instagram_analyzer_agent
)
from core.config import settings
from datetime import datetime
import json
import os
import uuid

router = APIRouter(prefix="/instagram", tags=["Instagram"])

# Storage for Instagram posts
os.makedirs("storage/instagram_posts", exist_ok=True)

@router.post("/generate-post")
async def generate_instagram_post(request: InstagramPostRequest):
    if not write_hashtag_agent:
        raise HTTPException(status_code=503, detail="Instagram Agent not initialized")
    
    try:
        # Generate Instagram post
        result = write_hashtag_agent.generate_instagram_post(
            affirmation=request.affirmation,
            period_name=request.period_name,
            style=request.style
        )
        
        # Save the post
        post_id = str(uuid.uuid4())
        filename = f"storage/instagram_posts/{post_id}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "id": post_id,
                "affirmation": request.affirmation,
                "period_name": request.period_name,
                "style": request.style,
                "post_text": result['post_text'],
                "hashtags": result['hashtags'],
                "call_to_action": result['call_to_action'],
                "period_color": get_period_color(request.period_name),
                "created_at": datetime.now().isoformat(),
                "source": "manual_generation"
            }, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "instagram_post": {
                "id": post_id,
                **result,
                "period_color": get_period_color(request.period_name)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posts")
async def get_instagram_posts():
    posts_dir = "storage/instagram_posts"
    
    if not os.path.exists(posts_dir):
        return {"status": "success", "posts": []}
    
    posts = []
    
    for filename in os.listdir(posts_dir):
        if filename.endswith('.json'):
            with open(os.path.join(posts_dir, filename), 'r', encoding='utf-8') as f:
                post = json.load(f)
                posts.append(post)
    
    # Sort by creation date, newest first
    posts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    return {
        "status": "success",
        "posts": posts,
        "count": len(posts)
    }

@router.post("/post")
async def post_to_instagram(request: InstagramPostingRequest):
    if not instagram_poster_agent:
        raise HTTPException(status_code=503, detail="Instagram Poster Agent not initialized")
    
    try:
        # Load Instagram post data
        post_path = f"storage/instagram_posts/{request.instagram_post_id}.json"
        if not os.path.exists(post_path):
            raise HTTPException(status_code=404, detail="Instagram post not found")
        
        with open(post_path, 'r', encoding='utf-8') as f:
            instagram_post = json.load(f)
        
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

@router.post("/analyze-account")
async def analyze_instagram_account(request: InstagramAnalyzeRequest):
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