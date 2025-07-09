from fastapi import APIRouter
from datetime import datetime
from app.core.dependencies import get_agent
import json

router = APIRouter(tags=["Health"])

@router.get("/", summary="API Root", description="Welcome endpoint with API information and documentation links")
async def root():
    """
    Welcome to the 7 Cycles AI Assistant API.
    
    This endpoint provides information about the API and links to documentation.
    """
    return {
        "message": "7 Cycles of Life AI Assistant API",
        "version": "2.0.0",
        "status": "active",
        "documentation": {
            "interactive": "/docs",
            "alternative": "/redoc",
            "openapi_schema": "/openapi.json"
        },
        "main_endpoints": {
            "health_check": "/health",
            "content_generation": "/content/generate",
            "ask_question": "/api/ask-question",
            "generate_affirmations": "/generate-affirmations",
            "create_visual_post": "/create-visual-post",
            "instagram_posts": "/instagram-posts",
            "workflows": "/api/workflows"
        },
        "timestamp": datetime.now().isoformat()
    }

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "7cycles-backend",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/qa-health")
async def qa_health():
    qa_agent = get_agent('qa_agent')
    if not qa_agent:
        return {"status": "error", "message": "QA Agent not initialized"}
    
    try:
        # Test the QA agent with a simple query
        test_result = qa_agent.answer_question("What is 7 cycles?")
        return {
            "status": "healthy",
            "test_response": test_result[:100] + "..." if len(test_result) > 100 else test_result,
            "knowledge_loaded": True
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "knowledge_loaded": False
        }

@router.get("/knowledge-overview")
async def knowledge_overview():
    qa_agent = get_agent('qa_agent')
    if not qa_agent:
        return {"status": "error", "message": "QA Agent not initialized"}
    
    try:
        # Get overview of loaded knowledge
        overview = qa_agent.get_knowledge_overview()
        return {
            "status": "success",
            "knowledge_overview": overview,
            "total_documents": len(qa_agent.documents) if hasattr(qa_agent, 'documents') else 0
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": str(e)
        }