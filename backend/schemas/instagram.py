from pydantic import BaseModel
from typing import Dict, Any, Optional, List

class InstagramPostRequest(BaseModel):
    affirmation: str
    period_name: str
    style: Optional[str] = "inspirational"

class InstagramAIImageRequest(BaseModel):
    text: str
    period: str
    tags: Optional[List[str]] = []
    image_style: Optional[str] = "inspirational"
    post_format: Optional[str] = "post"
    affirmation_id: Optional[str] = None
    source: Optional[str] = None
    instagram_post_text: Optional[str] = None
    instagram_hashtags: Optional[str] = None
    instagram_cta: Optional[str] = None
    instagram_style: Optional[str] = "inspirational"

class InstagramPostingRequest(BaseModel):
    instagram_post_id: str
    visual_post_id: Optional[str] = None
    post_type: Optional[str] = "feed_post"  # "feed_post" or "story"
    schedule_time: Optional[str] = None  # ISO format datetime for scheduling

class InstagramContentPrepareRequest(BaseModel):
    instagram_post_id: str
    visual_post_id: Optional[str] = None

class InstagramAnalyzeRequest(BaseModel):
    account_url_or_username: str
    analysis_focus: Optional[str] = "comprehensive"

class InstagramStrategyRequest(BaseModel):
    analysis_id: str
    target_niche: Optional[str] = "7cycles"
    account_stage: Optional[str] = "starting"

class InstagramMultipleAnalyzeRequest(BaseModel):
    account_list: List[str]
    analysis_focus: Optional[str] = "comprehensive"

class InstagramReelRequest(BaseModel):
    instagram_text: str
    period: str
    additional_input: Optional[str] = ""
    image_paths: Optional[List[str]] = None
    image_descriptions: Optional[List[str]] = None
    force_new: Optional[bool] = False
    provider: Optional[str] = "runway"  # "runway" or "sora"
    loop_style: Optional[str] = "seamless"  # For Sora videos