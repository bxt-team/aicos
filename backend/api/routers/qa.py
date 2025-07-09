"""
Q&A and knowledge base endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.dependencies import get_agent

router = APIRouter(prefix="/api", tags=["qa"])

# Request models
class QuestionRequest(BaseModel):
    question: str

# Q&A endpoints
@router.post("/ask-question")
async def ask_question(request: QuestionRequest):
    """Ask a question about the 7 Cycles of Life"""
    qa_agent = get_agent('qa_agent')
    if not qa_agent:
        raise HTTPException(status_code=503, detail="Q&A agent not available")
    
    result = qa_agent.answer_question(request.question)
    
    if result["success"]:
        return {
            "success": True,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "confidence": result.get("confidence", "high")
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "Failed to answer question"))

@router.get("/qa-health")
async def check_qa_health():
    """Check if Q&A agent is properly initialized"""
    qa_agent = get_agent('qa_agent')
    if not qa_agent:
        return {
            "status": "unhealthy",
            "message": "Q&A agent not initialized"
        }
    
    health_check = qa_agent.health_check()
    return {
        "status": "healthy" if health_check["is_ready"] else "unhealthy",
        "documents_loaded": health_check["documents_loaded"],
        "index_size": health_check["index_size"],
        "message": health_check.get("message", "Q&A agent is ready")
    }

@router.get("/knowledge-overview")
async def get_knowledge_overview():
    """Get an overview of the knowledge base"""
    qa_agent = get_agent('qa_agent')
    if not qa_agent:
        raise HTTPException(status_code=503, detail="Q&A agent not available")
    
    overview = qa_agent.get_knowledge_overview()
    return {
        "success": True,
        "overview": overview,
        "topics": [
            "7 Cycles Overview",
            "Individual Cycles",
            "Spiritual Aspects",
            "Practical Applications",
            "Life Transitions",
            "Personal Growth"
        ]
    }

@router.get("/periods")
async def get_periods():
    """Get information about all 7 periods/cycles"""
    return {
        "periods": [
            {
                "number": 1,
                "name": "Foundation",
                "age_range": "0-7",
                "description": "Building the foundation of self",
                "themes": ["security", "trust", "basic needs", "family bonds"]
            },
            {
                "number": 2,
                "name": "Expansion",
                "age_range": "7-14",
                "description": "Expanding awareness and social connections",
                "themes": ["learning", "friendship", "exploration", "identity formation"]
            },
            {
                "number": 3,
                "name": "Integration",
                "age_range": "14-21",
                "description": "Integrating self with society",
                "themes": ["independence", "relationships", "career exploration", "values"]
            },
            {
                "number": 4,
                "name": "Stability",
                "age_range": "21-28",
                "description": "Creating stability and structure",
                "themes": ["career", "partnerships", "goals", "responsibility"]
            },
            {
                "number": 5,
                "name": "Expression",
                "age_range": "28-35",
                "description": "Expressing authentic self",
                "themes": ["creativity", "leadership", "family", "achievement"]
            },
            {
                "number": 6,
                "name": "Reflection",
                "age_range": "35-42",
                "description": "Reflecting on life's journey",
                "themes": ["wisdom", "mentoring", "life review", "spiritual growth"]
            },
            {
                "number": 7,
                "name": "Transcendence",
                "age_range": "42+",
                "description": "Transcending to higher consciousness",
                "themes": ["legacy", "spiritual mastery", "service", "enlightenment"]
            }
        ]
    }

@router.get("/agent-prompts")
async def get_agent_prompts():
    """Get information about agent prompts (for debugging/transparency)"""
    return {
        "agents": {
            "qa_agent": {
                "description": "Answers questions about the 7 Cycles of Life philosophy",
                "capabilities": ["knowledge retrieval", "contextual answers", "source citation"]
            },
            "affirmations_agent": {
                "description": "Generates personalized affirmations for each life cycle",
                "capabilities": ["affirmation generation", "period-specific content", "motivational messaging"]
            },
            "content_workflow_agent": {
                "description": "Manages the complete content creation workflow",
                "capabilities": ["workflow orchestration", "multi-agent coordination", "content pipeline"]
            },
            "instagram_poster_agent": {
                "description": "Handles Instagram posting and scheduling",
                "capabilities": ["post creation", "scheduling", "hashtag optimization", "engagement tracking"]
            },
            "visual_post_creator_agent": {
                "description": "Creates visual content for social media",
                "capabilities": ["image generation", "template application", "text overlay", "format optimization"]
            }
        }
    }