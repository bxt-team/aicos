"""
Image search and generation endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from core.dependencies import get_agent

router = APIRouter(tags=["images"])

# Request models
class ImageSearchRequest(BaseModel):
    query: str
    count: Optional[int] = 5
    style: Optional[str] = "nature"
    orientation: Optional[str] = "landscape"

# Image search endpoints
@router.post("/search-images")
async def search_images(request: ImageSearchRequest):
    """Search for stock images from Pexels"""
    image_generator = get_agent('image_generator')
    if not image_generator:
        raise HTTPException(status_code=503, detail="Image generator not available")
    
    try:
        # Use the image generator's search capability
        results = image_generator.search_stock_images(
            request.query,
            request.count,
            request.style,
            request.orientation
        )
        
        if results.get("success"):
            return {
                "success": True,
                "images": results["images"],
                "total_results": results.get("total_results", len(results["images"])),
                "query": request.query
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=results.get("error", "Failed to search images")
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image search failed: {str(e)}")