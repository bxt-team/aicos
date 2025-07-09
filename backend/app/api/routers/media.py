"""
Media processing endpoints for voice, video, and captions
"""
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any, List, Optional
import os
import tempfile
import shutil
from pydantic import BaseModel

from app.core.dependencies import get_agent

router = APIRouter(prefix="/api", tags=["media"])

# Request models
class VoiceOverRequest(BaseModel):
    text: str
    voice: Optional[str] = "bella"
    language: Optional[str] = "en"
    model: Optional[str] = "eleven_multilingual_v2"
    output_format: Optional[str] = "mp3_44100_128"

class VoiceScriptRequest(BaseModel):
    video_content: str
    target_duration: Optional[int] = 30
    style: Optional[str] = "conversational"
    period: Optional[str] = None

class CaptionRequest(BaseModel):
    audio_path: str
    language: Optional[str] = "en"
    style: Optional[str] = "minimal"
    max_chars_per_line: Optional[int] = 40

class AddVoiceToVideoRequest(BaseModel):
    video_path: str
    audio_path: str
    volume: Optional[float] = 1.0
    fade_in: Optional[float] = 0.5
    fade_out: Optional[float] = 0.5

class AddCaptionsToVideoRequest(BaseModel):
    video_path: str
    subtitle_path: str
    burn_in: Optional[bool] = True
    style: Optional[str] = "minimal"

class ProcessVideoRequest(BaseModel):
    video_path: str
    script_text: str
    voice: Optional[str] = "bella"
    language: Optional[str] = "en"
    caption_style: Optional[str] = "minimal"
    burn_in_captions: Optional[bool] = True

class VideoGenerationRequest(BaseModel):
    image_paths: List[str]
    video_type: Optional[str] = "slideshow"
    duration: Optional[int] = 15
    fps: Optional[int] = 30
    options: Optional[Dict[str, Any]] = None
    force_new: Optional[bool] = False

class InstagramReelRequest(BaseModel):
    instagram_text: str
    period: str
    additional_input: Optional[str] = ""
    image_paths: Optional[List[str]] = None
    image_descriptions: Optional[List[str]] = None
    force_new: Optional[bool] = False
    provider: Optional[str] = "runway"  # "runway" or "sora"
    loop_style: Optional[str] = "seamless"  # For Sora videos

# Voice endpoints
@router.post("/generate-voice-script")
async def generate_voice_script(request: VoiceScriptRequest):
    """Generate a voice-over script for video content"""
    voice_over_agent = get_agent('voice_over_agent')
    if not voice_over_agent:
        raise HTTPException(status_code=503, detail="Voice over agent not available")
    
    result = voice_over_agent.generate_voice_script(
        request.video_content,
        request.target_duration,
        request.style,
        request.period
    )
    
    return result

@router.post("/generate-voice-over")
async def generate_voice_over(request: VoiceOverRequest):
    """Generate voice-over audio from text"""
    voice_over_agent = get_agent('voice_over_agent')
    if not voice_over_agent:
        raise HTTPException(status_code=503, detail="Voice over agent not available")
    
    result = voice_over_agent.generate_voice_over(
        request.text,
        request.voice,
        request.language,
        request.model,
        request.output_format
    )
    
    return result

@router.get("/available-voices")
async def get_available_voices():
    """Get list of available voice options"""
    voice_over_agent = get_agent('voice_over_agent')
    if not voice_over_agent:
        raise HTTPException(status_code=503, detail="Voice over agent not available")
    
    return voice_over_agent.get_available_voices()

@router.get("/voice-overs")
async def list_voice_overs():
    """List all generated voice-overs"""
    voice_over_agent = get_agent('voice_over_agent')
    if not voice_over_agent:
        raise HTTPException(status_code=503, detail="Voice over agent not available")
    
    return voice_over_agent.list_voice_overs()

# Caption endpoints
@router.post("/generate-captions")
async def generate_captions(request: CaptionRequest):
    """Generate captions from audio file"""
    voice_over_agent = get_agent('voice_over_agent')
    if not voice_over_agent:
        raise HTTPException(status_code=503, detail="Voice over agent not available")
    
    result = voice_over_agent.generate_captions(
        request.audio_path,
        request.language,
        request.style,
        request.max_chars_per_line
    )
    
    return result

@router.get("/caption-styles")
async def get_caption_styles():
    """Get available caption style options"""
    return {
        "styles": [
            {
                "id": "minimal",
                "name": "Minimal",
                "description": "Clean, simple captions"
            },
            {
                "id": "bold",
                "name": "Bold",
                "description": "Large, impactful captions"
            },
            {
                "id": "gradient",
                "name": "Gradient",
                "description": "Colorful gradient captions"
            },
            {
                "id": "animated",
                "name": "Animated",
                "description": "Animated word-by-word captions"
            }
        ]
    }

# Video processing endpoints
@router.post("/add-voice-to-video")
async def add_voice_to_video(request: AddVoiceToVideoRequest):
    """Add voice-over audio to video"""
    voice_over_agent = get_agent('voice_over_agent')
    if not voice_over_agent:
        raise HTTPException(status_code=503, detail="Voice over agent not available")
    
    result = voice_over_agent.add_voice_to_video(
        request.video_path,
        request.audio_path,
        request.volume,
        request.fade_in,
        request.fade_out
    )
    
    return result

@router.post("/add-captions-to-video")
async def add_captions_to_video(request: AddCaptionsToVideoRequest):
    """Add captions to video"""
    voice_over_agent = get_agent('voice_over_agent')
    if not voice_over_agent:
        raise HTTPException(status_code=503, detail="Voice over agent not available")
    
    result = voice_over_agent.add_captions_to_video(
        request.video_path,
        request.subtitle_path,
        request.burn_in,
        request.style
    )
    
    return result

@router.post("/process-video-with-voice-and-captions")
async def process_video_with_voice_and_captions(request: ProcessVideoRequest):
    """Process video with voice-over and captions in one step"""
    voice_over_agent = get_agent('voice_over_agent')
    if not voice_over_agent:
        raise HTTPException(status_code=503, detail="Voice over agent not available")
    
    result = voice_over_agent.process_video_complete(
        request.video_path,
        request.script_text,
        request.voice,
        request.language,
        request.caption_style,
        request.burn_in_captions
    )
    
    return result

# Video generation endpoints
@router.post("/generate-video")
async def generate_video(request: VideoGenerationRequest):
    """Generate video from images"""
    video_generation_agent = get_agent('video_generation_agent')
    if not video_generation_agent:
        raise HTTPException(status_code=503, detail="Video generation agent not available")
    
    result = video_generation_agent.generate_video(
        request.image_paths,
        request.video_type,
        request.duration,
        request.fps,
        request.options,
        request.force_new
    )
    
    return result

@router.get("/videos")
async def list_videos():
    """List all generated videos"""
    video_generation_agent = get_agent('video_generation_agent')
    if not video_generation_agent:
        raise HTTPException(status_code=503, detail="Video generation agent not available")
    
    return video_generation_agent.list_videos()

@router.get("/video-types")
async def get_video_types():
    """Get available video generation types"""
    return {
        "types": [
            {
                "id": "slideshow",
                "name": "Slideshow",
                "description": "Simple slideshow with transitions"
            },
            {
                "id": "ken_burns",
                "name": "Ken Burns Effect",
                "description": "Zoom and pan effects on images"
            },
            {
                "id": "parallax",
                "name": "Parallax",
                "description": "3D parallax effect"
            },
            {
                "id": "morphing",
                "name": "Morphing",
                "description": "Smooth morphing between images"
            }
        ]
    }

# Instagram Reel endpoints
@router.post("/api/generate-instagram-reel")
async def generate_instagram_reel(request: InstagramReelRequest):
    """Generate Instagram Reel video"""
    instagram_reel_agent = get_agent('instagram_reel_agent')
    if not instagram_reel_agent:
        raise HTTPException(status_code=503, detail="Instagram Reel agent not available")
    
    result = instagram_reel_agent.generate_reel(
        request.instagram_text,
        request.period,
        request.additional_input,
        request.image_paths,
        request.image_descriptions,
        request.force_new,
        request.provider
    )
    
    return result

@router.get("/video-providers")
async def get_video_providers():
    """Get available video generation providers"""
    return {
        "providers": [
            {
                "id": "runway",
                "name": "Runway ML",
                "description": "High-quality AI video generation",
                "features": ["image_to_video", "text_to_video", "video_editing"]
            },
            {
                "id": "sora",
                "name": "OpenAI Sora",
                "description": "Advanced AI video generation",
                "features": ["text_to_video", "seamless_loops", "long_form"]
            }
        ]
    }

@router.get("/loop-styles")
async def get_loop_styles():
    """Get available loop styles for video generation"""
    return {
        "styles": [
            {
                "id": "seamless",
                "name": "Seamless Loop",
                "description": "Perfect loop with no visible cut"
            },
            {
                "id": "fade",
                "name": "Fade Loop",
                "description": "Fade transition at loop point"
            },
            {
                "id": "bounce",
                "name": "Bounce Loop",
                "description": "Forward then reverse playback"
            }
        ]
    }