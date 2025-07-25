from fastapi import APIRouter, Depends, HTTPException, Request, Header
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import logging
import stripe

from app.core.supabase_auth import get_current_user as get_current_user_supabase
from app.services.stripe_service import StripeService
from supabase import create_client, Client
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/billing", tags=["billing"])


def get_supabase() -> Client:
    """Get the actual Supabase client."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        raise ValueError("Supabase credentials not configured")
    
    return create_client(url, key)

# Request/Response models
class CreateSubscriptionRequest(BaseModel):
    plan_id: str
    payment_method_id: Optional[str] = None

class UpdateSubscriptionRequest(BaseModel):
    plan_id: str

class PurchaseCreditsRequest(BaseModel):
    package_id: str
    payment_method_id: str

class SetupPaymentMethodRequest(BaseModel):
    return_url: str

class CreateCustomerRequest(BaseModel):
    email: str
    name: Optional[str] = None

# Endpoints
@router.get("/customer")
async def get_customer_info(
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get customer billing information"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        supabase = get_supabase()
        
        # Get customer info
        customer_result = supabase.table("customers").select("*").eq(
            "organization_id", org_id
        ).execute()
        
        if not customer_result.data:
            return {
                "success": True,
                "customer": None,
                "message": "No customer record found"
            }
        
        customer = customer_result.data[0]
        
        # Get Stripe customer details
        stripe_service = StripeService()
        stripe_customer = stripe.Customer.retrieve(customer["stripe_customer_id"])
        
        return {
            "success": True,
            "customer": {
                "id": customer["id"],
                "stripe_customer_id": customer["stripe_customer_id"],
                "email": stripe_customer.email,
                "name": stripe_customer.name,
                "default_payment_method": customer.get("default_payment_method_id"),
                "created_at": customer["created_at"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting customer info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/customer")
async def create_customer(
    request: CreateCustomerRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Create customer record for organization"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        stripe_service = StripeService()
        customer = await stripe_service.create_customer(
            organization_id=org_id,
            email=request.email,
            name=request.name
        )
        
        return {
            "success": True,
            "customer": customer
        }
    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/plans")
async def list_subscription_plans():
    """List available subscription plans"""
    try:
        supabase = get_supabase()
        
        result = supabase.table("subscription_plans").select("*").eq(
            "is_active", True
        ).order("price_cents").execute()
        
        plans = []
        for plan in result.data:
            plans.append({
                "id": plan["id"],
                "name": plan["name"],
                "description": plan["description"],
                "price": plan["price_cents"] / 100,  # Convert cents to dollars
                "currency": plan["currency"],
                "interval": plan["interval"],
                "included_credits": plan["included_credits"],
                "features": plan["features"],
                "stripe_price_id": plan["stripe_price_id"]
            })
        
        return {
            "success": True,
            "plans": plans
        }
    except Exception as e:
        logger.error(f"Error listing plans: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/subscription")
async def get_subscription(
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Get current subscription details"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        supabase = get_supabase()
        
        # Get customer
        customer_result = supabase.table("customers").select("id").eq(
            "organization_id", org_id
        ).execute()
        
        if not customer_result.data:
            return {
                "success": True,
                "subscription": None
            }
        
        # Get active subscription
        sub_result = supabase.table("subscriptions").select(
            "*, subscription_plans(*)"
        ).eq(
            "customer_id", customer_result.data[0]["id"]
        ).eq("status", "active").execute()
        
        if not sub_result.data:
            return {
                "success": True,
                "subscription": None
            }
        
        subscription = sub_result.data[0]
        plan = subscription["subscription_plans"]
        
        return {
            "success": True,
            "subscription": {
                "id": subscription["id"],
                "status": subscription["status"],
                "plan": {
                    "id": plan["id"],
                    "name": plan["name"],
                    "price": plan["price_cents"] / 100,
                    "interval": plan["interval"],
                    "included_credits": plan["included_credits"]
                },
                "current_period_start": subscription["current_period_start"],
                "current_period_end": subscription["current_period_end"],
                "cancel_at_period_end": subscription["cancel_at_period_end"]
            }
        }
    except Exception as e:
        logger.error(f"Error getting subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Create a new subscription"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        # Get plan details
        supabase = get_supabase()
        plan_result = supabase.table("subscription_plans").select("*").eq(
            "id", request.plan_id
        ).execute()
        
        if not plan_result.data:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        plan = plan_result.data[0]
        
        stripe_service = StripeService()
        result = await stripe_service.create_subscription(
            organization_id=org_id,
            price_id=plan["stripe_price_id"],
            payment_method_id=request.payment_method_id
        )
        
        return {
            "success": True,
            "subscription": result
        }
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/subscription")
async def update_subscription(
    request: UpdateSubscriptionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Update subscription plan"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        # Implementation would update existing subscription
        # This is a placeholder
        raise HTTPException(status_code=501, detail="Not implemented yet")
        
    except Exception as e:
        logger.error(f"Error updating subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/subscription")
async def cancel_subscription(
    at_period_end: bool = True,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Cancel subscription"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        supabase = get_supabase()
        
        # Get active subscription
        sub_result = supabase.table("subscriptions").select(
            "stripe_subscription_id"
        ).eq("status", "active").execute()
        
        if not sub_result.data:
            raise HTTPException(status_code=404, detail="No active subscription found")
        
        stripe_service = StripeService()
        success = await stripe_service.cancel_subscription(
            sub_result.data[0]["stripe_subscription_id"],
            at_period_end=at_period_end
        )
        
        return {
            "success": success,
            "cancel_at_period_end": at_period_end
        }
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/credit-packages")
async def list_credit_packages():
    """List available credit packages for purchase"""
    try:
        supabase = get_supabase()
        
        result = supabase.table("credit_packages").select("*").eq(
            "is_active", True
        ).order("credits").execute()
        
        packages = []
        for package in result.data:
            packages.append({
                "id": package["id"],
                "name": package["name"],
                "description": package["description"],
                "credits": package["credits"],
                "price": package["price_cents"] / 100,
                "currency": package["currency"],
                "stripe_price_id": package["stripe_price_id"]
            })
        
        return {
            "success": True,
            "packages": packages
        }
    except Exception as e:
        logger.error(f"Error listing credit packages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/purchase-credits")
async def purchase_credits(
    request: PurchaseCreditsRequest,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Purchase a credit package"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        stripe_service = StripeService()
        result = await stripe_service.purchase_credits(
            organization_id=org_id,
            package_id=request.package_id,
            payment_method_id=request.payment_method_id
        )
        
        return {
            "success": True,
            "purchase": result
        }
    except Exception as e:
        logger.error(f"Error purchasing credits: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payment-methods")
async def list_payment_methods(
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """List saved payment methods"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        stripe_service = StripeService()
        methods = await stripe_service.get_payment_methods(org_id)
        
        return {
            "success": True,
            "payment_methods": methods
        }
    except Exception as e:
        logger.error(f"Error listing payment methods: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/setup-intent")
async def create_setup_intent(
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """Create setup intent for adding payment method"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        stripe_service = StripeService()
        result = await stripe_service.create_setup_intent(org_id)
        
        return {
            "success": True,
            "setup_intent": result
        }
    except Exception as e:
        logger.error(f"Error creating setup intent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/invoices")
async def list_invoices(
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """List billing invoices"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        supabase = get_supabase()
        
        # Get customer
        customer_result = supabase.table("customers").select("id").eq(
            "organization_id", org_id
        ).execute()
        
        if not customer_result.data:
            return {
                "success": True,
                "invoices": []
            }
        
        # Get invoices
        invoice_result = supabase.table("invoices").select("*").eq(
            "customer_id", customer_result.data[0]["id"]
        ).order("created_at", desc=True).limit(limit).execute()
        
        invoices = []
        for invoice in invoice_result.data:
            invoices.append({
                "id": invoice["id"],
                "invoice_number": invoice["invoice_number"],
                "amount": invoice["amount_cents"] / 100,
                "currency": invoice["currency"],
                "status": invoice["status"],
                "due_date": invoice["due_date"],
                "paid_at": invoice["paid_at"],
                "pdf_url": invoice["invoice_pdf_url"],
                "created_at": invoice["created_at"]
            })
        
        return {
            "success": True,
            "invoices": invoices
        }
    except Exception as e:
        logger.error(f"Error listing invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payments")
async def list_payments(
    limit: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_user_supabase)
):
    """List payment history"""
    try:
        org_id = current_user.get("organization_id")
        if not org_id:
            raise HTTPException(status_code=400, detail="No organization found")
        
        supabase = get_supabase()
        
        # Get customer
        customer_result = supabase.table("customers").select("id").eq(
            "organization_id", org_id
        ).execute()
        
        if not customer_result.data:
            return {
                "success": True,
                "payments": []
            }
        
        # Get payments
        payment_result = supabase.table("payments").select("*").eq(
            "customer_id", customer_result.data[0]["id"]
        ).order("created_at", desc=True).limit(limit).execute()
        
        payments = []
        for payment in payment_result.data:
            payments.append({
                "id": payment["id"],
                "amount": payment["amount_cents"] / 100,
                "currency": payment["currency"],
                "status": payment["status"],
                "description": payment["description"],
                "created_at": payment["created_at"]
            })
        
        return {
            "success": True,
            "payments": payments
        }
    except Exception as e:
        logger.error(f"Error listing payments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Stripe webhook endpoint
@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None, alias="Stripe-Signature")
):
    """Handle Stripe webhook events"""
    try:
        payload = await request.body()
        
        stripe_service = StripeService()
        result = await stripe_service.handle_webhook(payload, stripe_signature)
        
        return result
        
    except ValueError as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))