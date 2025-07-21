from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ChannelPerformance(BaseModel):
    channel: str
    users: int
    new_users: int
    conversion_rate: float
    avg_session_duration: float


class ScreenPerformance(BaseModel):
    screen_name: str
    views: int
    unique_views: int
    avg_time: float
    exit_rate: float


class UserPath(BaseModel):
    path: str
    users: int
    completion_rate: float


class DropOffPoint(BaseModel):
    screen: str
    drop_off_rate: float
    users_lost: int


class Event(BaseModel):
    name: str
    count: int


class Goal(BaseModel):
    goal_name: str
    conversion_rate: float
    completions: int
    value: float


class FunnelStep(BaseModel):
    name: str
    users: int
    drop_off: float


class CohortData(BaseModel):
    name: str
    day_30_retention: float
    ltv: float


class PerformanceIssue(BaseModel):
    issue: str
    affected_users: int
    avg_load_time: float


class GoogleAnalyticsRecommendation(BaseModel):
    category: str
    recommendation: str
    priority: str
    expected_impact: str
    implementation_difficulty: str


class GoogleAnalyticsAnalysis(BaseModel):
    """Complete Google Analytics 4 mobile app analysis results."""
    
    # App Info
    app_id: str
    app_name: str
    property_id: str
    date_range: Dict[str, str]
    
    # User Metrics
    user_metrics: Dict[str, Any] = Field(
        description="Core user metrics and engagement data"
    )
    
    # Acquisition Analysis
    acquisition_analysis: Dict[str, Any] = Field(
        description="User acquisition channels and attribution"
    )
    
    # Behavior Analysis
    behavior_analysis: Dict[str, Any] = Field(
        description="User behavior, flows, and interactions"
    )
    
    # Conversion Analysis
    conversion_analysis: Dict[str, Any] = Field(
        description="Conversion funnels and revenue metrics"
    )
    
    # Retention Analysis
    retention_analysis: Dict[str, Any] = Field(
        description="User retention and cohort analysis"
    )
    
    # Recommendations
    recommendations: List[GoogleAnalyticsRecommendation] = Field(
        description="Prioritized optimization recommendations"
    )
    
    # Technical Performance
    technical_performance: Dict[str, Any] = Field(
        description="App technical performance metrics"
    )
    
    # Metadata
    analysis_timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "app_id": "com.example.app",
                "app_name": "Example App",
                "property_id": "123456789",
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-01-31"
                },
                "user_metrics": {
                    "total_users": 100000,
                    "new_users": 30000,
                    "active_users": {
                        "daily": 20000,
                        "weekly": 50000,
                        "monthly": 80000
                    }
                },
                "retention_analysis": {
                    "retention_curve": {
                        "day_1": 60.0,
                        "day_7": 30.0,
                        "day_30": 15.0
                    }
                },
                "recommendations": [
                    {
                        "category": "Retention",
                        "recommendation": "Implement onboarding improvements",
                        "priority": "high",
                        "expected_impact": "20% better day-7 retention",
                        "implementation_difficulty": "medium"
                    }
                ]
            }
        }