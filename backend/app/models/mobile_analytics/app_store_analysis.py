from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class KeywordInsight(BaseModel):
    """Model for keyword analysis insights."""
    keyword: str
    density: float
    placement_quality: str
    competition_level: Optional[str] = None
    recommendation: Optional[str] = None


class ReviewSentiment(BaseModel):
    """Model for review sentiment analysis."""
    overall_sentiment: float
    sentiment_label: str
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    common_themes: List[Dict[str, Any]]
    pain_points: List[Dict[str, Any]]
    positive_highlights: List[Dict[str, Any]]


class VisualAssessment(BaseModel):
    """Model for visual assets assessment."""
    icon_quality: Dict[str, Any]
    screenshot_analysis: Dict[str, Any]
    preview_video_analysis: Optional[Dict[str, Any]] = None
    overall_visual_score: int
    recommendations: List[str]


class OptimizationRecommendation(BaseModel):
    """Model for optimization recommendations."""
    category: str = Field(..., description="Category of recommendation (e.g., 'metadata', 'visuals', 'keywords')")
    priority: str = Field(..., description="Priority level: high, medium, low")
    recommendation: str = Field(..., description="Specific recommendation")
    expected_impact: str = Field(..., description="Expected impact on ASO performance")
    implementation_difficulty: str = Field(..., description="Easy, Medium, Hard")


class AppStoreAnalysis(BaseModel):
    """Complete App Store analysis result model."""
    app_id: str
    bundle_id: Optional[str] = None
    app_name: Optional[str] = None
    analysis_timestamp: datetime
    
    # Core listing data
    listing_data: Optional[Dict[str, Any]] = Field(default=None, description="Raw listing data")
    
    # Analysis results
    listing_analysis: Dict[str, Any] = Field(..., description="Detailed listing analysis")
    keyword_insights: Dict[str, Any] = Field(..., description="Keyword analysis and suggestions")
    review_sentiment: Optional[ReviewSentiment] = None
    visual_assessment: Optional[VisualAssessment] = None
    
    # Optimization score
    optimization_score: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Overall optimization score and breakdown"
    )
    
    # Recommendations
    recommendations: List[OptimizationRecommendation] = Field(
        default_factory=list,
        description="Prioritized list of optimization recommendations"
    )
    
    # Competitive analysis
    competitive_insights: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Insights about competitors and market positioning"
    )
    
    # Historical comparison (if available)
    trend_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Trends and changes since last analysis"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AppStoreOptimization(BaseModel):
    """Model for App Store optimization suggestions."""
    original_data: AppStoreAnalysis
    optimized_metadata: Dict[str, str] = Field(
        ..., 
        description="Optimized title, subtitle, keywords, description"
    )
    visual_recommendations: List[Dict[str, Any]] = Field(
        ...,
        description="Specific recommendations for visual assets"
    )
    a_b_test_suggestions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="A/B testing ideas for different elements"
    )
    expected_improvements: Dict[str, Any] = Field(
        ...,
        description="Expected improvements in metrics"
    )
    implementation_plan: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Step-by-step implementation plan"
    )