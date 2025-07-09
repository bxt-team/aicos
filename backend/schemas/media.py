from pydantic import BaseModel
from typing import Dict, Any, Optional, List

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