from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import json
import asyncio
from datetime import datetime
import sys
import traceback

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.flows.content_generation_wrapper import ContentGenerationWrapper
from src.tools.image_generator import ImageGenerator
from src.agents.qa_agent import QAAgent
from src.agents.affirmations_agent import AffirmationsAgent
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="7 Cycles of Life AI Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create static directory if it doesn't exist
static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "generated"), exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

content_storage = {}
image_generator = None
qa_agent = None
affirmations_agent = None

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

@app.on_event("startup")
async def startup_event():
    global image_generator, qa_agent, affirmations_agent
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        image_generator = ImageGenerator(openai_api_key)
        qa_agent = QAAgent(openai_api_key)
        affirmations_agent = AffirmationsAgent(openai_api_key)
        print("Successfully initialized all agents")
    else:
        print("Warning: OPENAI_API_KEY not found. All AI features will be disabled.")

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "image_generation_enabled": image_generator is not None,
        "qa_agent_enabled": qa_agent is not None,
        "affirmations_agent_enabled": affirmations_agent is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)