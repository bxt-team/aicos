"""
Workflow management endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from pydantic import BaseModel

from app.core.dependencies import get_agent

router = APIRouter(prefix="/api", tags=["workflows"])

# Request models
class WorkflowCreateRequest(BaseModel):
    period: str
    workflow_type: Optional[str] = "full"
    options: Optional[Dict[str, Any]] = None

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

class VideoReelRequest(BaseModel):
    template_id: str
    content_data: Dict[str, Any]

# Workflow endpoints
@router.post("/workflows")
async def create_workflow(request: WorkflowCreateRequest):
    """Create a new content workflow"""
    workflow_agent = get_agent('workflow_agent')
    if not workflow_agent:
        raise HTTPException(status_code=503, detail="Workflow agent not available")
    
    result = workflow_agent.create_workflow(
        request.period,
        request.workflow_type,
        request.options
    )
    
    return result

@router.get("/workflows")
async def list_workflows():
    """List all workflows"""
    workflow_agent = get_agent('workflow_agent')
    if not workflow_agent:
        raise HTTPException(status_code=503, detail="Workflow agent not available")
    
    return workflow_agent.list_workflows()

@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """Get a specific workflow by ID"""
    workflow_agent = get_agent('workflow_agent')
    if not workflow_agent:
        raise HTTPException(status_code=503, detail="Workflow agent not available")
    
    workflow = workflow_agent.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow

@router.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow"""
    workflow_agent = get_agent('workflow_agent')
    if not workflow_agent:
        raise HTTPException(status_code=503, detail="Workflow agent not available")
    
    result = workflow_agent.delete_workflow(workflow_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return result

@router.get("/workflow-templates")
async def get_workflow_templates():
    """Get available workflow templates"""
    return {
        "templates": [
            {
                "id": "full",
                "name": "Full Content Creation",
                "description": "Complete workflow from research to posting",
                "steps": ["research", "writing", "visual_creation", "posting"]
            },
            {
                "id": "quick_post",
                "name": "Quick Post",
                "description": "Fast workflow for simple posts",
                "steps": ["writing", "visual_creation"]
            },
            {
                "id": "research_only",
                "name": "Research Only",
                "description": "Research and content planning",
                "steps": ["research", "content_planning"]
            },
            {
                "id": "visual_focus",
                "name": "Visual Focus",
                "description": "Focus on visual content creation",
                "steps": ["visual_concepts", "image_generation", "post_composition"]
            }
        ]
    }

# Post composition endpoints
@router.post("/compose-post")
async def compose_post(request: PostCompositionRequest):
    """Compose a visual post with text overlay"""
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    result = post_composition_agent.compose_post(
        request.background_path,
        request.text,
        request.period,
        request.template_name,
        request.post_format,
        request.custom_options,
        request.force_new
    )
    
    return result

@router.get("/composed-posts")
async def list_composed_posts():
    """List all composed posts"""
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    return post_composition_agent.get_composed_posts()

@router.get("/post-composition-storage")
async def get_post_composition_storage():
    """Get all post composition storage data"""
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    return {"storage": post_composition_agent.storage}

@router.get("/composition-templates")
async def get_composition_templates():
    """Get available composition templates"""
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    # Get templates from the agent
    result = post_composition_agent.get_available_templates()
    
    if not result.get("success"):
        raise HTTPException(status_code=500, detail="Failed to get templates")
    
    # Format templates for frontend
    formatted_templates = []
    for template_id, template_data in result.get("templates", {}).items():
        # Skip video templates for this endpoint
        if template_data.get("type") == "video":
            continue
            
        formatted_templates.append({
            "id": template_id,
            "name": template_data.get("name", template_id),
            "description": template_data.get("description", ""),
            "supports": ["post", "story"],  # All PIL templates support both formats
            "type": template_data.get("type", "pil")
        })
    
    return {
        "templates": formatted_templates
    }

@router.delete("/composed-posts/{post_id}")
async def delete_composed_post(post_id: str):
    """Delete a composed post"""
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    result = post_composition_agent.delete_composed_post(post_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail="Composed post not found")
    
    return result

@router.post("/compose-integrated-post")
async def compose_integrated_post(request: IntegratedPostCompositionRequest):
    """Compose a post using existing Instagram post and visual post data"""
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    result = post_composition_agent.compose_integrated_post(
        request.instagram_post_id,
        request.visual_post_id,
        request.template_name,
        request.post_format,
        request.custom_options
    )
    
    return result

# Video template endpoints
@router.get("/video-templates")
async def get_video_templates():
    """Get available video templates"""
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    templates = post_composition_agent.get_available_templates()
    
    # Filter only video templates
    video_templates = {
        k: v for k, v in templates.get("templates", {}).items() 
        if v.get("type") == "video"
    }
    
    return {
        "success": True,
        "templates": video_templates,
        "video_templates_enabled": templates.get("video_templates_enabled", True)
    }

@router.get("/video-template-fields/{template_id}")
async def get_video_template_fields(template_id: str):
    """Get replaceable fields for a video template"""
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    result = post_composition_agent.get_video_template_fields(template_id)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Error getting template fields"))
    
    return result

@router.post("/create-video-reel")
async def create_video_reel(request: VideoReelRequest):
    """Create a reel/video using a video template"""
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    result = post_composition_agent.create_video_reel(
        request.template_id,
        request.content_data
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Error creating video reel"))
    
    return result

@router.post("/compose-video-post")
async def compose_video_post(request: PostCompositionRequest):
    """Compose a post using video templates"""
    # Ensure the template name starts with "video:"
    if not request.template_name.startswith("video:"):
        raise HTTPException(status_code=400, detail="Invalid video template name format")
    
    post_composition_agent = get_agent('post_composition_agent')
    if not post_composition_agent:
        raise HTTPException(status_code=503, detail="Post composition agent not available")
    
    result = post_composition_agent.compose_post(
        request.background_path,
        request.text,
        request.period,
        request.template_name,
        request.post_format,
        request.custom_options,
        request.force_new
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "Error composing video post"))
    
    return result