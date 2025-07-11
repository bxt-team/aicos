"""API router for Meta Threads functionality."""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ...core.dependencies import (
    get_threads_analysis_agent,
    get_content_strategy_agent,
    get_post_generator_agent,
    get_approval_agent,
    get_scheduler_agent,
    get_supabase_client
)
from ...agents.threads_analysis_agent import ThreadsAnalysisAgent
from ...agents.content_strategy_agent import ContentStrategyAgent
from ...agents.post_generator_agent import PostGeneratorAgent
from ...agents.approval_agent import ApprovalAgent
from ...agents.scheduler_agent import SchedulerAgent
from ...services.supabase_client import SupabaseClient

router = APIRouter(prefix="/api/threads", tags=["threads"])


# Request/Response Models
class AnalyzeProfilesRequest(BaseModel):
    """Request model for analyzing Threads profiles."""
    handles: List[str] = Field(..., description="List of Threads handles to analyze")


class CreateStrategyRequest(BaseModel):
    """Request model for creating content strategy."""
    analysis_id: Optional[str] = Field(None, description="ID of previous analysis to use")
    target_audience: Optional[str] = Field(None, description="Target audience description")


class GeneratePostsRequest(BaseModel):
    """Request model for generating posts."""
    count: int = Field(5, ge=1, le=20, description="Number of posts to generate")
    period: Optional[int] = Field(None, ge=1, le=7, description="7 Cycles period (1-7)")
    theme: Optional[str] = Field(None, description="Theme for posts")
    include_affirmations: bool = Field(True, description="Include affirmations in posts")
    include_activities: bool = Field(True, description="Include activities in posts")


class ApprovalDecisionRequest(BaseModel):
    """Request model for approval decisions."""
    approval_id: str = Field(..., description="Approval request ID")
    decision: str = Field(..., description="Decision: approved, rejected, needs_revision")
    approver: str = Field("user", description="Who made the decision")
    notes: Optional[str] = Field(None, description="Additional notes")


class SchedulePostsRequest(BaseModel):
    """Request model for scheduling posts."""
    post_ids: Optional[List[str]] = Field(None, description="Specific post IDs to schedule")
    start_date: Optional[str] = Field(None, description="Start date for scheduling")
    end_date: Optional[str] = Field(None, description="End date for scheduling")
    posts_per_week: int = Field(3, ge=1, le=7, description="Posts per week")


# Endpoints
@router.post("/analyze")
async def analyze_profiles(
    request: AnalyzeProfilesRequest,
    agent: ThreadsAnalysisAgent = Depends(get_threads_analysis_agent)
):
    """Analyze Threads profiles to extract patterns and strategies."""
    try:
        result = await agent.analyze_profiles(request.handles)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/latest")
async def get_latest_analysis(
    agent: ThreadsAnalysisAgent = Depends(get_threads_analysis_agent)
):
    """Get the latest analysis results."""
    analysis = agent.get_latest_analysis()
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found")
    return analysis


@router.post("/strategy")
async def create_strategy(
    request: CreateStrategyRequest,
    analysis_agent: ThreadsAnalysisAgent = Depends(get_threads_analysis_agent),
    strategy_agent: ContentStrategyAgent = Depends(get_content_strategy_agent)
):
    """Create a content strategy based on analysis."""
    try:
        # Get analysis if not provided
        analysis = None
        if request.analysis_id:
            # In real implementation, fetch by ID
            analysis = analysis_agent.get_latest_analysis()
        else:
            analysis = analysis_agent.get_latest_analysis()
        
        if not analysis:
            raise HTTPException(status_code=400, detail="No analysis available. Please analyze profiles first.")
        
        result = await strategy_agent.create_strategy(analysis, request.target_audience)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/latest")
async def get_latest_strategy(
    agent: ContentStrategyAgent = Depends(get_content_strategy_agent)
):
    """Get the latest content strategy."""
    strategy = agent.get_latest_strategy()
    if not strategy:
        raise HTTPException(status_code=404, detail="No strategy found")
    return strategy


@router.post("/posts/generate")
async def generate_posts(
    request: GeneratePostsRequest,
    strategy_agent: ContentStrategyAgent = Depends(get_content_strategy_agent),
    generator_agent: PostGeneratorAgent = Depends(get_post_generator_agent)
):
    """Generate Threads posts based on strategy."""
    try:
        # Get latest strategy
        strategy = strategy_agent.get_latest_strategy()
        
        result = await generator_agent.generate_posts(
            count=request.count,
            strategy=strategy,
            period=request.period,
            theme=request.theme,
            include_affirmations=request.include_affirmations,
            include_activities=request.include_activities
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/latest")
async def get_latest_posts(
    agent: PostGeneratorAgent = Depends(get_post_generator_agent)
):
    """Get the latest generated posts."""
    posts = agent.get_latest_posts()
    if not posts:
        raise HTTPException(status_code=404, detail="No posts found")
    return {"posts": posts}


@router.post("/posts/approve")
async def request_approval(
    generator_agent: PostGeneratorAgent = Depends(get_post_generator_agent),
    approval_agent: ApprovalAgent = Depends(get_approval_agent)
):
    """Request approval for the latest generated posts."""
    try:
        # Get latest posts
        posts = generator_agent.get_latest_posts()
        if not posts:
            raise HTTPException(status_code=404, detail="No posts to approve")
        
        result = await approval_agent.request_approval(posts)
        
        # Simulate Telegram approval
        if result["success"]:
            approval_request = result["approval_request"]
            telegram_result = approval_agent.simulate_telegram_approval(approval_request)
            
            # Auto-process the decision
            decision_result = await approval_agent.process_approval_decision(
                approval_request["id"],
                telegram_result["decision"],
                telegram_result["approver"],
                telegram_result["notes"]
            )
            
            result["telegram_simulation"] = telegram_result
            result["decision_result"] = decision_result
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/pending")
async def get_pending_approvals(
    agent: ApprovalAgent = Depends(get_approval_agent)
):
    """Get all pending approval requests."""
    try:
        pending = await agent.get_pending_approvals()
        return {"pending_approvals": pending}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/decide")
async def process_approval_decision(
    request: ApprovalDecisionRequest,
    agent: ApprovalAgent = Depends(get_approval_agent)
):
    """Process an approval decision."""
    try:
        result = await agent.process_approval_decision(
            request.approval_id,
            request.decision,
            request.approver,
            request.notes
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/history")
async def get_approval_history(
    agent: ApprovalAgent = Depends(get_approval_agent)
):
    """Get approval history."""
    history = agent.get_approval_history()
    return {"history": history}


@router.post("/schedule")
async def schedule_posts(
    request: SchedulePostsRequest,
    generator_agent: PostGeneratorAgent = Depends(get_post_generator_agent),
    scheduler_agent: SchedulerAgent = Depends(get_scheduler_agent)
):
    """Schedule approved posts."""
    try:
        # Get posts to schedule
        if request.post_ids:
            # In real implementation, fetch specific posts
            posts = generator_agent.get_latest_posts()
        else:
            posts = generator_agent.get_latest_posts()
        
        if not posts:
            raise HTTPException(status_code=404, detail="No posts to schedule")
        
        # Parse dates if provided
        start_date = None
        end_date = None
        if request.start_date:
            start_date = datetime.fromisoformat(request.start_date)
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date)
        
        result = await scheduler_agent.schedule_posts(
            posts,
            start_date,
            end_date,
            request.posts_per_week
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/latest")
async def get_latest_schedule(
    agent: SchedulerAgent = Depends(get_scheduler_agent)
):
    """Get the latest schedule."""
    schedule = agent.get_latest_schedule()
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found")
    return schedule


@router.get("/schedule/upcoming")
async def get_upcoming_posts(
    days: int = 7,
    agent: SchedulerAgent = Depends(get_scheduler_agent)
):
    """Get posts scheduled for the next N days."""
    upcoming = agent.get_upcoming_posts(days)
    return {"upcoming_posts": upcoming, "days": days}


@router.post("/publish")
async def publish_scheduled_posts(
    background_tasks: BackgroundTasks,
    agent: SchedulerAgent = Depends(get_scheduler_agent)
):
    """Publish posts that are ready to be published."""
    try:
        # Run publishing in background
        background_tasks.add_task(agent.publish_scheduled_posts)
        
        return {
            "message": "Publishing task started",
            "status": "processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activities")
async def get_activities(
    period: Optional[int] = None,
    tags: Optional[List[str]] = None,
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Get activities from the catalog."""
    try:
        activities = await supabase.get_activities(period=period, tags=tags)
        return {"activities": [a.dict() for a in activities]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts")
async def get_threads_posts(
    status: Optional[str] = None,
    limit: int = 50,
    supabase: SupabaseClient = Depends(get_supabase_client)
):
    """Get Threads posts from database."""
    try:
        posts = await supabase.get_threads_posts(status=status, limit=limit)
        return {"posts": [p.dict() for p in posts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(
    analysis_agent: ThreadsAnalysisAgent = Depends(get_threads_analysis_agent),
    strategy_agent: ContentStrategyAgent = Depends(get_content_strategy_agent),
    generator_agent: PostGeneratorAgent = Depends(get_post_generator_agent),
    approval_agent: ApprovalAgent = Depends(get_approval_agent),
    scheduler_agent: SchedulerAgent = Depends(get_scheduler_agent)
):
    """Check health status of all Threads agents."""
    return {
        "status": "healthy",
        "agents": {
            "analysis": analysis_agent.health_check(),
            "strategy": strategy_agent.health_check(),
            "generator": generator_agent.health_check(),
            "approval": approval_agent.health_check(),
            "scheduler": scheduler_agent.health_check()
        }
    }