from fastapi import APIRouter, HTTPException, BackgroundTasks
from schemas.content import ContentRequest, ApprovalRequest, ContentResponse, QuestionRequest
from core.dependencies import content_wrapper, content_storage, qa_agent
from datetime import datetime
import uuid
import traceback

router = APIRouter(prefix="/content", tags=["Content"])

# Content generation endpoints
@router.post("/generate", response_model=ContentResponse)
async def generate_content(request: ContentRequest, background_tasks: BackgroundTasks):
    content_id = str(uuid.uuid4())
    
    # Store initial content state
    content_storage[content_id] = {
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "request": request.model_dump()
    }
    
    # Run content generation in background
    background_tasks.add_task(
        run_content_generation,
        content_id,
        request.knowledge_files,
        request.style_preferences
    )
    
    return ContentResponse(
        content_id=content_id,
        research_results="Processing...",
        written_content="Processing...",
        visual_concepts="Processing...",
        images=[],
        status="processing",
        created_at=content_storage[content_id]["created_at"]
    )

@router.get("/{content_id}", response_model=ContentResponse)
async def get_content(content_id: str):
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content = content_storage[content_id]
    
    return ContentResponse(
        content_id=content_id,
        research_results=content.get("research_results", ""),
        written_content=content.get("written_content", ""),
        visual_concepts=content.get("visual_concepts", ""),
        images=content.get("images", []),
        status=content.get("status", "unknown"),
        created_at=content.get("created_at", "")
    )

@router.post("/approve")
async def approve_content(request: ApprovalRequest):
    if request.content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content_storage[request.content_id]["approved"] = request.approved
    content_storage[request.content_id]["feedback"] = request.feedback
    
    return {
        "status": "success",
        "message": f"Content {'approved' if request.approved else 'rejected'}",
        "content_id": request.content_id
    }

@router.get("/")
async def list_content():
    return {
        "content": [
            {
                "content_id": cid,
                "status": content.get("status", "unknown"),
                "created_at": content.get("created_at", ""),
                "approved": content.get("approved")
            }
            for cid, content in content_storage.items()
        ]
    }

@router.delete("/{content_id}")
async def delete_content(content_id: str):
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    del content_storage[content_id]
    return {"status": "success", "message": "Content deleted"}

# Helper function
async def run_content_generation(content_id: str, knowledge_files, style_preferences):
    try:
        content_storage[content_id]["status"] = "researching"
        
        # Run the content generation flow
        result = await content_wrapper.run_async(
            knowledge_files=knowledge_files,
            style_preferences=style_preferences
        )
        
        # Update storage with results
        content_storage[content_id].update({
            "status": "completed",
            "research_results": result.get("research_results", ""),
            "written_content": result.get("written_content", ""),
            "visual_concepts": result.get("visual_concepts", ""),
            "images": result.get("generated_images", [])
        })
    except Exception as e:
        content_storage[content_id].update({
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        })

# Question answering endpoint
@router.post("/ask-question")
async def ask_question(request: QuestionRequest):
    if not qa_agent:
        raise HTTPException(status_code=503, detail="QA Agent not initialized")
    
    try:
        answer = qa_agent.answer_question(request.question)
        return {
            "status": "success",
            "question": request.question,
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))