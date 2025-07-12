from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.core.dependencies import get_agent


router = APIRouter(prefix="/api/x", tags=["x"])


class XAnalysisRequest(BaseModel):
    profile_handles: List[str]


class XStrategyRequest(BaseModel):
    use_latest_analysis: bool = True
    analysis_data: Optional[Dict[str, Any]] = None


class XPostGenerationRequest(BaseModel):
    period: int
    post_type: str = "mixed"  # single, thread, poll, mixed
    count: int = 5
    use_latest_strategy: bool = True


class XApprovalRequest(BaseModel):
    posts: List[Dict[str, Any]]
    requester: str = "user"


class XApprovalDecision(BaseModel):
    approval_id: str
    decisions: Dict[int, str]  # post_index -> decision (approved/rejected)


class XScheduleRequest(BaseModel):
    approved_posts: List[Dict[str, Any]]
    scheduling_strategy: str = "optimal"  # optimal, aggressive, conservative
    start_date: Optional[datetime] = None


class XRescheduleRequest(BaseModel):
    post_id: str
    new_time: datetime


@router.post("/analyze")
async def analyze_x_profiles(request: XAnalysisRequest) -> Dict[str, Any]:
    """Analyze X (Twitter) profiles to extract content patterns and insights."""
    try:
        x_analysis_agent = get_agent("x_analysis")
        if not x_analysis_agent:
            raise HTTPException(status_code=500, detail="X analysis agent not initialized")
        
        result = x_analysis_agent.analyze_profile(request.profile_handles)
        return {
            "success": True,
            "analysis": result,
            "profiles_analyzed": request.profile_handles,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/latest")
async def get_latest_x_analysis() -> Dict[str, Any]:
    """Get the most recent X profile analysis."""
    try:
        x_analysis_agent = get_agent("x_analysis")
        if not x_analysis_agent:
            raise HTTPException(status_code=500, detail="X analysis agent not initialized")
        
        analysis = x_analysis_agent.get_latest_analysis()
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return {
            "success": True,
            "analysis": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategy")
async def create_x_strategy(request: XStrategyRequest) -> Dict[str, Any]:
    """Create a comprehensive X content strategy based on analysis."""
    try:
        x_strategy_agent = get_agent("x_strategy")
        if not x_strategy_agent:
            raise HTTPException(status_code=500, detail="X strategy agent not initialized")
        
        analysis_data = None
        if request.use_latest_analysis and not request.analysis_data:
            x_analysis_agent = get_agent("x_analysis")
            if x_analysis_agent:
                analysis_data = x_analysis_agent.get_latest_analysis()
        else:
            analysis_data = request.analysis_data
        
        result = x_strategy_agent.create_strategy(analysis_data)
        return {
            "success": True,
            "strategy": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/latest")
async def get_latest_x_strategy() -> Dict[str, Any]:
    """Get the most recent X content strategy."""
    try:
        x_strategy_agent = get_agent("x_strategy")
        if not x_strategy_agent:
            raise HTTPException(status_code=500, detail="X strategy agent not initialized")
        
        strategy = x_strategy_agent.get_latest_strategy()
        if "error" in strategy:
            raise HTTPException(status_code=404, detail=strategy["error"])
        
        return {
            "success": True,
            "strategy": strategy
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/posts/generate")
async def generate_x_posts(request: XPostGenerationRequest) -> Dict[str, Any]:
    """Generate X posts based on strategy and period."""
    try:
        x_generator_agent = get_agent("x_generator")
        if not x_generator_agent:
            raise HTTPException(status_code=500, detail="X post generator agent not initialized")
        
        strategy_data = None
        if request.use_latest_strategy:
            x_strategy_agent = get_agent("x_strategy")
            if x_strategy_agent:
                strategy_data = x_strategy_agent.get_latest_strategy()
        
        posts = x_generator_agent.generate_posts(
            period=request.period,
            post_type=request.post_type,
            count=request.count,
            strategy_data=strategy_data
        )
        
        return {
            "success": True,
            "posts": posts,
            "period": request.period,
            "count": len(posts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/latest")
async def get_latest_x_posts(period: Optional[int] = None) -> Dict[str, Any]:
    """Get the most recently generated X posts."""
    try:
        x_generator_agent = get_agent("x_generator")
        if not x_generator_agent:
            raise HTTPException(status_code=500, detail="X post generator agent not initialized")
        
        posts = x_generator_agent.get_latest_posts(period)
        return {
            "success": True,
            "posts": posts,
            "period": period,
            "count": len(posts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/posts/approve")
async def submit_x_posts_for_approval(request: XApprovalRequest) -> Dict[str, Any]:
    """Submit X posts for approval review."""
    try:
        x_approval_agent = get_agent("x_approval")
        if not x_approval_agent:
            raise HTTPException(status_code=500, detail="X approval agent not initialized")
        
        result = x_approval_agent.submit_for_approval(request.posts, request.requester)
        return {
            "success": True,
            "approval_request": result,
            "posts_count": len(request.posts),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/pending")
async def get_pending_x_approvals() -> Dict[str, Any]:
    """Get all pending X post approvals."""
    try:
        x_approval_agent = get_agent("x_approval")
        if not x_approval_agent:
            raise HTTPException(status_code=500, detail="X approval agent not initialized")
        
        pending = x_approval_agent.get_pending_approvals()
        return {
            "success": True,
            "pending_approvals": pending,
            "count": len(pending)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/approvals/decide")
async def process_x_approval_decision(request: XApprovalDecision) -> Dict[str, Any]:
    """Process approval decisions for X posts."""
    try:
        x_approval_agent = get_agent("x_approval")
        if not x_approval_agent:
            raise HTTPException(status_code=500, detail="X approval agent not initialized")
        
        result = x_approval_agent.process_approval_decision(
            request.approval_id,
            request.decisions
        )
        
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        
        return {
            "success": True,
            "approval_result": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/approvals/history")
async def get_x_approval_history() -> Dict[str, Any]:
    """Get X post approval history."""
    try:
        x_approval_agent = get_agent("x_approval")
        if not x_approval_agent:
            raise HTTPException(status_code=500, detail="X approval agent not initialized")
        
        history = x_approval_agent.get_approval_history()
        return {
            "success": True,
            "approval_history": history,
            "count": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule")
async def schedule_x_posts(request: XScheduleRequest) -> Dict[str, Any]:
    """Schedule approved X posts for publishing."""
    try:
        x_scheduler_agent = get_agent("x_scheduler")
        if not x_scheduler_agent:
            raise HTTPException(status_code=500, detail="X scheduler agent not initialized")
        
        result = x_scheduler_agent.schedule_posts(
            approved_posts=request.approved_posts,
            scheduling_strategy=request.scheduling_strategy,
            start_date=request.start_date
        )
        
        return {
            "success": True,
            "schedule": result,
            "posts_scheduled": result["posts_count"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/latest")
async def get_latest_x_schedule() -> Dict[str, Any]:
    """Get the most recent X posting schedule."""
    try:
        x_scheduler_agent = get_agent("x_scheduler")
        if not x_scheduler_agent:
            raise HTTPException(status_code=500, detail="X scheduler agent not initialized")
        
        schedule = x_scheduler_agent.get_latest_schedule()
        if "error" in schedule:
            raise HTTPException(status_code=404, detail=schedule["error"])
        
        return {
            "success": True,
            "schedule": schedule
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/upcoming")
async def get_upcoming_x_posts(days: int = 7) -> Dict[str, Any]:
    """Get X posts scheduled for the next N days."""
    try:
        x_scheduler_agent = get_agent("x_scheduler")
        if not x_scheduler_agent:
            raise HTTPException(status_code=500, detail="X scheduler agent not initialized")
        
        upcoming = x_scheduler_agent.get_upcoming_posts(days)
        return {
            "success": True,
            "upcoming_posts": upcoming,
            "days": days,
            "count": len(upcoming)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
async def publish_scheduled_x_posts() -> Dict[str, Any]:
    """Publish X posts that are due."""
    try:
        x_scheduler_agent = get_agent("x_scheduler")
        if not x_scheduler_agent:
            raise HTTPException(status_code=500, detail="X scheduler agent not initialized")
        
        result = x_scheduler_agent.publish_scheduled_posts()
        return {
            "success": True,
            "publish_result": result,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/schedule/reschedule")
async def reschedule_x_post(request: XRescheduleRequest) -> Dict[str, Any]:
    """Reschedule a specific X post."""
    try:
        x_scheduler_agent = get_agent("x_scheduler")
        if not x_scheduler_agent:
            raise HTTPException(status_code=500, detail="X scheduler agent not initialized")
        
        result = x_scheduler_agent.reschedule_post(request.post_id, request.new_time)
        
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result.get("error", "Post not found"))
        
        return {
            "success": True,
            "reschedule_result": result,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def x_agents_health_check() -> Dict[str, Any]:
    """Check health status of all X agents."""
    try:
        agents = ["x_analysis", "x_strategy", "x_generator", "x_approval", "x_scheduler"]
        health_status = {}
        
        for agent_name in agents:
            agent = get_agent(agent_name)
            if agent and hasattr(agent, 'health_check'):
                health_status[agent_name] = agent.health_check()
            else:
                health_status[agent_name] = {
                    "status": "not_initialized",
                    "agent": agent_name
                }
        
        all_healthy = all(
            status.get("status") == "healthy" 
            for status in health_status.values()
        )
        
        return {
            "success": True,
            "overall_status": "healthy" if all_healthy else "degraded",
            "agents": health_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Additional endpoints for activities integration
@router.get("/activities")
async def get_activities_for_x(period: Optional[int] = None) -> Dict[str, Any]:
    """Get activities suitable for X content creation."""
    try:
        from app.services.supabase_client import get_all_activities, get_activities_by_period
        
        if period:
            activities = get_activities_by_period(period)
        else:
            activities = get_all_activities()
        
        # Filter and format for X
        x_activities = []
        for activity in activities[:20]:  # Limit to 20
            x_activities.append({
                "id": activity["id"],
                "title": activity["title"],
                "description": activity["description"][:280],  # X character limit
                "period": activity["period"],
                "hashtag_suggestions": [
                    f"#7Cycles",
                    f"#Period{activity['period']}",
                    f"#{activity['title'].replace(' ', '')[:15]}"
                ],
                "tweet_potential": "high" if len(activity["description"]) < 200 else "thread"
            })
        
        return {
            "success": True,
            "activities": x_activities,
            "count": len(x_activities),
            "period": period
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))