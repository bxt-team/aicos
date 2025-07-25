from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from app.core.supabase_auth import get_current_user as get_current_user_supabase
from app.services.credit_service import CreditService
from app.core.exceptions import InsufficientCreditsError, CreditLimitExceededError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/credits", tags=["credits"])

# Request/Response models
class CreditConsumeRequest(BaseModel):
    amount: float
    project_id: Optional[str] = None
    department_id: Optional[str] = None
    agent_type: Optional[str] = None
    action: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class CreditAddRequest(BaseModel):
    amount: float
    type: str = "bonus"  # bonus, adjustment
    description: Optional[str] = None

class CreditReserveRequest(BaseModel):
    amount: float
    reservation_id: str

class CreditReleaseRequest(BaseModel):
    amount: float
    reservation_id: str
    consume: bool = False

class DepartmentLimitRequest(BaseModel):
    daily_limit: Optional[float] = None
    monthly_limit: Optional[float] = None

# Endpoints
@router.get("/balance")
async def get_credit_balance(
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get current credit balance for the user's organization"""
    try:
        # Get user's organization
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        credit_service = CreditService()
        balance = await credit_service.get_balance(org_id)
        
        return {
            "success": True,
            "balance": balance
        }
    except Exception as e:
        logger.error(f"Error getting balance: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/use")
async def consume_credits(
    request: CreditConsumeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Consume credits for an action"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        credit_service = CreditService()
        
        # If agent_type and action provided, get configured cost
        if request.agent_type and request.action:
            cost = await credit_service.get_cost_for_action(
                request.agent_type, request.action
            )
            amount = cost
        else:
            amount = request.amount
        
        success = await credit_service.consume_credits(
            organization_id=org_id,
            amount=amount,
            project_id=request.project_id,
            department_id=request.department_id,
            agent_type=request.agent_type,
            action=request.action,
            metadata=request.metadata,
            user_id=str(current_user["user_id"])
        )
        
        if not success:
            raise InsufficientCreditsError("Insufficient credits")
        
        # Get updated balance
        balance = await credit_service.get_balance(org_id)
        
        return {
            "success": True,
            "credits_consumed": amount,
            "balance_after": balance["available"]
        }
        
    except InsufficientCreditsError:
        raise HTTPException(status_code=402, detail="Insufficient credits")
    except CreditLimitExceededError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        logger.error(f"Error consuming credits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage")
async def get_credit_usage(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    project_id: Optional[str] = Query(None),
    department_id: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get credit usage history"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        credit_service = CreditService()
        usage = await credit_service.get_usage_history(
            organization_id=org_id,
            start_date=start_date,
            end_date=end_date,
            project_id=project_id,
            department_id=department_id,
            limit=limit
        )
        
        return {
            "success": True,
            "usage": usage,
            "count": len(usage)
        }
    except Exception as e:
        logger.error(f"Error getting usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/usage/summary")
async def get_usage_summary(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    group_by: str = Query("day", regex="^(day|agent|project|department)$"),
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get aggregated usage summary"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        credit_service = CreditService()
        summary = await credit_service.get_usage_summary(
            organization_id=org_id,
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        return {
            "success": True,
            "summary": summary,
            "group_by": group_by,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error getting usage summary: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions")
async def get_transactions(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get credit transaction history"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        credit_service = CreditService()
        transactions = await credit_service.get_transaction_history(
            organization_id=org_id,
            start_date=start_date,
            end_date=end_date,
            transaction_type=type,
            limit=limit
        )
        
        return {
            "success": True,
            "transactions": transactions,
            "count": len(transactions)
        }
    except Exception as e:
        logger.error(f"Error getting transactions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/costs")
async def get_action_costs(
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get configured costs for agent actions"""
    try:
        credit_service = CreditService()
        costs = await credit_service.get_agent_action_costs()
        
        return {
            "success": True,
            "costs": costs
        }
    except Exception as e:
        logger.error(f"Error getting action costs: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/add")
async def add_credits_admin(
    request: CreditAddRequest,
    organization_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Add credits to an organization (admin only)"""
    try:
        # Check if user is admin
        if not current_user.get("is_admin"):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        credit_service = CreditService()
        new_balance = await credit_service.add_credits(
            organization_id=organization_id,
            amount=request.amount,
            transaction_type=request.type,
            description=request.description
        )
        
        return {
            "success": True,
            "credits_added": request.amount,
            "new_balance": new_balance
        }
    except Exception as e:
        logger.error(f"Error adding credits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reserve")
async def reserve_credits(
    request: CreditReserveRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Reserve credits for future use"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        credit_service = CreditService()
        success = await credit_service.reserve_credits(
            organization_id=org_id,
            amount=request.amount,
            reservation_id=request.reservation_id
        )
        
        if not success:
            raise HTTPException(
                status_code=402, 
                detail="Insufficient credits to reserve"
            )
        
        return {
            "success": True,
            "reserved": request.amount,
            "reservation_id": request.reservation_id
        }
    except Exception as e:
        logger.error(f"Error reserving credits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/release")
async def release_reserved_credits(
    request: CreditReleaseRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Release or consume reserved credits"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        credit_service = CreditService()
        await credit_service.release_reserved_credits(
            organization_id=org_id,
            amount=request.amount,
            reservation_id=request.reservation_id,
            consume=request.consume
        )
        
        return {
            "success": True,
            "released": request.amount,
            "consumed": request.consume,
            "reservation_id": request.reservation_id
        }
    except Exception as e:
        logger.error(f"Error releasing credits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/departments/{department_id}/limits")
async def get_department_limits(
    department_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get credit limits for a department"""
    try:
        # Verify user has access to this department
        # TODO: Add proper authorization check
        
        from supabase import create_client, Client
        import os
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not url or not key:
            raise ValueError("Supabase credentials not configured")
        
        supabase = create_client(url, key)
        
        result = supabase.table("department_credit_limits").select("*").eq(
            "department_id", department_id
        ).execute()
        
        if not result.data:
            return {
                "success": True,
                "limits": {
                    "daily_limit": None,
                    "monthly_limit": None
                }
            }
        
        limits = result.data[0]
        return {
            "success": True,
            "limits": {
                "daily_limit": float(limits["daily_limit"]) if limits["daily_limit"] else None,
                "monthly_limit": float(limits["monthly_limit"]) if limits["monthly_limit"] else None,
                "updated_at": limits["updated_at"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting department limits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/departments/{department_id}/limits")
async def set_department_limits(
    department_id: str,
    request: DepartmentLimitRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Set credit limits for a department (admin only)"""
    try:
        # Check if user is admin
        # TODO: Add proper authorization check
        
        credit_service = CreditService()
        await credit_service.set_department_limits(
            department_id=department_id,
            daily_limit=request.daily_limit,
            monthly_limit=request.monthly_limit
        )
        
        return {
            "success": True,
            "message": "Department limits updated",
            "limits": {
                "daily_limit": request.daily_limit,
                "monthly_limit": request.monthly_limit
            }
        }
    except Exception as e:
        logger.error(f"Error setting department limits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))