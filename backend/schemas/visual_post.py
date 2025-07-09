from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class DALLEVisualPostRequest(BaseModel):
    text: str
    period: str
    tags: Optional[List[str]] = []
    image_style: str = "dalle"
    post_format: Optional[str] = "post"
    ai_context: Optional[str] = None
    force_new: Optional[bool] = True

class ImageFeedbackRequest(BaseModel):
    imagePath: str
    rating: int
    comments: Optional[str] = ""
    generationParams: Optional[Dict[str, Any]] = None
    userId: Optional[str] = None
    tags: Optional[List[str]] = []

class RegenerateWithFeedbackRequest(BaseModel):
    originalImagePath: str
    feedback: str
    rating: int
    originalPrompt: Optional[str] = None
    generationParams: Optional[Dict[str, Any]] = None
    keepOriginalStyle: Optional[bool] = True

class PostCompositionRequest(BaseModel):
    background_path: str
    text: str
    period: str
    template_name: Optional[str] = "default"
    post_format: Optional[str] = "story"
    custom_options: Optional[Dict[str, Any]] = None
    force_new: Optional[bool] = False

class IntegratedPostCompositionRequest(BaseModel):
    instagram_post_id: str
    visual_post_id: str
    template_name: Optional[str] = "default"
    post_format: Optional[str] = "story"
    custom_options: Optional[Dict[str, Any]] = None