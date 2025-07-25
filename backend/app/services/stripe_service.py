import stripe
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from app.core.dependencies import get_supabase_client

logger = logging.getLogger(__name__)

class StripeService:
    def __init__(self):
        self.stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
        self.mock_mode = not bool(self.stripe_api_key)
        
        if not self.stripe_api_key:
            logger.warning("Stripe API key not configured - running in mock mode")
        else:
            stripe.api_key = self.stripe_api_key
        
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.supabase = get_supabase_client().client
    
    async def create_customer(self, organization_id: str, email: str, name: str = None) -> Dict[str, Any]:
        """Create a Stripe customer and link to organization"""
        try:
            # Check if customer already exists
            existing = self.supabase.table("customers").select("*").eq(
                "organization_id", organization_id
            ).execute()
            
            if existing.data:
                return existing.data[0]
            
            # Create Stripe customer (or mock)
            if self.mock_mode:
                stripe_customer = type('obj', (object,), {
                    'id': f'cus_mock_{organization_id[:8]}',
                    'email': email,
                    'name': name
                })()
            else:
                stripe_customer = stripe.Customer.create(
                    email=email,
                    name=name,
                    metadata={
                        "organization_id": organization_id
                    }
                )
            
            # Store in database
            customer_data = {
                "organization_id": organization_id,
                "stripe_customer_id": stripe_customer.id
            }
            
            result = self.supabase.table("customers").insert(customer_data).execute()
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            raise
    
    async def get_or_create_customer(self, organization_id: str, email: str) -> str:
        """Get existing or create new Stripe customer ID"""
        customer = await self.create_customer(organization_id, email)
        return customer["stripe_customer_id"]
    
    async def create_subscription(
        self, 
        organization_id: str, 
        price_id: str,
        payment_method_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a subscription for an organization"""
        try:
            # Get customer
            customer_result = self.supabase.table("customers").select("*").eq(
                "organization_id", organization_id
            ).execute()
            
            if not customer_result.data:
                raise ValueError("Customer not found for organization")
            
            stripe_customer_id = customer_result.data[0]["stripe_customer_id"]
            
            # Attach payment method if provided
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=stripe_customer_id
                )
                
                # Set as default payment method
                stripe.Customer.modify(
                    stripe_customer_id,
                    invoice_settings={
                        "default_payment_method": payment_method_id
                    }
                )
            
            # Create subscription (or mock)
            if self.mock_mode:
                import time
                subscription = type('obj', (object,), {
                    'id': f'sub_mock_{organization_id[:8]}',
                    'status': 'active',
                    'current_period_start': int(time.time()),
                    'current_period_end': int(time.time()) + 30*24*60*60,
                    'latest_invoice': type('obj', (object,), {
                        'payment_intent': None
                    })()
                })()
            else:
                subscription = stripe.Subscription.create(
                    customer=stripe_customer_id,
                    items=[{"price": price_id}],
                    expand=["latest_invoice.payment_intent"]
                )
            
            # Get plan details
            plan_result = self.supabase.table("subscription_plans").select("*").eq(
                "stripe_price_id", price_id
            ).execute()
            
            if not plan_result.data:
                raise ValueError("Plan not found")
            
            plan = plan_result.data[0]
            
            # Store subscription
            subscription_data = {
                "customer_id": customer_result.data[0]["id"],
                "stripe_subscription_id": subscription.id,
                "plan_id": plan["id"],
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(subscription.current_period_start).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription.current_period_end).isoformat()
            }
            
            self.supabase.table("subscriptions").insert(subscription_data).execute()
            
            # Grant included credits
            if plan["included_credits"] > 0:
                from app.services.credit_service import CreditService
                credit_service = CreditService()
                await credit_service.add_credits(
                    organization_id,
                    plan["included_credits"],
                    "subscription_grant",
                    f"Monthly credits from {plan['name']} plan"
                )
            
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "client_secret": subscription.latest_invoice.payment_intent.client_secret if subscription.latest_invoice.payment_intent else None
            }
            
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    async def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> bool:
        """Cancel a subscription"""
        try:
            # Cancel in Stripe
            if at_period_end:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
            else:
                subscription = stripe.Subscription.delete(subscription_id)
            
            # Update database
            self.supabase.table("subscriptions").update({
                "status": subscription.status,
                "cancel_at_period_end": subscription.cancel_at_period_end
            }).eq("stripe_subscription_id", subscription_id).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            return False
    
    async def create_payment_intent(
        self, 
        organization_id: str,
        amount_cents: int,
        currency: str = "usd",
        description: str = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a payment intent for one-time purchase"""
        try:
            stripe_customer_id = await self.get_or_create_customer(
                organization_id, 
                "placeholder@example.com"  # Should get actual email
            )
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                customer=stripe_customer_id,
                description=description,
                metadata=metadata or {}
            )
            
            return {
                "client_secret": payment_intent.client_secret,
                "payment_intent_id": payment_intent.id
            }
            
        except Exception as e:
            logger.error(f"Error creating payment intent: {str(e)}")
            raise
    
    async def purchase_credits(
        self,
        organization_id: str,
        package_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Purchase a credit package"""
        try:
            # Get package details
            package_result = self.supabase.table("credit_packages").select("*").eq(
                "id", package_id
            ).execute()
            
            if not package_result.data:
                raise ValueError("Credit package not found")
            
            package = package_result.data[0]
            
            # Create payment intent
            payment_data = await self.create_payment_intent(
                organization_id,
                package["price_cents"],
                description=f"Purchase of {package['credits']} credits",
                metadata={
                    "type": "credit_purchase",
                    "package_id": package_id,
                    "credits": package["credits"]
                }
            )
            
            # Confirm payment
            stripe.PaymentIntent.confirm(
                payment_data["payment_intent_id"],
                payment_method=payment_method_id
            )
            
            return {
                "success": True,
                "payment_intent_id": payment_data["payment_intent_id"],
                "credits": package["credits"]
            }
            
        except Exception as e:
            logger.error(f"Error purchasing credits: {str(e)}")
            raise
    
    async def handle_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )
            
            logger.info(f"Processing Stripe webhook: {event['type']}")
            
            if event["type"] == "payment_intent.succeeded":
                await self._handle_payment_succeeded(event["data"]["object"])
            
            elif event["type"] == "invoice.payment_succeeded":
                await self._handle_invoice_paid(event["data"]["object"])
            
            elif event["type"] == "customer.subscription.updated":
                await self._handle_subscription_updated(event["data"]["object"])
            
            elif event["type"] == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event["data"]["object"])
            
            return {"success": True, "event_type": event["type"]}
            
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise ValueError("Invalid signature")
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            raise
    
    async def _handle_payment_succeeded(self, payment_intent):
        """Handle successful payment"""
        try:
            metadata = payment_intent.get("metadata", {})
            
            if metadata.get("type") == "credit_purchase":
                # Find organization from customer
                customer_result = self.supabase.table("customers").select("*").eq(
                    "stripe_customer_id", payment_intent["customer"]
                ).execute()
                
                if customer_result.data:
                    organization_id = customer_result.data[0]["organization_id"]
                    credits = float(metadata.get("credits", 0))
                    
                    # Add credits
                    from app.services.credit_service import CreditService
                    credit_service = CreditService()
                    await credit_service.add_credits(
                        organization_id,
                        credits,
                        "purchase",
                        f"Credit purchase",
                        payment_intent["id"]
                    )
                    
                    # Record payment
                    payment_data = {
                        "customer_id": customer_result.data[0]["id"],
                        "stripe_payment_intent_id": payment_intent["id"],
                        "amount_cents": payment_intent["amount"],
                        "currency": payment_intent["currency"],
                        "status": "succeeded",
                        "description": f"Purchase of {credits} credits",
                        "metadata": metadata
                    }
                    self.supabase.table("payments").insert(payment_data).execute()
                    
        except Exception as e:
            logger.error(f"Error handling payment success: {str(e)}")
    
    async def _handle_invoice_paid(self, invoice):
        """Handle paid invoice (subscription renewal)"""
        try:
            subscription_id = invoice["subscription"]
            
            # Get subscription details
            sub_result = self.supabase.table("subscriptions").select(
                "*, subscription_plans(*), customers(*)"
            ).eq("stripe_subscription_id", subscription_id).execute()
            
            if sub_result.data:
                subscription = sub_result.data[0]
                plan = subscription["subscription_plans"]
                customer = subscription["customers"]
                
                # Grant monthly credits
                if plan["included_credits"] > 0:
                    from app.services.credit_service import CreditService
                    credit_service = CreditService()
                    await credit_service.add_credits(
                        customer["organization_id"],
                        plan["included_credits"],
                        "subscription_grant",
                        f"Monthly credits from {plan['name']} plan"
                    )
                
                # Record invoice
                invoice_data = {
                    "customer_id": customer["id"],
                    "stripe_invoice_id": invoice["id"],
                    "invoice_number": invoice["number"],
                    "amount_cents": invoice["amount_paid"],
                    "currency": invoice["currency"],
                    "status": "paid",
                    "paid_at": datetime.fromtimestamp(invoice["status_transitions"]["paid_at"]).isoformat(),
                    "invoice_pdf_url": invoice["invoice_pdf"]
                }
                self.supabase.table("invoices").insert(invoice_data).execute()
                
        except Exception as e:
            logger.error(f"Error handling invoice payment: {str(e)}")
    
    async def _handle_subscription_updated(self, subscription):
        """Handle subscription updates"""
        try:
            self.supabase.table("subscriptions").update({
                "status": subscription["status"],
                "current_period_start": datetime.fromtimestamp(subscription["current_period_start"]).isoformat(),
                "current_period_end": datetime.fromtimestamp(subscription["current_period_end"]).isoformat(),
                "cancel_at_period_end": subscription.get("cancel_at_period_end", False)
            }).eq("stripe_subscription_id", subscription["id"]).execute()
            
        except Exception as e:
            logger.error(f"Error updating subscription: {str(e)}")
    
    async def _handle_subscription_deleted(self, subscription):
        """Handle subscription deletion"""
        try:
            self.supabase.table("subscriptions").update({
                "status": "canceled"
            }).eq("stripe_subscription_id", subscription["id"]).execute()
            
        except Exception as e:
            logger.error(f"Error handling subscription deletion: {str(e)}")
    
    async def get_payment_methods(self, organization_id: str) -> List[Dict[str, Any]]:
        """Get payment methods for an organization"""
        try:
            stripe_customer_id = await self.get_or_create_customer(
                organization_id,
                "placeholder@example.com"
            )
            
            payment_methods = stripe.PaymentMethod.list(
                customer=stripe_customer_id,
                type="card"
            )
            
            return [
                {
                    "id": pm.id,
                    "brand": pm.card.brand,
                    "last4": pm.card.last4,
                    "exp_month": pm.card.exp_month,
                    "exp_year": pm.card.exp_year
                }
                for pm in payment_methods.data
            ]
            
        except Exception as e:
            logger.error(f"Error getting payment methods: {str(e)}")
            return []
    
    async def create_setup_intent(self, organization_id: str) -> Dict[str, Any]:
        """Create setup intent for adding payment method"""
        try:
            stripe_customer_id = await self.get_or_create_customer(
                organization_id,
                "placeholder@example.com"
            )
            
            setup_intent = stripe.SetupIntent.create(
                customer=stripe_customer_id,
                payment_method_types=["card"]
            )
            
            return {
                "client_secret": setup_intent.client_secret,
                "setup_intent_id": setup_intent.id
            }
            
        except Exception as e:
            logger.error(f"Error creating setup intent: {str(e)}")
            raise