from fastapi import APIRouter
from datetime import datetime
from core.dependencies import get_agent, qa_agent
import json

router = APIRouter(tags=["Health"])

@router.get("/")
async def root():
    return {"message": "7 Cycles of Life AI Assistant API", "version": "1.0.0"}

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "7cycles-backend",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/qa-health")
async def qa_health():
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