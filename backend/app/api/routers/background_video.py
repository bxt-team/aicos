"""
Background video generation endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.dependencies import get_agent

router = APIRouter(prefix="/api", tags=["background-video"])


class BackgroundVideoRequest(BaseModel):
    period: str
    duration: Optional[int] = 5  # 5 or 10 seconds
    custom_prompt: Optional[str] = None


class VideoStatusRequest(BaseModel):
    video_id: str


@router.post("/generate-background-video")
async def generate_background_video(request: BackgroundVideoRequest):
    """Generate a short background video for reels"""
    print(f"[API] Received background video request: period={request.period}, duration={request.duration}, custom_prompt={request.custom_prompt}")
    
    background_video_agent = get_agent('background_video_agent')
    if not background_video_agent:
        print("[API] ERROR: Background video agent not available")
        raise HTTPException(status_code=503, detail="Background video agent not available")
    
    print("[API] Agent found, calling generate_background_video...")
    result = background_video_agent.generate_background_video(
        period=request.period,
        duration=request.duration,
        custom_prompt=request.custom_prompt,
        async_mode=True  # Always use async mode for better user experience
    )
    
    print(f"[API] Agent returned: success={result.get('success')}, message={result.get('message')}")
    
    if not result.get("success"):
        print(f"[API] Returning 400 error: {result.get('message')}")
        raise HTTPException(
            status_code=400, 
            detail=result.get("message", "Failed to generate background video")
        )
    
    print("[API] Returning successful result")
    return result


@router.get("/background-videos")
async def get_background_videos(period: Optional[str] = None):
    """Get all or period-specific background videos"""
    background_video_agent = get_agent('background_video_agent')
    if not background_video_agent:
        raise HTTPException(status_code=503, detail="Background video agent not available")
    
    return background_video_agent.get_background_videos(period)


@router.delete("/background-videos/{video_id}")
async def delete_background_video(video_id: str):
    """Delete a background video"""
    background_video_agent = get_agent('background_video_agent')
    if not background_video_agent:
        raise HTTPException(status_code=503, detail="Background video agent not available")
    
    result = background_video_agent.delete_background_video(video_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Background video not found")
    
    return result


@router.get("/background-video-status/{task_id}")
async def get_video_task_status(task_id: str):
    """Check the status of a video generation task"""
    background_video_agent = get_agent('background_video_agent')
    if not background_video_agent:
        raise HTTPException(status_code=503, detail="Background video agent not available")
    
    result = background_video_agent.check_video_task_status(task_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message", "Task not found"))
    
    return result

@router.post("/background-video-status")
async def get_video_status(request: VideoStatusRequest):
    """Check the status of a video generation job"""
    background_video_agent = get_agent('background_video_agent')
    if not background_video_agent:
        raise HTTPException(status_code=503, detail="Background video agent not available")
    
    return background_video_agent.get_video_generation_status(request.video_id)


@router.get("/background-video-themes")
async def get_video_themes():
    """Get available themes for background videos"""
    return {
        "themes": {
            "Image": {
                "keywords": "golden light, sunburst, radiant glow",
                "mood": "inspiring",
                "description": "Goldenes Licht und strahlende Energie"
            },
            "Veränderung": {
                "keywords": "flowing water, transformation, blue waves",
                "mood": "dynamic",
                "description": "Fließende Transformation und Wandel"
            },
            "Energie": {
                "keywords": "fire, lightning, red energy burst",
                "mood": "powerful",
                "description": "Kraftvolle Energie und Dynamik"
            },
            "Kreativität": {
                "keywords": "paint splash, colorful abstract, yellow burst",
                "mood": "creative",
                "description": "Kreative Explosion und Farbenspiel"
            },
            "Erfolg": {
                "keywords": "sparkling lights, celebration, magenta glow",
                "mood": "triumphant",
                "description": "Erfolg und festlicher Glanz"
            },
            "Entspannung": {
                "keywords": "calm water, green nature, peaceful clouds",
                "mood": "relaxing",
                "description": "Ruhe und natürliche Harmonie"
            },
            "Umsicht": {
                "keywords": "purple mist, cosmic space, gentle stars",
                "mood": "contemplative",
                "description": "Weisheit und kosmische Verbindung"
            }
        },
        "duration_options": [5, 10],
        "format": "9:16 (vertical for reels)"
    }