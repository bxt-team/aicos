from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PerformanceSegment(BaseModel):
    segment: str
    installs: int
    cpi: float
    performance_index: float


class PlacementMetrics(BaseModel):
    ctr: float
    cpi: float


class GeographicPerformance(BaseModel):
    location: str
    installs: int
    cpi: float


class CreativeMetrics(BaseModel):
    creative_id: str
    format: str
    impressions: int
    ctr: float
    installs: int
    cpi: float
    engagement_rate: float


class BudgetReallocation(BaseModel):
    from_placement: str = Field(alias="from")
    to_placement: str = Field(alias="to")
    amount: float
    expected_cpi_reduction: float


class MetaAdsRecommendation(BaseModel):
    category: str
    recommendation: str
    priority: str
    expected_impact: str
    implementation_difficulty: str


class MetaAdsAnalysis(BaseModel):
    """Complete Meta Ads campaign analysis results."""
    
    # Campaign Info
    campaign_id: str
    campaign_name: str
    app_id: str
    platform: str
    date_range: Dict[str, str]
    
    # Performance Metrics
    performance_metrics: Dict[str, Any] = Field(
        description="Overall campaign performance metrics"
    )
    
    # Audience Insights
    audience_insights: Dict[str, Any] = Field(
        description="Audience performance and targeting insights"
    )
    
    # Creative Performance
    creative_performance: Dict[str, Any] = Field(
        description="Ad creative performance analysis"
    )
    
    # Recommendations
    recommendations: List[MetaAdsRecommendation] = Field(
        description="Prioritized optimization recommendations"
    )
    
    # Optimization Opportunities
    optimization_opportunities: Dict[str, Any] = Field(
        description="Specific optimization opportunities identified"
    )
    
    # Metadata
    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    
    class Config:
        schema_extra = {
            "example": {
                "campaign_id": "123456789",
                "campaign_name": "Mobile App Install Campaign",
                "app_id": "com.example.app",
                "platform": "meta_ads",
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-01-31"
                },
                "performance_metrics": {
                    "impressions": 1000000,
                    "clicks": 30000,
                    "ctr": 3.0,
                    "installs": 1500,
                    "cost_per_install": 15.00,
                    "roas": 2.5
                },
                "recommendations": [
                    {
                        "category": "Audience",
                        "recommendation": "Expand lookalike audience to 3%",
                        "priority": "high",
                        "expected_impact": "20% more installs",
                        "implementation_difficulty": "easy"
                    }
                ]
            }
        }