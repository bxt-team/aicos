from fastapi import APIRouter, HTTPException
from schemas.content import AffirmationRequest
from core.dependencies import affirmations_agent
from datetime import datetime
import json
import os

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
    if not affirmations_agent:
        raise HTTPException(status_code=503, detail="Affirmations Agent not initialized")
    
    try:
        period_info = PERIODS.get(request.period_name, request.period_info)
        
        affirmations = affirmations_agent.generate_affirmations(
            period_name=request.period_name,
            period_info=period_info,
            count=request.count
        )
        
        # Save affirmations to file
        storage_dir = "storage/affirmations"
        os.makedirs(storage_dir, exist_ok=True)
        
        filename = f"{storage_dir}/affirmations_{request.period_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "period": request.period_name,
                "affirmations": affirmations,
                "created_at": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        return {
            "status": "success",
            "period": request.period_name,
            "affirmations": affirmations,
            "count": len(affirmations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/affirmations")
async def get_all_affirmations():
    storage_dir = "storage/affirmations"
    
    if not os.path.exists(storage_dir):
        return {"status": "success", "affirmations": []}
    
    all_affirmations = []
    
    for filename in os.listdir(storage_dir):
        if filename.endswith('.json'):
            with open(os.path.join(storage_dir, filename), 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Create individual affirmation entries
                for affirmation_text in data.get('affirmations', []):
                    all_affirmations.append({
                        "id": f"{filename}_{hash(affirmation_text)}",
                        "text": affirmation_text,
                        "period_name": data['period'],
                        "period_color": PERIODS.get(data['period'], {}).get('color', '#999999'),
                        "created_at": data.get('created_at', '')
                    })
    
    # Sort by creation date, newest first
    all_affirmations.sort(key=lambda x: x['created_at'], reverse=True)
    
    return {
        "status": "success",
        "affirmations": all_affirmations,
        "count": len(all_affirmations)
    }

@router.get("/periods")
async def get_periods():
    return {
        "status": "success",
        "periods": PERIODS
    }