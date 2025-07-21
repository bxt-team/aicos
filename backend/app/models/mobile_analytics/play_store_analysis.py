from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class KeywordOpportunity(BaseModel):
    keyword: str
    search_volume: str
    competition: str
    relevance: float


class PainPoint(BaseModel):
    issue: str
    frequency: int
    severity: str
    percentage_of_negative: float


class PositiveHighlight(BaseModel):
    aspect: str
    mentions: int
    percentage_of_positive: float


class FeatureRequest(BaseModel):
    feature: str
    mentions: int
    priority: str


class VisualQuality(BaseModel):
    score: float
    recommendations: List[str]


class ScreenshotAnalysis(BaseModel):
    count: int
    quality_score: float
    recommendations: List[str]


class VideoAnalysis(BaseModel):
    present: bool
    quality_score: Optional[float] = None
    recommendations: List[str]


class Recommendation(BaseModel):
    category: str
    recommendation: str
    priority: str
    expected_impact: str
    implementation_difficulty: str


class PlayStoreAnalysis(BaseModel):
    """Complete Play Store listing analysis results."""
    
    # Basic App Info
    app_id: str
    app_name: str
    package_name: str
    developer: str
    category: str
    rating: float
    total_reviews: int
    downloads: str
    last_updated: str
    
    # Keyword Analysis
    keyword_analysis: Dict[str, Any] = Field(
        description="Keyword effectiveness and opportunities"
    )
    
    # Review Sentiment
    review_sentiment: Dict[str, Any] = Field(
        description="Review sentiment analysis and insights"
    )
    
    # Visual Analysis
    visual_analysis: Dict[str, Any] = Field(
        description="Analysis of app icon, screenshots, and graphics"
    )
    
    # Recommendations
    recommendations: List[Recommendation] = Field(
        description="Prioritized optimization recommendations"
    )
    
    # Competitor Analysis
    competitor_analysis: Dict[str, Any] = Field(
        description="Competitive positioning and insights"
    )
    
    # Metadata
    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    
    # Cost Tracking
    cost_estimate: Optional[Dict[str, Any]] = Field(
        None,
        description="Estimated cost for this analysis"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "app_id": "com.example.app",
                "app_name": "Example App",
                "package_name": "com.example.app",
                "developer": "Example Developer",
                "category": "Productivity",
                "rating": 4.5,
                "total_reviews": 25000,
                "downloads": "1,000,000+",
                "last_updated": "2024-01-15",
                "keyword_analysis": {
                    "primary_keywords": ["productivity", "task manager", "to-do"],
                    "keyword_density": {
                        "title": 0.3,
                        "short_description": 0.25,
                        "description": 0.15
                    }
                },
                "recommendations": [
                    {
                        "category": "Keywords",
                        "recommendation": "Add 'planner' to title",
                        "priority": "high",
                        "expected_impact": "20% traffic increase",
                        "implementation_difficulty": "easy"
                    }
                ]
            }
        }