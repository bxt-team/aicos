from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import json
import asyncio
import subprocess
import tempfile
import shutil
from datetime import datetime
import sys
import traceback
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.flows.content_generation_wrapper import ContentGenerationWrapper
from src.tools.image_generator import ImageGenerator
from src.agents.qa_agent import QAAgent
from src.agents.affirmations_agent import AffirmationsAgent
from src.agents.write_hashtag_research_agent import WriteHashtagResearchAgent
from src.agents.instagram_ai_prompt_agent import InstagramAIPromptAgent
from src.agents.instagram_poster_agent import InstagramPosterAgent
from src.agents.instagram_analyzer_agent import InstagramAnalyzerAgent
from src.agents.content_workflow_agent import ContentWorkflowAgent
from src.agents.post_composition_agent import PostCompositionAgent
from src.agents.video_generation_agent import VideoGenerationAgent
from src.agents.instagram_reel_agent import InstagramReelAgent
from src.agents.android_testing_agent import AndroidTestingAgent
from src.agents.voice_over_agent import VoiceOverAgent
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for agents
content_storage = {}
image_generator = None
qa_agent = None
affirmations_agent = None
write_hashtag_agent = None
instagram_ai_prompt_agent = None
instagram_poster_agent = None
instagram_analyzer_agent = None
content_wrapper = None
workflow_agent = None
post_composition_agent = None
video_generation_agent = None
instagram_reel_agent = None
android_testing_agent = None
voice_over_agent = None

# Lifespan context manager for startup and shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global image_generator, qa_agent, affirmations_agent, write_hashtag_agent, instagram_ai_prompt_agent, instagram_poster_agent, instagram_analyzer_agent, content_wrapper, workflow_agent, post_composition_agent, video_generation_agent, instagram_reel_agent, android_testing_agent, voice_over_agent
    openai_api_key = os.getenv("OPENAI_API_KEY")
    pexels_api_key = os.getenv("PEXELS_API_KEY")
    instagram_access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
    instagram_business_account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
    
    if openai_api_key:
        image_generator = ImageGenerator(openai_api_key)
        qa_agent = QAAgent(openai_api_key)
        affirmations_agent = AffirmationsAgent(openai_api_key)
        write_hashtag_agent = WriteHashtagResearchAgent(openai_api_key)
        instagram_ai_prompt_agent = InstagramAIPromptAgent(openai_api_key)
        instagram_poster_agent = InstagramPosterAgent(openai_api_key, instagram_access_token, instagram_business_account_id)
        instagram_analyzer_agent = InstagramAnalyzerAgent(openai_api_key)
        content_wrapper = ContentGenerationWrapper()
        
        # Initialize new agents
        workflow_agent = ContentWorkflowAgent(openai_api_key, pexels_api_key, instagram_access_token)
        post_composition_agent = PostCompositionAgent(openai_api_key)
        video_generation_agent = VideoGenerationAgent(openai_api_key)
        instagram_reel_agent = InstagramReelAgent(openai_api_key, os.getenv('RUNWAY_API_KEY'))
        
        # Initialize Voice Over agent
        elevenlabs_api_key = os.getenv('ELEVENLABS_API_KEY')
        voice_over_agent = VoiceOverAgent(openai_api_key, elevenlabs_api_key)
        
        # Initialize Android testing agent
        adb_path = os.getenv('ADB_PATH', 'adb')  # Allow custom ADB path
        logger.info(f"Initializing AndroidTestingAgent with adb_path: {adb_path}")
        try:
            android_testing_agent = AndroidTestingAgent(openai_api_key, adb_path)
            logger.info(f"AndroidTestingAgent initialized successfully: {android_testing_agent is not None}")
        except Exception as e:
            logger.error(f"Failed to initialize AndroidTestingAgent: {str(e)}")
            logger.error(f"AndroidTestingAgent initialization traceback: {traceback.format_exc()}")
            android_testing_agent = None
        
        print(f"InstagramReelAgent initialized: {instagram_reel_agent is not None}")
        print(f"AndroidTestingAgent initialized: {android_testing_agent is not None}")
        
        print("Successfully initialized all agents")
        
        # Validate Instagram credentials
        if instagram_access_token and instagram_business_account_id:
            validation = instagram_poster_agent.validate_instagram_credentials()
            if validation["success"]:
                print(f"Instagram API validated: {validation['account_info'].get('username', 'Unknown')}")
            else:
                print(f"Instagram API validation failed: {validation['error']}")
        else:
            print("Instagram API credentials not configured - posting features will be disabled")
    else:
        print("Warning: OPENAI_API_KEY not found. All AI features will be disabled.")
    
    # Yield control to the application
    yield
    
    # Cleanup code (executed on shutdown)
    print("Shutting down 7 Cycles of Life AI Assistant API...")
    # Add any cleanup code here if needed

# Initialize FastAPI app with lifespan
app = FastAPI(title="7 Cycles of Life AI Assistant API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    if request.url.path.startswith("/api/android-test"):
        logger.info(f"Android-test route detected: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

# Create static directory if it doesn't exist
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "generated"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "android_screenshots"), exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

class ContentRequest(BaseModel):
    knowledge_files: Optional[List[str]] = None
    style_preferences: Optional[Dict[str, str]] = None

class ApprovalRequest(BaseModel):
    content_id: str
    approved: bool
    feedback: Optional[str] = None

class ContentResponse(BaseModel):
    content_id: str
    research_results: str
    written_content: str
    visual_concepts: str
    images: List[Dict[str, Any]]
    status: str
    created_at: str

class QuestionRequest(BaseModel):
    question: str

class AffirmationRequest(BaseModel):
    period_name: str
    period_info: Optional[Dict[str, Any]] = {}
    count: Optional[int] = 5

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

class DALLEVisualPostRequest(BaseModel):
    text: str
    period: str
    tags: Optional[List[str]] = []
    image_style: str = "dalle"
    post_format: Optional[str] = "post"
    ai_context: Optional[str] = None
    force_new: Optional[bool] = True

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

# New workflow-related request models
class WorkflowCreateRequest(BaseModel):
    period: str
    workflow_type: Optional[str] = "full"
    options: Optional[Dict[str, Any]] = None

class InstagramReelRequest(BaseModel):
    instagram_text: str
    period: str
    additional_input: Optional[str] = ""
    image_paths: Optional[List[str]] = None
    image_descriptions: Optional[List[str]] = None
    force_new: Optional[bool] = False
    provider: Optional[str] = "runway"  # "runway" or "sora"
    loop_style: Optional[str] = "seamless"  # For Sora videos

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

class VideoGenerationRequest(BaseModel):
    image_paths: List[str]
    video_type: Optional[str] = "slideshow"
    duration: Optional[int] = 15
    fps: Optional[int] = 30
    options: Optional[Dict[str, Any]] = None
    force_new: Optional[bool] = False

class AndroidTestRequest(BaseModel):
    apk_path: str
    test_actions: Optional[List[str]] = None
    target_api_level: Optional[int] = None
    avd_name: Optional[str] = None

class AndroidTestResultRequest(BaseModel):
    test_id: str

@app.get("/")
async def root():
    return {"message": "7 Cycles of Life AI Assistant API", "version": "1.0.0"}

@app.post("/generate-content")
async def generate_content(request: ContentRequest, background_tasks: BackgroundTasks):
    """Generate Instagram content using CrewAI flow"""
    try:
        content_id = f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        content_storage[content_id] = {
            "status": "generating",
            "created_at": datetime.now().isoformat(),
            "request": request.dict()
        }
        
        background_tasks.add_task(run_content_generation, content_id)
        
        return {
            "content_id": content_id,
            "status": "started",
            "message": "Content generation started. Check status with /content/{content_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start content generation: {str(e)}")

async def run_content_generation(content_id: str):
    """Background task to run content generation"""
    import asyncio
    import concurrent.futures
    
    try:
        content_storage[content_id]["status"] = "generating_text"
        content_storage[content_id]["last_updated"] = datetime.now().isoformat()
        
        # Run the synchronous CrewAI wrapper in a thread pool to avoid event loop conflicts
        with concurrent.futures.ThreadPoolExecutor() as executor:
            wrapper = ContentGenerationWrapper()
            future = executor.submit(wrapper.run_sequential_generation)
            result = await asyncio.get_event_loop().run_in_executor(None, future.result)
        
        if not result["success"]:
            content_storage[content_id]["status"] = "failed"
            content_storage[content_id]["error"] = result["error"]
            return
        
        flow_data = result["data"]
        
        content_storage[content_id]["research_results"] = str(flow_data.get("research_results", ""))
        content_storage[content_id]["written_content"] = str(flow_data.get("written_content", ""))
        content_storage[content_id]["visual_concepts"] = str(flow_data.get("visual_concepts", ""))
        
        # Explicitly update status to generating_images before starting image generation
        if image_generator:
            content_storage[content_id]["status"] = "generating_images"
            content_storage[content_id]["last_updated"] = datetime.now().isoformat()
            print(f"Status updated to: generating_images for {content_id}")  # Debug log
            
            image_results = image_generator.create_instagram_post_images(
                content_storage[content_id]["visual_concepts"]
            )
            
            if image_results["success"]:
                content_storage[content_id]["images"] = image_results["results"]
            else:
                content_storage[content_id]["images"] = []
                content_storage[content_id]["image_error"] = image_results["error"]
        else:
            content_storage[content_id]["images"] = []
            content_storage[content_id]["image_error"] = "Image generation disabled - no API key"
        
        content_storage[content_id]["status"] = "completed"
        content_storage[content_id]["completed_at"] = datetime.now().isoformat()
        
    except Exception as e:
        content_storage[content_id]["status"] = "failed"
        content_storage[content_id]["error"] = str(e)
        content_storage[content_id]["traceback"] = traceback.format_exc()

@app.get("/content/{content_id}")
async def get_content(content_id: str):
    """Get content generation status and results"""
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content = content_storage[content_id]
    
    return {
        "content_id": content_id,
        "status": content["status"],
        "created_at": content["created_at"],
        "last_updated": content.get("last_updated"),
        "research_results": content.get("research_results", ""),
        "written_content": content.get("written_content", ""),
        "visual_concepts": content.get("visual_concepts", ""),
        "images": content.get("images", []),
        "error": content.get("error"),
        "image_error": content.get("image_error"),
        "completed_at": content.get("completed_at")
    }

@app.post("/approve-content")
async def approve_content(request: ApprovalRequest):
    """Approve or reject generated content"""
    if request.content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content = content_storage[request.content_id]
    content["approval_status"] = "approved" if request.approved else "rejected"
    content["feedback"] = request.feedback
    content["approved_at"] = datetime.now().isoformat()
    
    return {
        "content_id": request.content_id,
        "approval_status": content["approval_status"],
        "message": "Content approval recorded"
    }

@app.get("/content")
async def list_content():
    """List all generated content"""
    return {
        "content": [
            {
                "content_id": content_id,
                "status": content["status"],
                "created_at": content["created_at"],
                "approval_status": content.get("approval_status"),
                "has_images": len(content.get("images", [])) > 0
            }
            for content_id, content in content_storage.items()
        ]
    }

@app.delete("/content/{content_id}")
async def delete_content(content_id: str):
    """Delete generated content"""
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content = content_storage[content_id]
    
    if "images" in content:
        for image in content["images"]:
            if "image_path" in image and os.path.exists(image["image_path"]):
                try:
                    os.remove(image["image_path"])
                except Exception as e:
                    print(f"Failed to delete image file: {e}")
    
    del content_storage[content_id]
    
    return {"message": "Content deleted successfully"}

@app.post("/ask-question")
async def ask_question(request: QuestionRequest):
    """Ask a question about the 7 Cycles of Life"""
    try:
        if not qa_agent:
            raise HTTPException(status_code=503, detail="Q&A agent not available")
        
        result = qa_agent.answer_question(request.question)
        
        if result["success"]:
            return {
                "success": True,
                "question": request.question,
                "answer": result["answer"],
                "context_preview": result.get("context_used", "")
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.get("/qa-health")
async def qa_health_check():
    """Simple health check for Q&A agent"""
    try:
        if not qa_agent:
            raise HTTPException(status_code=503, detail="Q&A agent not available")
        
        # Simple check if vector store is loaded
        if qa_agent.vector_store:
            return {
                "status": "healthy",
                "message": "Q&A agent is ready"
            }
        else:
            raise HTTPException(status_code=503, detail="Knowledge base not loaded")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/knowledge-overview")
async def get_knowledge_overview():
    """Get an overview of the knowledge base"""
    try:
        if not qa_agent:
            raise HTTPException(status_code=503, detail="Q&A agent not available")
        
        result = qa_agent.get_knowledge_overview()
        
        if result["success"]:
            return {
                "success": True,
                "overview": result["overview"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting knowledge overview: {str(e)}")

@app.post("/generate-affirmations")
async def generate_affirmations(request: AffirmationRequest):
    """Generate affirmations for a specific period"""
    try:
        if not affirmations_agent:
            raise HTTPException(status_code=503, detail="Affirmations agent not available")
        
        result = affirmations_agent.generate_affirmations(
            request.period_name, 
            request.period_info, 
            request.count
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating affirmations: {str(e)}")

@app.get("/affirmations")
async def get_affirmations(period_name: Optional[str] = None):
    """Get all affirmations, optionally filtered by period type"""
    try:
        if not affirmations_agent:
            raise HTTPException(status_code=503, detail="Affirmations agent not available")
        
        result = affirmations_agent.get_affirmations_by_period(period_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting affirmations: {str(e)}")

@app.get("/periods")
async def get_available_periods():
    """Get information about available period types"""
    try:
        if not affirmations_agent:
            raise HTTPException(status_code=503, detail="Affirmations agent not available")
        
        return affirmations_agent.get_available_periods()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting periods: {str(e)}")

# Visual Posts API Endpoints

@app.post("/search-images")
async def search_images(request: dict):
    """Search for background images using the ImageSearchAgent"""
    try:
        tags = request.get("tags", [])
        period = request.get("period", "")
        count = request.get("count", 5)
        
        if not tags or not period:
            raise HTTPException(status_code=400, detail="Tags and period are required")
        
        # Initialize image search agent
        from src.agents.image_search_agent import ImageSearchAgent
        pexels_key = os.getenv('PEXELS_API_KEY')
        
        if not pexels_key:
            raise HTTPException(status_code=503, detail="Pexels API key not configured")
        
        image_agent = ImageSearchAgent(os.getenv("OPENAI_API_KEY"), pexels_key)
        result = image_agent.search_images(tags, period, count)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching images: {str(e)}")

@app.post("/create-visual-post")
async def create_visual_post(request: dict):
    """Create a visual affirmation post"""
    try:
        text = request.get("text", "")
        period = request.get("period", "")
        tags = request.get("tags", [])
        image_style = request.get("image_style", "minimal")
        post_format = request.get("post_format", "post")
        force_new = request.get("force_new", False)
        
        if not text or not period:
            raise HTTPException(status_code=400, detail="Text and period are required")
        
        if not tags:
            tags = ["inspiration", "motivation", "peaceful"]
        
        # Initialize visual post creator agent
        from src.agents.visual_post_creator_agent import VisualPostCreatorAgent
        pexels_key = os.getenv('PEXELS_API_KEY')
        
        if not pexels_key:
            raise HTTPException(status_code=503, detail="Pexels API key not configured")
        
        # Since VisualPostCreatorAgent now only handles image finding, we need to use both agents
        visual_agent = VisualPostCreatorAgent(os.getenv("OPENAI_API_KEY"), pexels_key)
        
        # First, find background images
        image_result = visual_agent.find_background_image(tags, period, image_style, count=1)
        
        if not image_result["success"] or not image_result["images"]:
            raise HTTPException(status_code=500, detail="Failed to find background images")
        
        # Get the first image
        background_image = image_result["images"][0]
        
        # Now compose the post
        if not post_composition_agent:
            raise HTTPException(status_code=503, detail="Post composition agent not available")
        
        result = post_composition_agent.compose_post(
            background_path=background_image["local_path"],
            text=text,
            period=period,
            template_name=image_style,  # Use image_style as template name
            post_format=post_format,
            force_new=force_new
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating visual post: {str(e)}")

@app.get("/visual-posts")
async def get_visual_posts(period: str = None):
    """Get all visual posts, optionally filtered by period"""
    try:
        # Read from visual_posts_storage.json (original Visual Posts Creator data)
        visual_posts_storage_path = os.path.join(static_dir, "visual_posts_storage.json")
        
        if not os.path.exists(visual_posts_storage_path):
            return {
                "success": True,
                "posts": [],
                "count": 0,
                "period": period
            }
        
        with open(visual_posts_storage_path, 'r') as f:
            visual_data = json.load(f)
        
        # Handle both old format (array) and new format (object with posts key)
        if isinstance(visual_data, dict):
            posts = visual_data.get("posts", [])
        elif isinstance(visual_data, list):
            posts = visual_data
        else:
            posts = []
        
        # Filter by period if provided
        if period:
            posts = [post for post in posts if post.get("period") == period]
        
        return {
            "success": True,
            "posts": posts,
            "count": len(posts),
            "period": period
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting visual posts: {str(e)}")

@app.delete("/visual-posts/{post_id}")
async def delete_visual_post(post_id: str):
    """Delete a visual post"""
    try:
        if not post_composition_agent:
            raise HTTPException(status_code=503, detail="Post composition agent not available")
        
        result = post_composition_agent.delete_composed_post(post_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting visual post: {str(e)}")

@app.post("/create-affirmation-post")
async def create_affirmation_post(request: dict):
    """Create visual post directly from existing affirmation"""
    try:
        affirmation_id = request.get("affirmation_id", "")
        image_style = request.get("image_style", "minimal")
        post_format = request.get("post_format", "post")
        custom_tags = request.get("tags", [])
        force_new = request.get("force_new", False)
        
        if not affirmation_id:
            raise HTTPException(status_code=400, detail="Affirmation ID is required")
        
        # Get affirmation from storage
        if not affirmations_agent:
            raise HTTPException(status_code=503, detail="Affirmations agent not available")
        
        affirmations_result = affirmations_agent.get_affirmations_by_period()
        
        if not affirmations_result["success"]:
            raise HTTPException(status_code=500, detail="Error getting affirmations")
        
        # Find the specific affirmation
        affirmation = None
        for aff in affirmations_result["affirmations"]:
            if aff["id"] == affirmation_id:
                affirmation = aff
                break
        
        if not affirmation:
            raise HTTPException(status_code=404, detail="Affirmation not found")
        
        # Generate tags based on period and text
        tags = custom_tags if custom_tags else []
        if not tags:
            # Default tags based on period
            period_tags = {
                "Image": ["portrait", "confidence", "mirror", "self"],
                "Veränderung": ["transformation", "change", "growth", "new"],
                "Energie": ["energy", "power", "vitality", "strength"],
                "Kreativität": ["creative", "art", "inspiration", "colorful"],
                "Erfolg": ["success", "achievement", "goal", "victory"],
                "Entspannung": ["peace", "calm", "meditation", "nature"],
                "Umsicht": ["wisdom", "thoughtful", "planning", "contemplation"]
            }
            tags = period_tags.get(affirmation["period_name"], ["inspiration", "motivation"])
        
        # Create visual post using the new architecture
        pexels_key = os.getenv('PEXELS_API_KEY')
        
        if not pexels_key:
            raise HTTPException(status_code=503, detail="Pexels API key not configured")
        
        # Find background image
        visual_agent = VisualPostCreatorAgent(os.getenv("OPENAI_API_KEY"), pexels_key)
        image_result = visual_agent.find_background_image(tags, affirmation["period_name"], image_style, count=1)
        
        if not image_result["success"] or not image_result["images"]:
            raise HTTPException(status_code=500, detail="Failed to find background images")
        
        # Get the first image
        background_image = image_result["images"][0]
        
        # Compose the post
        if not post_composition_agent:
            raise HTTPException(status_code=503, detail="Post composition agent not available")
        
        result = post_composition_agent.compose_post(
            background_path=background_image["local_path"],
            text=affirmation["text"],
            period=affirmation["period_name"],
            template_name=image_style,
            post_format=post_format,
            force_new=force_new
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating affirmation post: {str(e)}")

# Write and Hashtag Research Agent endpoints

@app.post("/generate-instagram-post")
async def generate_instagram_post(request: InstagramPostRequest):
    """Generate an Instagram post with hashtags and call-to-action"""
    try:
        if not write_hashtag_agent:
            raise HTTPException(status_code=503, detail="Write and Hashtag Research agent not available")
        
        result = write_hashtag_agent.generate_instagram_post(
            request.affirmation,
            request.period_name,
            request.style
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating Instagram post: {str(e)}")

@app.post("/create-visual-from-instagram-post")
async def create_visual_from_instagram_post(request: dict):
    """Create a visual post from an existing Instagram post"""
    try:
        # Extract data from Instagram post
        instagram_post_id = request.get("instagram_post_id")
        instagram_post = request.get("instagram_post", {})
        
        # Get required fields from Instagram post
        affirmation = instagram_post.get("affirmation", "")
        period_name = instagram_post.get("period_name", "")
        period_color = instagram_post.get("period_color", "")
        
        # Optional parameters
        image_style = request.get("image_style", "minimal")
        custom_tags = request.get("custom_tags", [])
        force_new = request.get("force_new", False)
        
        if not affirmation or not period_name:
            raise HTTPException(status_code=400, detail="Affirmation and period_name are required")
        
        # Generate smart tags based on period and content
        tags = custom_tags if custom_tags else []
        if not tags:
            # Default tags based on period
            period_tags = {
                "Image": ["self-reflection", "identity", "golden", "authentic"],
                "Veränderung": ["transformation", "change", "blue", "growth"],
                "Energie": ["vitality", "power", "red", "dynamic"],
                "Kreativität": ["creative", "inspiration", "yellow", "artistic"],
                "Erfolg": ["success", "achievement", "magenta", "goals"],
                "Entspannung": ["relaxation", "peace", "green", "calm"],
                "Umsicht": ["wisdom", "thoughtful", "purple", "mindful"]
            }
            tags = period_tags.get(period_name, ["inspiration", "motivation", "peaceful"])
        
        # Create visual post using the new architecture
        pexels_key = os.getenv('PEXELS_API_KEY')
        
        if not pexels_key:
            raise HTTPException(status_code=503, detail="Pexels API key not configured")
        
        # Find background image
        visual_agent = VisualPostCreatorAgent(os.getenv("OPENAI_API_KEY"), pexels_key)
        image_result = visual_agent.find_background_image(tags, period_name, image_style, count=1)
        
        if not image_result["success"] or not image_result["images"]:
            raise HTTPException(status_code=500, detail="Failed to find background images")
        
        # Get the first image
        background_image = image_result["images"][0]
        
        # Compose the post
        if not post_composition_agent:
            raise HTTPException(status_code=503, detail="Post composition agent not available")
        
        result = post_composition_agent.compose_post(
            background_path=background_image["local_path"],
            text=affirmation,
            period=period_name,
            template_name=image_style,
            post_format="post",  # Default to post format
            force_new=force_new
        )
        
        # Add reference to original Instagram post
        if result.get("success"):
            result["post"]["instagram_post_id"] = instagram_post_id
            result["post"]["source"] = "instagram_integration"
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating visual post from Instagram post: {str(e)}")

@app.get("/instagram-posts")
async def get_instagram_posts(period_name: Optional[str] = None):
    """Get all Instagram posts, optionally filtered by period"""
    try:
        if not write_hashtag_agent:
            raise HTTPException(status_code=503, detail="Write and Hashtag Research agent not available")
        
        result = write_hashtag_agent.get_generated_posts(period_name)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting Instagram posts: {str(e)}")

@app.post("/create-instagram-ai-image")
async def create_instagram_ai_image(request: InstagramAIImageRequest):
    """Create an AI-generated image based on complete Instagram post data"""
    try:
        if not instagram_ai_prompt_agent:
            raise HTTPException(status_code=503, detail="Instagram AI Prompt agent not available")
        
        # Prepare Instagram post data
        instagram_post_data = {
            "text": request.text,
            "period": request.period,
            "tags": request.tags,
            "image_style": request.image_style,
            "post_format": request.post_format,
            "affirmation_id": request.affirmation_id,
            "source": request.source,
            "instagram_post_text": request.instagram_post_text,
            "instagram_hashtags": request.instagram_hashtags,
            "instagram_cta": request.instagram_cta,
            "instagram_style": request.instagram_style
        }
        
        result = instagram_ai_prompt_agent.generate_ai_image_from_instagram_post(
            instagram_post_data=instagram_post_data,
            post_format=request.post_format,
            image_style=request.image_style
        )
        
        if result["success"]:
            # Create visual post from the generated AI image
            visual_post_data = {
                "text": request.text,
                "period": request.period,
                "tags": request.tags,
                "image_style": request.image_style,
                "post_format": request.post_format,
                "ai_image_data": result["image"]
            }
            
            # Create visual post from AI image
            visual_post_result = content_wrapper.create_visual_post_from_ai_image(visual_post_data)
            
            if visual_post_result["success"]:
                return {
                    "success": True,
                    "message": "AI-generierter visueller Post erstellt",
                    "ai_image": result["image"],
                    "visual_post": visual_post_result["post"]
                }
            else:
                return result  # Return just the AI image if visual post creation fails
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating Instagram AI image: {str(e)}")

@app.post("/create-dalle-visual-post")
async def create_dalle_visual_post(request: DALLEVisualPostRequest):
    """Create a visual post using DALL-E AI image generation"""
    try:
        if not instagram_ai_prompt_agent:
            raise HTTPException(status_code=503, detail="Instagram AI Prompt agent not available")
        
        # Prepare data for AI image generation
        instagram_post_data = {
            "text": request.text,
            "period": request.period,
            "tags": request.tags,
            "image_style": request.image_style,
            "post_format": request.post_format,
            "source": "manual_dalle",
            "instagram_post_text": request.ai_context or request.text,
            "instagram_hashtags": "",
            "instagram_cta": "",
            "instagram_style": "inspirational"
        }
        
        # Generate AI image
        result = instagram_ai_prompt_agent.generate_ai_image_from_instagram_post(
            instagram_post_data=instagram_post_data,
            post_format=request.post_format,
            image_style="inspirational"
        )
        
        if result["success"]:
            # Convert the AI image result to visual post format
            ai_image = result["image"]
            
            # Create visual post entry
            import hashlib
            post_id = hashlib.md5(f"{request.text}_{request.period}_dalle".encode()).hexdigest()
            
            visual_post_data = {
                "id": post_id,
                "text": request.text,
                "period": request.period,
                "tags": request.tags or [],
                "period_color": ai_image.get("period_color", "#667eea"),
                "image_style": "dalle",
                "post_format": request.post_format,
                "file_path": ai_image.get("image_path", ""),
                "file_url": f"/static/generated/{os.path.basename(ai_image.get('image_path', ''))}" if ai_image.get("image_path") else "",
                "background_image": {
                    "id": "dalle_generated",
                    "photographer": "DALL-E AI",
                    "pexels_url": ""
                },
                "created_at": datetime.now().isoformat(),
                "dimensions": {
                    "width": 1024,
                    "height": 1024
                },
                "ai_prompt": ai_image.get("dalle_prompt", ""),
                "ai_generated": True
            }
            
            # Save to visual posts storage
            visual_posts_storage_path = os.path.join(os.path.dirname(__file__), "..", "static", "visual_posts_storage.json")
            visual_storage = {"posts": [], "by_period": {}}
            
            if os.path.exists(visual_posts_storage_path):
                with open(visual_posts_storage_path, 'r') as f:
                    visual_storage = json.load(f)
            
            # Ensure the required keys exist
            if "posts" not in visual_storage:
                visual_storage["posts"] = []
            if "by_period" not in visual_storage:
                visual_storage["by_period"] = {}
            
            visual_storage["posts"].append(visual_post_data)
            visual_storage["by_period"][post_id] = visual_post_data
            
            os.makedirs(os.path.dirname(visual_posts_storage_path), exist_ok=True)
            with open(visual_posts_storage_path, 'w') as f:
                json.dump(visual_storage, f, indent=2)
            
            return {
                "success": True,
                "post": visual_post_data,
                "source": "dalle_generated",
                "message": f"DALL-E visueller Post für {request.period} erfolgreich erstellt"
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating DALL-E visual post: {str(e)}")

@app.post("/prepare-instagram-content")
async def prepare_instagram_content(request: InstagramContentPrepareRequest):
    """Prepare Instagram content for posting (optimize text, hashtags, etc.)"""
    try:
        if not instagram_poster_agent:
            raise HTTPException(status_code=503, detail="Instagram Poster agent not available")
        
        # Load Instagram post data
        if not write_hashtag_agent:
            raise HTTPException(status_code=503, detail="Write and Hashtag Research agent not available")
        
        instagram_posts = write_hashtag_agent.get_generated_posts()
        if not instagram_posts["success"]:
            raise HTTPException(status_code=500, detail="Failed to load Instagram posts")
        
        # Find the specific Instagram post
        instagram_post = None
        for post in instagram_posts["posts"]:
            if post["id"] == request.instagram_post_id:
                instagram_post = post
                break
        
        if not instagram_post:
            raise HTTPException(status_code=404, detail="Instagram post not found")
        
        # Load visual post data if provided
        visual_post = None
        if request.visual_post_id:
            # For now, we'll load from the visual posts storage
            # This would be better implemented with a proper visual posts service
            visual_posts_storage_path = os.path.join(os.path.dirname(__file__), "..", "static", "visual_posts_storage.json")
            if os.path.exists(visual_posts_storage_path):
                with open(visual_posts_storage_path, 'r') as f:
                    visual_data = json.load(f)
                    visual_posts = visual_data.get("posts", [])
                    for vpost in visual_posts:
                        if vpost.get("id") == request.visual_post_id:
                            visual_post = vpost
                            break
        
        # Prepare content for posting
        result = instagram_poster_agent.prepare_post_content(instagram_post, visual_post)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preparing Instagram content: {str(e)}")

@app.post("/post-to-instagram")
async def post_to_instagram(request: InstagramPostingRequest):
    """Post complete content to Instagram (combining text and visual)"""
    try:
        if not instagram_poster_agent:
            raise HTTPException(status_code=503, detail="Instagram Poster agent not available")
        
        result = instagram_poster_agent.post_complete_content(
            instagram_post_id=request.instagram_post_id,
            visual_post_id=request.visual_post_id,
            post_type=request.post_type,
            schedule_time=request.schedule_time
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error posting to Instagram: {str(e)}")

@app.get("/instagram-posting-status")
async def get_instagram_posting_status():
    """Get Instagram posting status and rate limiting info"""
    try:
        if not instagram_poster_agent:
            raise HTTPException(status_code=503, detail="Instagram Poster agent not available")
        
        result = instagram_poster_agent.get_posting_status()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting posting status: {str(e)}")

@app.get("/instagram-posting-history")
async def get_instagram_posting_history(limit: int = 50):
    """Get Instagram posting history"""
    try:
        if not instagram_poster_agent:
            raise HTTPException(status_code=503, detail="Instagram Poster agent not available")
        
        result = instagram_poster_agent.get_posting_history(limit)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting posting history: {str(e)}")

# Instagram Analyzer Agent endpoints

@app.post("/api/analyze-instagram-account")
async def analyze_instagram_account(request: InstagramAnalyzeRequest):
    """Analyze a successful Instagram account for strategy insights"""
    try:
        if not instagram_analyzer_agent:
            raise HTTPException(status_code=503, detail="Instagram Analyzer agent not available")
        
        result = instagram_analyzer_agent.analyze_instagram_account(
            account_url_or_username=request.account_url_or_username,
            analysis_focus=request.analysis_focus
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing Instagram account: {str(e)}")

@app.post("/api/generate-strategy-from-analysis")
async def generate_strategy_from_analysis(request: InstagramStrategyRequest):
    """Generate an actionable Instagram strategy based on analysis"""
    try:
        if not instagram_analyzer_agent:
            raise HTTPException(status_code=503, detail="Instagram Analyzer agent not available")
        
        result = instagram_analyzer_agent.generate_strategy_from_analysis(
            analysis_id=request.analysis_id,
            target_niche=request.target_niche,
            account_stage=request.account_stage
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating strategy: {str(e)}")

@app.post("/api/analyze-multiple-accounts")
async def analyze_multiple_accounts(request: InstagramMultipleAnalyzeRequest):
    """Analyze multiple Instagram accounts and create comparative insights"""
    try:
        if not instagram_analyzer_agent:
            raise HTTPException(status_code=503, detail="Instagram Analyzer agent not available")
        
        result = instagram_analyzer_agent.analyze_multiple_accounts(
            account_list=request.account_list,
            analysis_focus=request.analysis_focus
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing multiple accounts: {str(e)}")

@app.get("/api/instagram-analyses")
async def get_instagram_analyses(account_username: Optional[str] = None):
    """Get stored Instagram analyses, optionally filtered by account"""
    try:
        if not instagram_analyzer_agent:
            raise HTTPException(status_code=503, detail="Instagram Analyzer agent not available")
        
        result = instagram_analyzer_agent.get_stored_analyses(account_username)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting analyses: {str(e)}")

@app.get("/instagram-strategy/{strategy_id}")
async def get_instagram_strategy(strategy_id: str):
    """Get a specific Instagram strategy by ID"""
    try:
        if not instagram_analyzer_agent:
            raise HTTPException(status_code=503, detail="Instagram Analyzer agent not available")
        
        result = instagram_analyzer_agent.get_strategy_by_id(strategy_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting strategy: {str(e)}")

# Image Feedback API endpoints

@app.post("/api/submit-feedback")
async def submit_image_feedback(request: ImageFeedbackRequest):
    """Submit feedback for a generated image"""
    try:
        if not image_generator:
            raise HTTPException(status_code=503, detail="Image generator not available")
        
        # Add feedback to the system
        feedback_id = image_generator.add_feedback(
            image_path=request.imagePath,
            rating=request.rating,
            comments=request.comments,
            generation_params=request.generationParams,
            user_id=request.userId,
            tags=request.tags
        )
        
        return {
            "success": True,
            "feedback_id": feedback_id,
            "message": "Feedback submitted successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@app.get("/api/feedback-analytics")
async def get_feedback_analytics():
    """Get comprehensive feedback analytics"""
    try:
        if not image_generator:
            raise HTTPException(status_code=503, detail="Image generator not available")
        
        analytics = image_generator.get_feedback_analytics()
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting feedback analytics: {str(e)}")

@app.get("/api/feedback-recommendations")
async def get_feedback_recommendations():
    """Get optimization recommendations based on feedback"""
    try:
        if not image_generator:
            raise HTTPException(status_code=503, detail="Image generator not available")
        
        recommendations = image_generator.get_optimization_recommendations()
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

@app.get("/api/image-feedback/{image_path:path}")
async def get_image_feedback(image_path: str):
    """Get feedback for a specific image"""
    try:
        if not image_generator:
            raise HTTPException(status_code=503, detail="Image generator not available")
        
        feedback = image_generator.get_feedback_for_image(image_path)
        
        if feedback:
            return {
                "success": True,
                "feedback": feedback
            }
        else:
            return {
                "success": False,
                "message": "No feedback found for this image"
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting image feedback: {str(e)}")

@app.post("/api/regenerate-with-feedback")
async def regenerate_image_with_feedback(request: RegenerateWithFeedbackRequest):
    """Regenerate an image based on user feedback with optimized prompt"""
    try:
        if not image_generator:
            raise HTTPException(status_code=503, detail="Image generator not available")
        
        # First, submit the feedback to improve the system
        feedback_id = image_generator.add_feedback(
            image_path=request.originalImagePath,
            rating=request.rating,
            comments=request.feedback,
            generation_params=request.generationParams
        )
        
        # Get the original visual post data to understand context
        visual_posts_file = os.path.join(static_dir, "visual_posts_storage.json")
        original_post_data = None
        
        # First try to find in visual posts storage
        if os.path.exists(visual_posts_file):
            with open(visual_posts_file, 'r', encoding='utf-8') as f:
                visual_posts = json.load(f)
                # Find the original post by image path
                for post in visual_posts:
                    if isinstance(post, dict):
                        post_file_path = post.get('file_path', '')
                        if post_file_path == request.originalImagePath or request.originalImagePath in post_file_path:
                            original_post_data = post
                            break
        
        # If not found in visual posts, try to reconstruct from feedback data
        if not original_post_data:
            # Try to find feedback with flexible path matching
            feedback_entries = None
            all_feedback = image_generator.feedback_collector.get_all_feedback()
            
            # Extract filename from the requested path
            requested_filename = os.path.basename(request.originalImagePath)
            
            for entry in all_feedback:
                entry_path = entry.get('image_path', '')
                entry_filename = os.path.basename(entry_path)
                
                # Match by exact path or filename
                if (entry_path == request.originalImagePath or 
                    entry_filename == requested_filename or
                    requested_filename in entry_path):
                    feedback_entries = entry
                    break
            
            if feedback_entries:
                # Use the generation params from the feedback
                generation_params = feedback_entries.get('generation_params', {})
                if generation_params:
                    original_post_data = {
                        'file_path': request.originalImagePath,
                        'text': generation_params.get('text', ''),
                        'period': generation_params.get('period', ''),
                        'tags': generation_params.get('tags', []),
                        'period_color': '',
                        'image_style': generation_params.get('style', 'dalle'),
                        'post_format': generation_params.get('post_format', 'post'),
                        'dalle_prompt': generation_params.get('ai_prompt', ''),
                        'ai_prompt': generation_params.get('ai_prompt', ''),
                        'ai_generated': generation_params.get('ai_generated', True)
                    }
        
        if not original_post_data:
            # Debug information for troubleshooting
            debug_info = {
                "requested_path": request.originalImagePath,
                "visual_posts_file_exists": os.path.exists(visual_posts_file),
                "feedback_entries_count": len(image_generator.feedback_collector.get_all_feedback()),
                "available_feedback_paths": [entry.get('image_path', '') for entry in image_generator.feedback_collector.get_all_feedback()]
            }
            raise HTTPException(status_code=404, detail=f"Original image data not found. Debug info: {debug_info}")
        
        # Create optimized prompt based on feedback and original data
        original_prompt = request.originalPrompt or original_post_data.get('dalle_prompt', '') or original_post_data.get('ai_prompt', '')
        
        # Use the image generator's prompt optimizer with feedback
        optimized_prompt = image_generator.optimize_prompt_with_feedback(
            original_prompt=original_prompt,
            feedback=request.feedback,
            rating=request.rating,
            style=original_post_data.get('image_style', 'dalle'),
            period=original_post_data.get('period', ''),
            existing_generation_params=request.generationParams
        )
        
        # Generate new image with optimized prompt
        generation_result = image_generator.generate_image(
            prompt=optimized_prompt,
            style=original_post_data.get('image_style', 'natural') if request.keepOriginalStyle else 'natural',
            use_feedback_optimization=True
        )
        
        if not generation_result.get('success', False):
            raise HTTPException(status_code=500, detail=generation_result.get('error', 'Failed to generate image'))
        
        # Create new visual post entry
        new_post = {
            "id": f"regenerated_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "text": original_post_data.get('text', ''),
            "period": original_post_data.get('period', ''),
            "tags": original_post_data.get('tags', []),
            "period_color": original_post_data.get('period_color', ''),
            "image_style": original_post_data.get('image_style', 'dalle'),
            "post_format": original_post_data.get('post_format', 'post'),
            "file_path": generation_result['image_path'],
            "file_url": generation_result['image_url'],
            "dalle_prompt": optimized_prompt,
            "ai_prompt": optimized_prompt,  # Also add ai_prompt for consistency
            "original_image_path": request.originalImagePath,
            "feedback_used": request.feedback,
            "optimization_applied": True,
            "ai_generated": True,
            "created_at": datetime.now().isoformat(),
            "dimensions": {"width": 1024, "height": 1024}
        }
        
        # Save the new post to storage
        if os.path.exists(visual_posts_file):
            try:
                with open(visual_posts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Handle both old format (array) and new format (object with posts key)
                    if isinstance(data, dict) and "posts" in data:
                        visual_posts = data["posts"]
                    elif isinstance(data, list):
                        visual_posts = data
                    else:
                        visual_posts = []
            except (json.JSONDecodeError, FileNotFoundError):
                visual_posts = []
        else:
            visual_posts = []
        
        visual_posts.append(new_post)
        
        # Save in the correct format expected by the get_visual_posts endpoint
        visual_posts_data = {
            "posts": visual_posts,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(visual_posts_file, 'w', encoding='utf-8') as f:
            json.dump(visual_posts_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "message": "Image regenerated successfully with feedback optimization",
            "visual_post": new_post,
            "feedback_id": feedback_id,
            "original_prompt": original_prompt,
            "optimized_prompt": optimized_prompt,
            "optimization_details": {
                "feedback_applied": request.feedback,
                "rating_considered": request.rating,
                "style_preserved": request.keepOriginalStyle
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating image with feedback: {str(e)}")

# Workflow Management API endpoints

@app.post("/api/workflows")
async def create_workflow(request: WorkflowCreateRequest, background_tasks: BackgroundTasks):
    """Create and execute a complete content workflow"""
    try:
        if not workflow_agent:
            raise HTTPException(status_code=503, detail="Workflow agent not available")
        
        # Start workflow execution in background
        workflow_id = f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Store initial workflow state
        content_storage[workflow_id] = {
            "type": "workflow",
            "status": "starting",
            "period": request.period,
            "workflow_type": request.workflow_type,
            "options": request.options or {},
            "created_at": datetime.now().isoformat()
        }
        
        background_tasks.add_task(run_workflow_execution, workflow_id, request.period, request.workflow_type, request.options or {})
        
        return {
            "workflow_id": workflow_id,
            "status": "started",
            "message": f"Workflow für {request.period} gestartet"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")

async def run_workflow_execution(workflow_id: str, period: str, workflow_type: str, options: Dict[str, Any]):
    """Background task to run workflow execution"""
    import asyncio
    import concurrent.futures
    
    try:
        content_storage[workflow_id]["status"] = "executing"
        content_storage[workflow_id]["last_updated"] = datetime.now().isoformat()
        
        # Run the workflow in a thread pool
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(
                workflow_agent.create_complete_content_workflow,
                period, workflow_type, options
            )
            result = await asyncio.get_event_loop().run_in_executor(None, future.result)
        
        if result["success"]:
            content_storage[workflow_id].update({
                "status": "completed",
                "workflow_result": result,
                "completed_at": datetime.now().isoformat()
            })
        else:
            content_storage[workflow_id].update({
                "status": "failed",
                "error": result.get("error", "Unknown error"),
                "failed_at": datetime.now().isoformat()
            })
        
    except Exception as e:
        content_storage[workflow_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

@app.get("/api/workflows")
async def list_workflows(period: Optional[str] = None, status: Optional[str] = None):
    """List all workflows with optional filtering"""
    try:
        if not workflow_agent:
            raise HTTPException(status_code=503, detail="Workflow agent not available")
        
        result = workflow_agent.get_workflows(period, status)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing workflows: {str(e)}")

@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get workflow details and status"""
    try:
        # Check if it's in content_storage (for running workflows)
        if workflow_id in content_storage and content_storage[workflow_id].get("type") == "workflow":
            return {
                "workflow_id": workflow_id,
                **content_storage[workflow_id]
            }
        
        # Check completed workflows
        if not workflow_agent:
            raise HTTPException(status_code=503, detail="Workflow agent not available")
        
        result = workflow_agent.get_workflow_by_id(workflow_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=404, detail="Workflow not found")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow: {str(e)}")

@app.delete("/api/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    try:
        if not workflow_agent:
            raise HTTPException(status_code=503, detail="Workflow agent not available")
        
        # Remove from content_storage if present
        if workflow_id in content_storage:
            del content_storage[workflow_id]
        
        result = workflow_agent.delete_workflow(workflow_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting workflow: {str(e)}")

@app.get("/api/workflow-templates")
async def get_workflow_templates():
    """Get available workflow templates"""
    try:
        if not workflow_agent:
            raise HTTPException(status_code=503, detail="Workflow agent not available")
        
        result = workflow_agent.get_workflow_templates()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting workflow templates: {str(e)}")

# Post Composition API endpoints

@app.post("/api/compose-post")
async def compose_post(request: PostCompositionRequest):
    """Compose a visual post using templates"""
    try:
        if not post_composition_agent:
            raise HTTPException(status_code=503, detail="Post composition agent not available")
        
        result = post_composition_agent.compose_post(
            background_path=request.background_path,
            text=request.text,
            period=request.period,
            template_name=request.template_name,
            post_format=request.post_format,
            custom_options=request.custom_options or {},
            force_new=request.force_new
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error composing post: {str(e)}")

@app.get("/api/composed-posts")
async def get_composed_posts(period: Optional[str] = None, template: Optional[str] = None):
    """Get all composed posts with optional filtering"""
    try:
        if not post_composition_agent:
            raise HTTPException(status_code=503, detail="Post composition agent not available")
        
        result = post_composition_agent.get_composed_posts(period, template)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting composed posts: {str(e)}")

@app.get("/api/post-composition-storage")
async def get_post_composition_storage():
    """Get the post composition storage file contents"""
    try:
        post_composition_storage_path = os.path.join(static_dir, "post_composition_storage.json")
        
        if not os.path.exists(post_composition_storage_path):
            return {
                "success": True,
                "posts": [],
                "by_hash": {},
                "message": "No post composition storage found"
            }
        
        with open(post_composition_storage_path, 'r') as f:
            data = json.load(f)
            
        return {
            "success": True,
            "data": data,
            "file_path": post_composition_storage_path
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading post composition storage: {str(e)}")

@app.get("/api/composition-templates")
async def get_composition_templates():
    """Get available composition templates"""
    try:
        if not post_composition_agent:
            raise HTTPException(status_code=503, detail="Post composition agent not available")
        
        result = post_composition_agent.get_available_templates()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting composition templates: {str(e)}")

@app.delete("/api/composed-posts/{post_id}")
async def delete_composed_post(post_id: str):
    """Delete a composed post"""
    try:
        if not post_composition_agent:
            raise HTTPException(status_code=503, detail="Post composition agent not available")
        
        result = post_composition_agent.delete_composed_post(post_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting composed post: {str(e)}")

@app.post("/api/compose-integrated-post")
async def compose_integrated_post(request: IntegratedPostCompositionRequest):
    """Compose a visual post by integrating Instagram and Visual Posts data"""
    try:
        if not post_composition_agent:
            raise HTTPException(status_code=503, detail="Post composition agent not available")
        
        if not write_hashtag_agent:
            raise HTTPException(status_code=503, detail="Instagram hashtag agent not available")
        
        # Load Instagram post data
        instagram_storage_file = os.path.join(static_dir, "write_hashtag_storage.json")
        instagram_post = None
        if os.path.exists(instagram_storage_file):
            with open(instagram_storage_file, 'r') as f:
                instagram_data = json.load(f)
                for post in instagram_data.get("posts", []):
                    if post.get("id") == request.instagram_post_id:
                        instagram_post = post
                        break
        
        if not instagram_post:
            raise HTTPException(status_code=404, detail="Instagram post not found")
        
        # Load Visual post data
        visual_storage_file = os.path.join(static_dir, "visual_posts_storage.json")
        visual_post = None
        if os.path.exists(visual_storage_file):
            with open(visual_storage_file, 'r') as f:
                visual_data = json.load(f)
                for post in visual_data.get("posts", []):
                    if post.get("id") == request.visual_post_id:
                        visual_post = post
                        break
        
        if not visual_post:
            raise HTTPException(status_code=404, detail="Visual post not found")
        
        # Combine the content
        combined_text = f"{instagram_post.get('post_text', '')}\n\n{' '.join(instagram_post.get('hashtags', [])[:20])}"
        # Visual Posts haben file_path (fertiges Bild), nicht background_path
        background_path = visual_post.get("file_path", visual_post.get("background_path", ""))
        period = instagram_post.get("period_name", visual_post.get("period", ""))
        
        # Create enhanced custom options
        enhanced_options = {
            **(request.custom_options or {}),
            "source_instagram_id": request.instagram_post_id,
            "source_visual_id": request.visual_post_id,
            "call_to_action": instagram_post.get("call_to_action", ""),
            "hashtags": instagram_post.get("hashtags", []),
            "engagement_strategies": instagram_post.get("engagement_strategies", []),
            "combined_content": True
        }
        
        # Compose the integrated post
        result = post_composition_agent.compose_post(
            background_path=background_path,
            text=combined_text,
            period=period,
            template_name=request.template_name,
            post_format=request.post_format,
            custom_options=enhanced_options,
            force_new=True  # Always create new for integrated posts
        )
        
        if result["success"]:
            # Add integration metadata to the result
            result["post"]["integration_data"] = {
                "instagram_post_id": request.instagram_post_id,
                "visual_post_id": request.visual_post_id,
                "integrated": True,
                "created_at": datetime.now().isoformat()
            }
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error composing integrated post: {str(e)}")

# Video Generation API endpoints

@app.post("/api/generate-video")
async def generate_video(request: VideoGenerationRequest):
    """Generate a video from images"""
    try:
        if not video_generation_agent:
            raise HTTPException(status_code=503, detail="Video generation agent not available")
        
        result = video_generation_agent.create_video(
            image_paths=request.image_paths,
            video_type=request.video_type,
            duration=request.duration,
            fps=request.fps,
            options=request.options or {},
            force_new=request.force_new
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating video: {str(e)}")

@app.get("/api/videos")
async def get_videos(video_type: Optional[str] = None):
    """Get all videos with optional filtering by type"""
    try:
        if not video_generation_agent:
            raise HTTPException(status_code=503, detail="Video generation agent not available")
        
        result = video_generation_agent.get_videos(video_type)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting videos: {str(e)}")

@app.get("/api/video-types")
async def get_video_types():
    """Get available video types and their options"""
    try:
        if not video_generation_agent:
            raise HTTPException(status_code=503, detail="Video generation agent not available")
        
        result = video_generation_agent.get_available_video_types()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting video types: {str(e)}")

@app.delete("/api/videos/{video_id}")
async def delete_video(video_id: str):
    """Delete a video"""
    try:
        if not video_generation_agent:
            raise HTTPException(status_code=503, detail="Video generation agent not available")
        
        result = video_generation_agent.delete_video(video_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting video: {str(e)}")

@app.post("/api/cleanup-temp-files")
async def cleanup_temp_files():
    """Clean up temporary files from video generation"""
    try:
        if not video_generation_agent:
            raise HTTPException(status_code=503, detail="Video generation agent not available")
        
        result = video_generation_agent.cleanup_temp_files()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up temp files: {str(e)}")

# Instagram Reel endpoints
@app.post("/api/generate-reel")
async def generate_reel(request: InstagramReelRequest):
    """Generate Instagram Reel with script and video using selected provider"""
    try:
        if not instagram_reel_agent:
            raise HTTPException(status_code=503, detail="Instagram Reel agent not available")
        
        # Choose generation method based on provider
        if request.provider == "sora":
            result = instagram_reel_agent.generate_reel_with_sora(
                instagram_text=request.instagram_text,
                period=request.period,
                additional_input=request.additional_input,
                image_paths=request.image_paths,
                image_descriptions=request.image_descriptions,
                loop_style=request.loop_style,
                force_new=request.force_new
            )
        else:
            result = instagram_reel_agent.generate_reel_with_runway(
                instagram_text=request.instagram_text,
                period=request.period,
                additional_input=request.additional_input,
                image_paths=request.image_paths,
                image_descriptions=request.image_descriptions,
                force_new=request.force_new
            )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating reel: {str(e)}")

@app.post("/api/generate-video-script")
async def generate_video_script(request: InstagramReelRequest):
    """Generate video script for Instagram Reel"""
    try:
        if not instagram_reel_agent:
            raise HTTPException(status_code=503, detail="Instagram Reel agent not available")
        
        result = instagram_reel_agent.generate_video_script(
            instagram_text=request.instagram_text,
            period=request.period,
            additional_input=request.additional_input,
            image_descriptions=request.image_descriptions
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating video script: {str(e)}")

@app.get("/api/instagram-reels")
async def get_instagram_reels(period: Optional[str] = None):
    """Get all Instagram reels with optional filtering by period"""
    try:
        if not instagram_reel_agent:
            raise HTTPException(status_code=503, detail="Instagram Reel agent not available")
        
        result = instagram_reel_agent.get_generated_reels(period)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting reels: {str(e)}")

@app.delete("/api/instagram-reels/{reel_id}")
async def delete_reel(reel_id: str):
    """Delete an Instagram reel"""
    try:
        if not instagram_reel_agent:
            raise HTTPException(status_code=503, detail="Instagram Reel agent not available")
        
        result = instagram_reel_agent.delete_reel(reel_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting reel: {str(e)}")

@app.get("/api/reel-themes")
async def get_reel_themes():
    """Get period themes for reel generation"""
    try:
        if not instagram_reel_agent:
            raise HTTPException(status_code=503, detail="Instagram Reel agent not available")
        
        result = instagram_reel_agent.get_period_themes()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting reel themes: {str(e)}")

@app.get("/api/video-providers")
async def get_video_providers():
    """Get available video generation providers"""
    try:
        if not instagram_reel_agent:
            raise HTTPException(status_code=503, detail="Instagram Reel agent not available")
        
        result = instagram_reel_agent.get_video_providers()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting video providers: {str(e)}")

@app.get("/api/loop-styles")
async def get_loop_styles():
    """Get available loop styles for Sora videos"""
    try:
        if not instagram_reel_agent:
            raise HTTPException(status_code=503, detail="Instagram Reel agent not available")
        
        result = instagram_reel_agent.get_loop_styles()
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting loop styles: {str(e)}")

# Voice Over endpoints
@app.post("/api/generate-voice-script")
async def generate_voice_script(request: VoiceScriptRequest):
    """Generate a voice over script for video content"""
    try:
        if not voice_over_agent:
            raise HTTPException(status_code=503, detail="Voice Over agent not available")
        
        result = voice_over_agent.generate_voice_script(
            video_content=request.video_content,
            target_duration=request.target_duration,
            style=request.style,
            period=request.period
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating voice script: {str(e)}")

@app.post("/api/generate-voice-over")
async def generate_voice_over(request: VoiceOverRequest):
    """Generate voice over audio using ElevenLabs"""
    try:
        if not voice_over_agent:
            raise HTTPException(status_code=503, detail="Voice Over agent not available")
        
        result = voice_over_agent.generate_voice_over(
            text=request.text,
            voice=request.voice,
            language=request.language,
            model=request.model,
            output_format=request.output_format
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating voice over: {str(e)}")

@app.post("/api/generate-captions")
async def generate_captions(request: CaptionRequest):
    """Generate captions/subtitles from audio"""
    try:
        if not voice_over_agent:
            raise HTTPException(status_code=503, detail="Voice Over agent not available")
        
        result = voice_over_agent.generate_captions(
            audio_path=request.audio_path,
            language=request.language,
            style=request.style,
            max_chars_per_line=request.max_chars_per_line
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating captions: {str(e)}")

@app.post("/api/add-voice-to-video")
async def add_voice_to_video(request: AddVoiceToVideoRequest):
    """Add voice over audio to video"""
    try:
        if not voice_over_agent:
            raise HTTPException(status_code=503, detail="Voice Over agent not available")
        
        result = voice_over_agent.add_voice_over_to_video(
            video_path=request.video_path,
            audio_path=request.audio_path,
            volume=request.volume,
            fade_in=request.fade_in,
            fade_out=request.fade_out
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding voice to video: {str(e)}")

@app.post("/api/add-captions-to-video")
async def add_captions_to_video(request: AddCaptionsToVideoRequest):
    """Add captions/subtitles to video"""
    try:
        if not voice_over_agent:
            raise HTTPException(status_code=503, detail="Voice Over agent not available")
        
        result = voice_over_agent.add_captions_to_video(
            video_path=request.video_path,
            subtitle_path=request.subtitle_path,
            burn_in=request.burn_in,
            style=request.style
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding captions to video: {str(e)}")

@app.post("/api/process-video-with-voice-and-captions")
async def process_video_with_voice_and_captions(request: ProcessVideoRequest):
    """Complete pipeline: generate voice over, create captions, and add both to video"""
    try:
        if not voice_over_agent:
            raise HTTPException(status_code=503, detail="Voice Over agent not available")
        
        result = voice_over_agent.process_video_with_voice_and_captions(
            video_path=request.video_path,
            script_text=request.script_text,
            voice=request.voice,
            language=request.language,
            caption_style=request.caption_style,
            burn_in_captions=request.burn_in_captions
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")

@app.get("/api/available-voices")
async def get_available_voices():
    """Get list of available voices"""
    try:
        if not voice_over_agent:
            raise HTTPException(status_code=503, detail="Voice Over agent not available")
        
        return voice_over_agent.get_available_voices()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting available voices: {str(e)}")

@app.get("/api/caption-styles")
async def get_caption_styles():
    """Get available caption styles"""
    try:
        if not voice_over_agent:
            raise HTTPException(status_code=503, detail="Voice Over agent not available")
        
        return voice_over_agent.get_caption_styles()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting caption styles: {str(e)}")

@app.get("/api/voice-overs")
async def get_voice_overs():
    """Get all generated voice overs"""
    try:
        if not voice_over_agent:
            raise HTTPException(status_code=503, detail="Voice Over agent not available")
        
        return voice_over_agent.get_voice_overs()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting voice overs: {str(e)}")

@app.post("/api/android-test")
async def test_android_app(request: AndroidTestRequest, background_tasks: BackgroundTasks):
    """Start automated Android app testing"""
    logger.info("========== ANDROID TEST POST ENDPOINT CALLED ==========")
    logger.info(f"Request method: POST")
    logger.info(f"Request data: {request}")
    logger.info(f"APK path: {request.apk_path}")
    logger.info(f"Test actions: {request.test_actions}")
    logger.info(f"Target API level: {request.target_api_level}")
    logger.info(f"AVD name: {request.avd_name}")
    try:
        if not android_testing_agent:
            logger.error("Android testing agent not available")
            raise HTTPException(status_code=503, detail="Android testing agent not available")
        
        logger.info(f"Validating APK path: {request.apk_path}")
        # Validate APK path
        if not os.path.exists(request.apk_path):
            logger.error(f"APK file not found: {request.apk_path}")
            raise HTTPException(status_code=400, detail=f"APK file not found: {request.apk_path}")
        
        # Generate test ID
        test_id = android_testing_agent._generate_test_id(request.apk_path)
        logger.info(f"Generated test ID: {test_id}")
        
        # Start testing in background
        logger.info(f"Adding background task for test {test_id}")
        background_tasks.add_task(
            run_android_test,
            test_id,
            request.apk_path,
            request.test_actions,
            request.target_api_level,
            request.avd_name
        )
        
        response = {
            "success": True,
            "test_id": test_id,
            "message": "Android app testing started",
            "status_url": f"/api/android-test/{test_id}"
        }
        logger.info(f"Android test started successfully: {response}")
        return response
        
    except HTTPException as he:
        logger.error(f"HTTP exception in Android test endpoint: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Android test endpoint: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error starting Android test: {str(e)}")

async def run_android_test(test_id: str, apk_path: str, test_actions: Optional[List[str]], 
                          target_api_level: Optional[int], avd_name: Optional[str]):
    """Background task to run Android testing"""
    logger.info(f"Starting background Android test with ID: {test_id}")
    logger.info(f"Test parameters - APK: {apk_path}, Actions: {test_actions}, API Level: {target_api_level}, AVD: {avd_name}")
    
    try:
        # Run the test with asyncio execution
        logger.info(f"Calling android_testing_agent.test_android_app for test {test_id}")
        
        # Wrap the async call in proper error handling
        try:
            result = await android_testing_agent.test_android_app(
                apk_path=apk_path,
                test_actions=test_actions,
                target_api_level=target_api_level,
                avd_name=avd_name
            )
            logger.info(f"Android test {test_id} completed successfully: {result}")
        except Exception as inner_e:
            logger.error(f"Error during test_android_app execution for test {test_id}: {str(inner_e)}")
            logger.error(f"Inner exception traceback: {traceback.format_exc()}")
            raise
        
        # Results are automatically saved by the agent
        logger.info(f"Background test {test_id} completed, results saved by agent")
        
    except Exception as e:
        logger.error(f"Exception in run_android_test for test {test_id}: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # Save error to storage
        error_data = {
            "success": False,
            "test_id": test_id,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Saving error data to storage for test {test_id}: {error_data}")
        
        android_testing_agent.storage[test_id] = error_data
        android_testing_agent._save_storage()
        logger.info(f"Error data saved for test {test_id}")

@app.get("/api/android-test/{test_id}")
async def get_android_test_results(test_id: str):
    """Get Android test results by ID"""
    logger.info(f"Android test GET endpoint called for test_id: {test_id}")
    try:
        if not android_testing_agent:
            logger.error("Android testing agent not available for GET request")
            raise HTTPException(status_code=503, detail="Android testing agent not available")
        
        logger.info(f"Retrieving test results for test_id: {test_id}")
        result = android_testing_agent.get_test_results(test_id)
        logger.info(f"Retrieved result for test {test_id}: {result}")
        
        if result["success"]:
            return result["data"]
        else:
            logger.warning(f"Test {test_id} not found or failed: {result['error']}")
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException as he:
        logger.error(f"HTTP exception in GET /api/android-test/{test_id}: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in GET /api/android-test/{test_id}: {str(e)}")
        logger.error(f"GET endpoint traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error retrieving test results: {str(e)}")

@app.get("/api/android-tests")
async def list_android_tests(limit: int = 10):
    """List recent Android test results"""
    try:
        if not android_testing_agent:
            raise HTTPException(status_code=503, detail="Android testing agent not available")
        
        result = android_testing_agent.list_recent_tests(limit)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=500, detail=result["error"])
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing test results: {str(e)}")

@app.get("/api/android-avds")
async def list_android_avds():
    """List available Android Virtual Devices (AVDs)"""
    try:
        # Run emulator command to list AVDs
        result = subprocess.run(
            ["emulator", "-list-avds"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # If emulator command fails, try to provide helpful error
            error_msg = result.stderr.strip() if result.stderr else "Emulator command not found"
            logger.error(f"Failed to list AVDs: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "avds": []
            }
        
        # Parse AVD names from output
        avd_names = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
        
        return {
            "success": True,
            "avds": avd_names,
            "count": len(avd_names)
        }
        
    except FileNotFoundError:
        logger.error("Emulator command not found in PATH")
        return {
            "success": False,
            "error": "Android emulator not found. Please ensure Android SDK is installed and emulator is in PATH",
            "avds": []
        }
    except Exception as e:
        logger.error(f"Error listing AVDs: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "avds": []
        }

@app.post("/api/android-test/upload-apk")
async def upload_apk(file: UploadFile = File(...)):
    """Upload an APK file for testing"""
    try:
        # Validate file is an APK
        if not file.filename.endswith('.apk'):
            raise HTTPException(status_code=400, detail="File must be an APK")
        
        # Create temp directory for APK uploads if it doesn't exist
        temp_dir = os.path.join(tempfile.gettempdir(), "android_test_apks")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save the uploaded file with a unique name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"upload_{timestamp}_{file.filename}"
        file_path = os.path.join(temp_dir, safe_filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"APK uploaded successfully: {file_path}")
        
        return {
            "success": True,
            "file_path": file_path,
            "original_filename": file.filename,
            "size": len(content)
        }
        
    except Exception as e:
        logger.error(f"Error uploading APK: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading APK: {str(e)}")

@app.get("/api/android-test/{test_id}/screenshots")
async def get_test_screenshots(test_id: str):
    """Get list of screenshots for a test"""
    try:
        if not android_testing_agent:
            raise HTTPException(status_code=503, detail="Android testing agent not available")
        
        # Get test results
        result = android_testing_agent.get_test_results(test_id)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail="Test not found")
        
        # Extract screenshot paths
        test_data = result["data"]
        screenshots = []
        
        # Get all screenshots from the directory for this test_id
        screenshot_dir = android_testing_agent.screenshot_dir
        import glob
        
        # Find all screenshots for this test
        all_screenshots = glob.glob(os.path.join(screenshot_dir, f"{test_id}_*.png"))
        
        # Sort by timestamp in filename
        all_screenshots.sort()
        
        # Create screenshot entries for all found files
        for screenshot_path in all_screenshots:
            basename = os.path.basename(screenshot_path)
            # Extract the name part (between test_id and timestamp)
            parts = basename.split('_')
            if len(parts) >= 3:
                # Skip the test_id hash and reconstruct the name
                name_parts = []
                for i in range(2, len(parts)):
                    if parts[i].startswith('20'):  # Likely a timestamp
                        break
                    name_parts.append(parts[i])
                name = '_'.join(name_parts) if name_parts else 'screenshot'
            else:
                name = 'screenshot'
            
            # Get metadata from storage if available
            screenshot_metadata = {}
            if "screenshots" in test_data and isinstance(test_data["screenshots"], dict):
                # Find matching metadata by name
                for stored_name, metadata in test_data["screenshots"].items():
                    if stored_name in basename or name == stored_name:
                        screenshot_metadata = metadata
                        break
            
            screenshots.append({
                "name": name,
                "path": screenshot_path,
                "url": f"/static/android_screenshots/{basename}",
                "action": screenshot_metadata.get("action", ""),
                "description": screenshot_metadata.get("description", ""),
                "ui_elements": screenshot_metadata.get("ui_elements_found", {})
            })
        
        return {
            "success": True,
            "test_id": test_id,
            "screenshots": screenshots
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving screenshots: {str(e)}")

@app.delete("/api/android-test/{test_id}")
async def delete_android_test(test_id: str):
    """Delete Android test results and associated data"""
    logger.info(f"Löschung von Android-Test angefordert: {test_id}")
    try:
        if not android_testing_agent:
            logger.error("Android-Test-Agent nicht verfügbar")
            raise HTTPException(status_code=503, detail="Android-Test-Agent nicht verfügbar")
        
        logger.info(f"Lösche Testergebnisse für Test-ID: {test_id}")
        result = android_testing_agent.delete_test_run(test_id)
        
        if result["success"]:
            logger.info(f"Test {test_id} erfolgreich gelöscht")
            return result
        else:
            logger.warning(f"Test {test_id} nicht gefunden: {result['error']}")
            raise HTTPException(status_code=404, detail=result["error"])
            
    except HTTPException as he:
        logger.error(f"HTTP-Fehler beim Löschen von Test {test_id}: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Unerwarteter Fehler beim Löschen von Test {test_id}: {str(e)}")
        logger.error(f"Traceback für Löschvorgang: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Löschen der Testergebnisse: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "image_generation_enabled": image_generator is not None,
        "qa_agent_enabled": qa_agent is not None,
        "affirmations_agent_enabled": affirmations_agent is not None,
        "visual_posts_enabled": os.getenv('PEXELS_API_KEY') is not None,
        "write_hashtag_agent_enabled": write_hashtag_agent is not None,
        "instagram_analyzer_enabled": instagram_analyzer_agent is not None,
        "workflow_agent_enabled": workflow_agent is not None,
        "post_composition_agent_enabled": post_composition_agent is not None,
        "video_generation_agent_enabled": video_generation_agent is not None,
        "instagram_reel_agent_enabled": instagram_reel_agent is not None,
        "android_testing_agent_enabled": android_testing_agent is not None,
        "ffmpeg_available": video_generation_agent.ffmpeg_available if video_generation_agent else False,
        "runway_api_configured": os.getenv('RUNWAY_API_KEY') is not None,
        "adb_configured": os.getenv('ADB_PATH') is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)