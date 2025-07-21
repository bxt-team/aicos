from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from app.models.content import ContentRequest, ApprovalRequest, ContentResponse, QuestionRequest
from app.core.dependencies import get_agent, content_wrapper, content_storage
from app.core.auth import get_current_user
from app.models.auth import User
from app.core.middleware import RequestContext
from datetime import datetime
import uuid
import traceback

router = APIRouter(prefix="/content", tags=["Content"])

# Content generation endpoints
@router.post("/generate", response_model=ContentResponse)
async def generate_content(
    request: ContentRequest, 
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Generate content (requires authentication)"""
    content_id = str(uuid.uuid4())
    
    # Extract organization context
    org_id = getattr(request, 'organization_id', None) or current_user.default_organization_id
    project_id = getattr(request, 'project_id', None)
    
    # Store initial content state with user context
    content_storage[content_id] = {
        "status": "processing",
        "created_at": datetime.now().isoformat(),
        "request": request.model_dump(),
        "user_id": current_user.id,
        "organization_id": org_id,
        "project_id": project_id
    }
    
    # Create context for background task
    context = RequestContext(
        user_id=current_user.id,
        organization_id=org_id,
        project_id=project_id
    )
    
    # Run content generation in background
    background_tasks.add_task(
        run_content_generation,
        content_id,
        request.knowledge_files,
        request.style_preferences,
        context
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
async def get_content(
    content_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get content by ID (requires authentication)"""
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content = content_storage[content_id]
    
    # Check if user has access to this content
    if content.get("user_id") != current_user.id and content.get("organization_id") != current_user.default_organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
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
async def approve_content(
    request: ApprovalRequest,
    current_user: User = Depends(get_current_user)
):
    """Approve or reject content (requires authentication)"""
    if request.content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content = content_storage[request.content_id]
    
    # Check if user has access to this content
    if content.get("user_id") != current_user.id and content.get("organization_id") != current_user.default_organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    content_storage[request.content_id]["approved"] = request.approved
    content_storage[request.content_id]["feedback"] = request.feedback
    content_storage[request.content_id]["approved_by"] = current_user.id
    content_storage[request.content_id]["approved_at"] = datetime.now().isoformat()
    
    return {
        "status": "success",
        "message": f"Content {'approved' if request.approved else 'rejected'}",
        "content_id": request.content_id
    }

@router.get("/")
async def list_content(
    current_user: User = Depends(get_current_user)
):
    """List all content for the user's organization (requires authentication)"""
    user_content = []
    
    for cid, content in content_storage.items():
        # Filter by user's organization
        if content.get("organization_id") == current_user.default_organization_id or content.get("user_id") == current_user.id:
            user_content.append({
                "content_id": cid,
                "status": content.get("status", "unknown"),
                "created_at": content.get("created_at", ""),
                "approved": content.get("approved")
            })
    
    return {
        "content": user_content
    }

@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete content (requires authentication)"""
    if content_id not in content_storage:
        raise HTTPException(status_code=404, detail="Content not found")
    
    content = content_storage[content_id]
    
    # Check if user has access to delete this content
    if content.get("user_id") != current_user.id and content.get("organization_id") != current_user.default_organization_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    del content_storage[content_id]
    return {"status": "success", "message": "Content deleted"}

# Helper function
async def run_content_generation(content_id: str, knowledge_files, style_preferences, context: RequestContext):
    try:
        content_storage[content_id]["status"] = "researching"
        
        # Set context on content_wrapper if it supports it
        if hasattr(content_wrapper, 'set_context'):
            content_wrapper.set_context(context)
        
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

