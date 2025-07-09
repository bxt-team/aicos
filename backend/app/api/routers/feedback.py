"""
Feedback and analytics endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import json
from pydantic import BaseModel

from app.core.dependencies import get_agent

router = APIRouter(prefix="/api", tags=["feedback"])

# Storage for feedback data
FEEDBACK_STORAGE_FILE = "static/feedback_storage.json"

def load_feedback_storage():
    """Load feedback data from storage"""
    if os.path.exists(FEEDBACK_STORAGE_FILE):
        with open(FEEDBACK_STORAGE_FILE, 'r') as f:
            return json.load(f)
    return {"feedback": [], "analytics": {}}

def save_feedback_storage(data):
    """Save feedback data to storage"""
    os.makedirs(os.path.dirname(FEEDBACK_STORAGE_FILE), exist_ok=True)
    with open(FEEDBACK_STORAGE_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Request models
class ImageFeedbackRequest(BaseModel):
    imagePath: str
    rating: int
    comments: Optional[str] = ""
    generationParams: Optional[Dict[str, Any]] = None
    userId: Optional[str] = None
    tags: Optional[List[str]] = []

class RegenerateWithFeedbackRequest(BaseModel):
    originalImagePath: str
    feedback: str
    rating: int
    originalPrompt: Optional[str] = None
    generationParams: Optional[Dict[str, Any]] = None
    keepOriginalStyle: Optional[bool] = True

# Feedback endpoints
@router.post("/submit-feedback")
async def submit_feedback(request: ImageFeedbackRequest):
    """Submit feedback for generated images"""
    try:
        storage = load_feedback_storage()
        
        feedback_entry = {
            "id": f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "imagePath": request.imagePath,
            "rating": request.rating,
            "comments": request.comments,
            "generationParams": request.generationParams,
            "userId": request.userId,
            "tags": request.tags,
            "timestamp": datetime.now().isoformat()
        }
        
        storage["feedback"].append(feedback_entry)
        
        # Update analytics
        if "analytics" not in storage:
            storage["analytics"] = {}
        
        analytics = storage["analytics"]
        
        # Rating distribution
        if "ratingDistribution" not in analytics:
            analytics["ratingDistribution"] = {}
        rating_key = str(request.rating)
        analytics["ratingDistribution"][rating_key] = analytics["ratingDistribution"].get(rating_key, 0) + 1
        
        # Tag frequency
        if "tagFrequency" not in analytics:
            analytics["tagFrequency"] = {}
        for tag in request.tags:
            analytics["tagFrequency"][tag] = analytics["tagFrequency"].get(tag, 0) + 1
        
        # Average rating
        all_ratings = [f["rating"] for f in storage["feedback"]]
        analytics["averageRating"] = sum(all_ratings) / len(all_ratings) if all_ratings else 0
        analytics["totalFeedback"] = len(storage["feedback"])
        
        save_feedback_storage(storage)
        
        return {
            "success": True,
            "feedbackId": feedback_entry["id"],
            "message": "Feedback submitted successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")

@router.get("/feedback-analytics")
async def get_feedback_analytics():
    """Get analytics from collected feedback"""
    try:
        storage = load_feedback_storage()
        analytics = storage.get("analytics", {})
        
        # Add time-based analytics
        feedback_list = storage.get("feedback", [])
        if feedback_list:
            # Recent feedback trends
            recent_feedback = sorted(
                feedback_list, 
                key=lambda x: x.get("timestamp", ""), 
                reverse=True
            )[:10]
            
            analytics["recentTrends"] = {
                "lastFeedbackDate": recent_feedback[0].get("timestamp") if recent_feedback else None,
                "recentAverageRating": sum(f["rating"] for f in recent_feedback) / len(recent_feedback) if recent_feedback else 0,
                "recentCount": len(recent_feedback)
            }
        
        return {
            "success": True,
            "analytics": analytics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@router.get("/feedback-recommendations")
async def get_feedback_recommendations():
    """Get AI-powered recommendations based on feedback"""
    try:
        storage = load_feedback_storage()
        feedback_list = storage.get("feedback", [])
        
        if not feedback_list:
            return {
                "success": True,
                "recommendations": [],
                "message": "No feedback data available for recommendations"
            }
        
        # Simple recommendation logic (can be enhanced with AI)
        low_rated = [f for f in feedback_list if f["rating"] <= 2]
        high_rated = [f for f in feedback_list if f["rating"] >= 4]
        
        recommendations = []
        
        # Analyze common issues in low-rated content
        if low_rated:
            common_issues = {}
            for feedback in low_rated:
                if feedback.get("comments"):
                    # Simple keyword extraction (can be improved with NLP)
                    words = feedback["comments"].lower().split()
                    for word in words:
                        if len(word) > 4:  # Focus on meaningful words
                            common_issues[word] = common_issues.get(word, 0) + 1
            
            if common_issues:
                top_issues = sorted(common_issues.items(), key=lambda x: x[1], reverse=True)[:3]
                recommendations.append({
                    "type": "improvement",
                    "title": "Common Issues to Address",
                    "description": f"Users frequently mention: {', '.join([issue[0] for issue in top_issues])}",
                    "priority": "high"
                })
        
        # Analyze successful patterns
        if high_rated:
            successful_tags = {}
            for feedback in high_rated:
                for tag in feedback.get("tags", []):
                    successful_tags[tag] = successful_tags.get(tag, 0) + 1
            
            if successful_tags:
                top_tags = sorted(successful_tags.items(), key=lambda x: x[1], reverse=True)[:3]
                recommendations.append({
                    "type": "success_pattern",
                    "title": "Successful Content Patterns",
                    "description": f"High-rated content often includes: {', '.join([tag[0] for tag in top_tags])}",
                    "priority": "medium"
                })
        
        # General recommendations based on analytics
        analytics = storage.get("analytics", {})
        avg_rating = analytics.get("averageRating", 0)
        
        if avg_rating < 3:
            recommendations.append({
                "type": "quality",
                "title": "Overall Quality Improvement Needed",
                "description": "Average rating is below 3. Consider reviewing generation parameters and prompts.",
                "priority": "high"
            })
        elif avg_rating > 4:
            recommendations.append({
                "type": "maintain",
                "title": "Maintain Current Quality",
                "description": "Content is performing well. Keep using similar approaches.",
                "priority": "low"
            })
        
        return {
            "success": True,
            "recommendations": recommendations,
            "basedOnFeedback": len(feedback_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")

@router.get("/image-feedback/{image_path:path}")
async def get_image_feedback(image_path: str):
    """Get feedback for a specific image"""
    try:
        storage = load_feedback_storage()
        feedback_list = storage.get("feedback", [])
        
        # Find feedback for the specific image
        image_feedback = [f for f in feedback_list if f.get("imagePath") == image_path]
        
        if not image_feedback:
            raise HTTPException(status_code=404, detail="No feedback found for this image")
        
        # Calculate image-specific analytics
        ratings = [f["rating"] for f in image_feedback]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            "success": True,
            "imagePath": image_path,
            "feedback": image_feedback,
            "analytics": {
                "totalFeedback": len(image_feedback),
                "averageRating": avg_rating,
                "ratingDistribution": {str(i): ratings.count(i) for i in range(1, 6)}
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get image feedback: {str(e)}")

@router.post("/regenerate-with-feedback")
async def regenerate_with_feedback(request: RegenerateWithFeedbackRequest):
    """Regenerate image based on feedback"""
    image_generator = get_agent('image_generator')
    if not image_generator:
        raise HTTPException(status_code=503, detail="Image generator not available")
    
    try:
        # Enhance prompt based on feedback
        enhanced_prompt = request.originalPrompt or ""
        if request.feedback:
            enhanced_prompt += f" {request.feedback}"
        
        # Generate new image with enhanced prompt
        result = image_generator.generate_with_feedback(
            enhanced_prompt,
            request.originalImagePath,
            request.keepOriginalStyle,
            request.generationParams
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Generation failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to regenerate with feedback: {str(e)}")