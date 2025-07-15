import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from app.core.dependencies import get_agent
from app.agents.app_store_analyst import AppStoreAnalystAgent
from app.models.mobile_analytics import AppStoreAnalysis
from app.core.cost_tracker import cost_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/mobile-analytics", tags=["mobile-analytics"])


class AppStoreAnalysisRequest(BaseModel):
    """Request model for App Store analysis."""
    url: Optional[str] = Field(None, description="App Store URL")
    bundle_id: Optional[str] = Field(None, description="iOS Bundle ID")
    include_reviews: bool = Field(True, description="Include review sentiment analysis")
    include_visuals: bool = Field(True, description="Include visual assets analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://apps.apple.com/us/app/example-app/id123456789",
                "include_reviews": True,
                "include_visuals": True
            }
        }


class AppStoreOptimizationRequest(BaseModel):
    """Request model for App Store optimization."""
    analysis_id: Optional[str] = Field(None, description="Previous analysis ID to optimize from")
    app_data: Optional[Dict[str, Any]] = Field(None, description="App data to optimize")
    optimization_goals: List[str] = Field(
        default=["keywords", "conversion", "visibility"],
        description="Optimization goals"
    )


@router.post("/app-store/analyze", response_model=AppStoreAnalysis)
async def analyze_app_store_listing(
    request: AppStoreAnalysisRequest,
    background_tasks: BackgroundTasks
) -> AppStoreAnalysis:
    """
    Analyze an iOS App Store listing for ASO performance.
    
    Provides comprehensive analysis including:
    - Keyword effectiveness and suggestions
    - Review sentiment analysis
    - Visual assets assessment
    - Optimization recommendations
    """
    try:
        if not request.url and not request.bundle_id:
            raise HTTPException(
                status_code=400,
                detail="Either 'url' or 'bundle_id' must be provided"
            )
        
        # Get the App Store Analyst agent
        analyst_agent = get_agent("app_store_analyst")
        if not analyst_agent:
            raise HTTPException(
                status_code=500,
                detail="App Store Analyst agent not available"
            )
        
        # Prepare analysis parameters
        app_info = {
            "url": request.url,
            "bundle_id": request.bundle_id,
            "include_reviews": request.include_reviews,
            "include_visuals": request.include_visuals
        }
        
        logger.info(f"Starting App Store analysis for: {app_info}")
        
        # Run the analysis
        analysis = await analyst_agent.analyze_listing(app_info)
        
        logger.info(f"App Store analysis completed successfully")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in App Store analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/app-store/health")
async def app_store_analyst_health():
    """Check health status of App Store Analyst agent."""
    try:
        agent = get_agent("app_store_analyst")
        if not agent:
            return {
                "status": "unhealthy",
                "error": "Agent not initialized"
            }
        
        health = agent.health_check()
        return health
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.post("/app-store/batch-analyze")
async def batch_analyze_app_store(
    apps: List[AppStoreAnalysisRequest],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Analyze multiple App Store listings in batch.
    
    Useful for competitive analysis or portfolio management.
    """
    try:
        if not apps:
            raise HTTPException(
                status_code=400,
                detail="No apps provided for analysis"
            )
        
        if len(apps) > 10:
            raise HTTPException(
                status_code=400,
                detail="Maximum 10 apps per batch"
            )
        
        # Get the analyst agent
        analyst_agent = get_agent("app_store_analyst")
        if not analyst_agent:
            raise HTTPException(
                status_code=500,
                detail="App Store Analyst agent not available"
            )
        
        # Queue all analyses
        analysis_tasks = []
        for app_request in apps:
            app_info = {
                "url": app_request.url,
                "bundle_id": app_request.bundle_id,
                "include_reviews": app_request.include_reviews,
                "include_visuals": app_request.include_visuals
            }
            
            # In a real implementation, this would be queued
            background_tasks.add_task(analyst_agent.analyze_listing, app_info)
            analysis_tasks.append(app_info)
        
        return {
            "status": "batch_analysis_started",
            "apps_queued": len(apps),
            "message": "Analyses are being processed in the background"
        }
        
    except Exception as e:
        logger.error(f"Error in batch analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/app-store/historical/{app_id}")
async def get_historical_performance(app_id: str) -> Dict[str, Any]:
    """
    Get historical performance data for an app.
    
    Returns trend data showing how the app's ASO metrics have changed over time.
    """
    try:
        analyst_agent = get_agent("app_store_analyst")
        if not analyst_agent:
            raise HTTPException(
                status_code=500,
                detail="App Store Analyst agent not available"
            )
        
        historical_data = analyst_agent.get_historical_performance(app_id)
        
        if not historical_data:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for app ID: {app_id}"
            )
        
        return {
            "app_id": app_id,
            "data_points": len(historical_data),
            "historical_data": historical_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching historical data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PlayStoreAnalysisRequest(BaseModel):
    """Request model for Play Store analysis."""
    url: Optional[str] = Field(None, description="Play Store URL")
    package_name: Optional[str] = Field(None, description="Android package name")
    include_reviews: bool = Field(True, description="Include review sentiment analysis")
    include_visuals: bool = Field(True, description="Include visual assets analysis")
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://play.google.com/store/apps/details?id=com.example.app",
                "include_reviews": True,
                "include_visuals": True
            }
        }


@router.post("/play-store/analyze")
async def analyze_play_store_listing(
    request: PlayStoreAnalysisRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Analyze an Android Play Store listing for ASO performance.
    
    Provides comprehensive analysis including:
    - Keyword effectiveness and suggestions
    - Review sentiment analysis
    - Visual assets assessment
    - Optimization recommendations
    """
    try:
        if not request.url and not request.package_name:
            raise HTTPException(
                status_code=400,
                detail="Either 'url' or 'package_name' must be provided"
            )
        
        # Get the Play Store Analyst agent
        analyst_agent = get_agent("play_store_analyst")
        if not analyst_agent:
            raise HTTPException(
                status_code=500,
                detail="Play Store Analyst agent not available"
            )
        
        # Prepare analysis parameters
        app_info = {
            "url": request.url,
            "package_name": request.package_name,
            "include_reviews": request.include_reviews,
            "include_visuals": request.include_visuals
        }
        
        logger.info(f"Starting Play Store analysis for: {app_info}")
        
        # Run the analysis
        analysis = await analyst_agent.analyze_listing(app_info)
        
        logger.info(f"Play Store analysis completed successfully")
        
        return analysis.dict()
        
    except Exception as e:
        logger.error(f"Error in Play Store analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class MetaAdsAnalysisRequest(BaseModel):
    """Request model for Meta Ads analysis."""
    campaign_id: Optional[str] = Field(None, description="Meta campaign ID")
    access_token: Optional[str] = Field(None, description="Meta user access token for API authentication")
    campaign_data: Optional[Dict[str, Any]] = Field(None, description="Campaign performance data (for mock/testing)")
    date_range: Optional[Dict[str, str]] = Field(
        None, 
        description="Date range for analysis",
        example={"start": "2024-01-01", "end": "2024-01-31"}
    )
    
    class Config:
        schema_extra = {
            "example": {
                "campaign_id": "123456789",
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-01-31"
                }
            }
        }


@router.post("/meta-ads/analyze")
async def analyze_meta_ads_performance(
    request: MetaAdsAnalysisRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Analyze Meta Ads (Facebook/Instagram) campaign performance.
    
    Provides comprehensive analysis including:
    - Campaign performance metrics
    - Audience insights and targeting effectiveness
    - Creative performance and fatigue detection
    - Budget optimization recommendations
    """
    try:
        if not request.campaign_id and not request.campaign_data:
            raise HTTPException(
                status_code=400,
                detail="Either 'campaign_id' or 'campaign_data' must be provided"
            )
        
        # Get the Meta Ads Analyst agent
        analyst_agent = get_agent("meta_ads_analyst")
        if not analyst_agent:
            raise HTTPException(
                status_code=500,
                detail="Meta Ads Analyst agent not available"
            )
        
        # Prepare campaign info
        campaign_info = {
            "campaign_id": request.campaign_id,
            "access_token": request.access_token,
            "campaign_data": request.campaign_data,
            "date_range": request.date_range
        }
        
        # Add campaign data if provided (for mock testing)
        if request.campaign_data:
            campaign_info.update(request.campaign_data)
        
        logger.info(f"Starting Meta Ads analysis for campaign: {campaign_info.get('campaign_id', 'Unknown')}")
        
        # Run the analysis
        analysis = await analyst_agent.analyze_campaign(campaign_info)
        
        logger.info(f"Meta Ads analysis completed successfully")
        
        return analysis.dict()
        
    except Exception as e:
        logger.error(f"Error in Meta Ads analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class GoogleAnalyticsRequest(BaseModel):
    """Request model for Google Analytics analysis."""
    property_id: Optional[str] = Field(None, description="GA4 property ID")
    app_id: Optional[str] = Field(None, description="Mobile app ID")
    app_name: Optional[str] = Field(None, description="App name")
    date_range: Optional[Dict[str, str]] = Field(
        None, 
        description="Date range for analysis",
        example={"start": "2024-01-01", "end": "2024-01-31"}
    )
    analytics_data: Optional[Dict[str, Any]] = Field(None, description="Pre-fetched analytics data")
    
    class Config:
        schema_extra = {
            "example": {
                "property_id": "123456789",
                "app_name": "My Mobile App",
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-01-31"
                }
            }
        }


@router.post("/google-analytics/analyze")
async def analyze_google_analytics(
    request: GoogleAnalyticsRequest,
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Analyze Google Analytics 4 mobile app data.
    
    Provides comprehensive analysis including:
    - User behavior and engagement metrics
    - Conversion funnel optimization
    - Retention and churn analysis
    - Revenue and monetization insights
    - Technical performance metrics
    """
    try:
        if not request.property_id and not request.analytics_data:
            raise HTTPException(
                status_code=400,
                detail="Either 'property_id' or 'analytics_data' must be provided"
            )
        
        # Get the Google Analytics Expert agent
        analyst_agent = get_agent("google_analytics_expert")
        if not analyst_agent:
            raise HTTPException(
                status_code=500,
                detail="Google Analytics Expert agent not available"
            )
        
        # Prepare analytics info
        analytics_info = {
            "property_id": request.property_id,
            "app_id": request.app_id or "unknown",
            "app_name": request.app_name or "Mobile App",
            "date_range": request.date_range,
            "analytics_data": request.analytics_data
        }
        
        if request.date_range:
            analytics_info["start_date"] = request.date_range.get("start")
            analytics_info["end_date"] = request.date_range.get("end")
        
        logger.info(f"Starting GA4 analysis for app: {analytics_info.get('app_name')}")
        
        # Run the analysis
        analysis = await analyst_agent.analyze_app_data(analytics_info)
        
        logger.info(f"Google Analytics analysis completed successfully")
        
        return analysis.dict()
        
    except Exception as e:
        logger.error(f"Error in Google Analytics analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/play-store/analyses")
async def list_play_store_analyses() -> Dict[str, Any]:
    """
    List all saved Play Store analyses.
    
    Returns a list of analysis summaries with basic info.
    """
    try:
        # Get the Play Store Analyst agent
        analyst_agent = get_agent("play_store_analyst")
        if not analyst_agent:
            raise HTTPException(
                status_code=500,
                detail="Play Store Analyst agent not available"
            )
        
        analyses = analyst_agent.get_all_analyses()
        
        return {
            "analyses": analyses,
            "total": len(analyses)
        }
        
    except Exception as e:
        logger.error(f"Error listing Play Store analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/play-store/analyses/{analysis_id}")
async def get_play_store_analysis(analysis_id: str) -> Dict[str, Any]:
    """
    Get a specific Play Store analysis by ID.
    
    Returns the full analysis details.
    """
    try:
        # Get the Play Store Analyst agent
        analyst_agent = get_agent("play_store_analyst")
        if not analyst_agent:
            raise HTTPException(
                status_code=500,
                detail="Play Store Analyst agent not available"
            )
        
        analysis = analyst_agent.get_analysis_by_id(analysis_id)
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis {analysis_id} not found"
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Play Store analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/play-store/analyses/{analysis_id}")
async def delete_play_store_analysis(analysis_id: str) -> Dict[str, Any]:
    """
    Delete a specific Play Store analysis by ID.
    
    Returns success status.
    """
    try:
        # Get the Play Store Analyst agent
        analyst_agent = get_agent("play_store_analyst")
        if not analyst_agent:
            raise HTTPException(
                status_code=500,
                detail="Play Store Analyst agent not available"
            )
        
        success = analyst_agent.delete_analysis(analysis_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis {analysis_id} not found or could not be deleted"
            )
        
        return {
            "success": True,
            "message": f"Analysis {analysis_id} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting Play Store analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/session")
async def get_session_costs() -> Dict[str, Any]:
    """
    Get cost summary for the current session.
    
    Returns breakdown of costs by agent and model.
    """
    try:
        return cost_tracker.get_session_summary()
    except Exception as e:
        logger.error(f"Error getting session costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/daily/{date}")
async def get_daily_costs(date: str) -> Dict[str, Any]:
    """
    Get cost summary for a specific date.
    
    Args:
        date: Date in YYYY-MM-DD format
        
    Returns:
        Daily cost breakdown
    """
    try:
        return cost_tracker.get_daily_costs(date)
    except Exception as e:
        logger.error(f"Error getting daily costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/costs/monthly/{year}/{month}")
async def get_monthly_costs(year: int, month: int) -> Dict[str, Any]:
    """
    Get cost summary for a specific month.
    
    Args:
        year: Year (e.g., 2024)
        month: Month (1-12)
        
    Returns:
        Monthly cost breakdown
    """
    try:
        if month < 1 or month > 12:
            raise HTTPException(
                status_code=400,
                detail="Month must be between 1 and 12"
            )
        
        return cost_tracker.get_monthly_summary(year, month)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monthly costs: {e}")
        raise HTTPException(status_code=500, detail=str(e))