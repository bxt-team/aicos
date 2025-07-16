from fastapi import APIRouter, HTTPException
from app.models.content import AffirmationRequest
from app.core.dependencies import get_agent
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Affirmations"])

# Period information
PERIODS = {
    "Image": {"description": "Focus on self-image and identity", "color": "#FF6B6B"},
    "Veränderung": {"description": "Embrace change and transformation", "color": "#4ECDC4"},
    "Energie": {"description": "Harness energy and vitality", "color": "#FFE66D"},
    "Kreativität": {"description": "Express creativity and innovation", "color": "#A8E6CF"},
    "Erfolg": {"description": "Achieve success and recognition", "color": "#C7CEEA"},
    "Entspannung": {"description": "Find relaxation and peace", "color": "#FFDAB9"},
    "Umsicht": {"description": "Practice wisdom and reflection", "color": "#B4A0E5"}
}

@router.post("/generate-affirmations")
async def generate_affirmations(request: AffirmationRequest):
    affirmations_agent = get_agent('affirmations_agent')
    logger.info(f"Affirmations agent status: {affirmations_agent}")
    logger.info(f"Affirmations agent type: {type(affirmations_agent)}")
    
    if not affirmations_agent:
        logger.error("Affirmations Agent is None")
        raise HTTPException(status_code=503, detail="Affirmations Agent not initialized")
    
    try:
        period_info = PERIODS.get(request.period_name, request.period_info)
        
        result = await affirmations_agent.generate_affirmations(
            period_name=request.period_name,
            period_info=period_info,
            count=request.count
        )
        
        # Check if generation was successful
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate affirmations"))
        
        return {
            "status": "success",
            "period": request.period_name,
            "affirmations": result.get("affirmations", []),
            "count": len(result.get("affirmations", [])),
            "message": result.get("message", "Affirmations generated successfully")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/affirmations")
async def get_all_affirmations(period_name: str = None):
    affirmations_agent = get_agent('affirmations_agent')
    
    if not affirmations_agent:
        logger.error("Affirmations Agent is None")
        raise HTTPException(status_code=503, detail="Affirmations Agent not initialized")
    
    try:
        result = await affirmations_agent.get_affirmations_by_period(period_name)
        
        if not result.get("success", False):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to retrieve affirmations"))
        
        # Add theme and focus if missing for compatibility
        affirmations = result.get("affirmations", [])
        for aff in affirmations:
            if "theme" not in aff and "period_name" in aff:
                aff["theme"] = aff["period_name"]
            if "focus" not in aff and "period_name" in aff:
                aff["focus"] = f"{aff['period_name']} Stärkung"
        
        return {
            "status": "success",
            "affirmations": affirmations,
            "count": len(affirmations)
        }
    except Exception as e:
        logger.error(f"Error retrieving affirmations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/periods")
async def get_periods():
    return {
        "status": "success",
        "periods": PERIODS
    }