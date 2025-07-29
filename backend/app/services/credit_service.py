from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import logging
import os
from supabase import create_client, Client
from app.core.exceptions import InsufficientCreditsError, CreditLimitExceededError

logger = logging.getLogger(__name__)


class CreditService:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError("Supabase credentials not configured")

        self.supabase = create_client(url, key)

    async def get_balance(self, organization_id: str) -> Dict[str, Any]:
        """Get credit balance for an organization"""
        try:
            result = (
                self.supabase.table("credit_balances")
                .select("*")
                .eq("organization_id", organization_id)
                .execute()
            )

            if not result.data:
                # Create initial balance if doesn't exist
                balance_data = {
                    "organization_id": organization_id,
                    "available_credits": 0,
                    "reserved_credits": 0,
                    "total_purchased": 0,
                    "total_consumed": 0,
                }
                result = (
                    self.supabase.table("credit_balances")
                    .insert(balance_data)
                    .execute()
                )

            balance = result.data[0]
            return {
                "available": float(balance["available_credits"]),
                "reserved": float(balance["reserved_credits"]),
                "total_purchased": float(balance["total_purchased"]),
                "total_consumed": float(balance["total_consumed"]),
                "updated_at": balance["updated_at"],
            }

        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}")
            raise

    async def consume_credits(
        self,
        organization_id: str,
        amount: float,
        project_id: Optional[str] = None,
        department_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        action: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> bool:
        """Consume credits for an action"""
        try:
            # Check department limits if applicable
            if department_id:
                await self._check_department_limits(department_id, amount)

            # Call stored procedure to consume credits atomically
            result = self.supabase.rpc(
                "consume_credits",
                {
                    "p_organization_id": organization_id,
                    "p_amount": amount,
                    "p_project_id": project_id,
                    "p_department_id": department_id,
                    "p_agent_type": agent_type,
                    "p_action": action,
                    "p_metadata": metadata or {},
                },
            ).execute()

            if not result.data:
                raise InsufficientCreditsError(
                    f"Insufficient credits. Required: {amount}"
                )

            # Check if balance is low and emit event
            balance = await self.get_balance(organization_id)
            if balance["available"] < 10:
                await self._emit_low_balance_event(
                    organization_id, balance["available"]
                )

            return True

        except Exception as e:
            logger.error(f"Error consuming credits: {str(e)}")
            raise

    async def add_credits(
        self,
        organization_id: str,
        amount: float,
        transaction_type: str,
        description: Optional[str] = None,
        stripe_payment_intent_id: Optional[str] = None,
    ) -> float:
        """Add credits to an organization"""
        try:
            result = self.supabase.rpc(
                "add_credits",
                {
                    "p_organization_id": organization_id,
                    "p_amount": amount,
                    "p_type": transaction_type,
                    "p_description": description,
                    "p_stripe_payment_intent_id": stripe_payment_intent_id,
                },
            ).execute()

            return float(result.data)

        except Exception as e:
            logger.error(f"Error adding credits: {str(e)}")
            raise

    async def get_usage_history(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        project_id: Optional[str] = None,
        department_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get credit usage history"""
        try:
            query = (
                self.supabase.table("credit_usage")
                .select("*")
                .eq("organization_id", organization_id)
            )

            if project_id:
                query = query.eq("project_id", project_id)

            if department_id:
                query = query.eq("department_id", department_id)

            if start_date:
                query = query.gte("created_at", start_date.isoformat())

            if end_date:
                query = query.lte("created_at", end_date.isoformat())

            query = query.order("created_at", desc=True).limit(limit)

            result = query.execute()

            return [
                {
                    "id": usage["id"],
                    "agent_type": usage["agent_type"],
                    "action": usage["action"],
                    "credits": float(usage["credits_consumed"]),
                    "project_id": usage["project_id"],
                    "department_id": usage["department_id"],
                    "metadata": usage["metadata"],
                    "created_at": usage["created_at"],
                    "user_id": usage["user_id"],
                }
                for usage in result.data
            ]

        except Exception as e:
            logger.error(f"Error getting usage history: {str(e)}")
            raise

    async def get_usage_summary(
        self,
        organization_id: str,
        start_date: datetime,
        end_date: datetime,
        group_by: str = "day",  # day, week, month, agent, project, department
    ) -> List[Dict[str, Any]]:
        """Get aggregated usage summary"""
        try:
            # For daily summaries
            if group_by == "day":
                query = """
                    SELECT 
                        DATE(created_at) as date,
                        SUM(credits_consumed) as total_credits,
                        COUNT(*) as action_count
                    FROM credit_usage
                    WHERE organization_id = %s
                        AND created_at >= %s
                        AND created_at <= %s
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """
            elif group_by == "agent":
                query = """
                    SELECT 
                        agent_type,
                        SUM(credits_consumed) as total_credits,
                        COUNT(*) as action_count
                    FROM credit_usage
                    WHERE organization_id = %s
                        AND created_at >= %s
                        AND created_at <= %s
                    GROUP BY agent_type
                    ORDER BY total_credits DESC
                """
            elif group_by == "project":
                query = """
                    SELECT 
                        cu.project_id,
                        p.name as project_name,
                        SUM(cu.credits_consumed) as total_credits,
                        COUNT(*) as action_count
                    FROM credit_usage cu
                    LEFT JOIN projects p ON cu.project_id = p.id
                    WHERE cu.organization_id = %s
                        AND cu.created_at >= %s
                        AND cu.created_at <= %s
                    GROUP BY cu.project_id, p.name
                    ORDER BY total_credits DESC
                """
            elif group_by == "department":
                query = """
                    SELECT 
                        cu.department_id,
                        d.name as department_name,
                        SUM(cu.credits_consumed) as total_credits,
                        COUNT(*) as action_count
                    FROM credit_usage cu
                    LEFT JOIN departments d ON cu.department_id = d.id
                    WHERE cu.organization_id = %s
                        AND cu.created_at >= %s
                        AND cu.created_at <= %s
                    GROUP BY cu.department_id, d.name
                    ORDER BY total_credits DESC
                """
            else:
                raise ValueError(f"Invalid group_by value: {group_by}")

            # Note: Supabase doesn't support raw SQL queries directly
            # We'll use the data from regular queries and aggregate in Python

            usage_data = await self.get_usage_history(
                organization_id, start_date, end_date, limit=10000
            )

            # Aggregate based on group_by
            summary = {}

            for usage in usage_data:
                if group_by == "day":
                    key = usage["created_at"][:10]  # Date only
                elif group_by == "agent":
                    key = usage["agent_type"]
                elif group_by == "project":
                    key = usage["project_id"] or "No Project"
                elif group_by == "department":
                    key = usage["department_id"] or "No Department"

                if key not in summary:
                    summary[key] = {"total_credits": 0, "action_count": 0}

                summary[key]["total_credits"] += usage["credits"]
                summary[key]["action_count"] += 1

            # Convert to list format
            result = []
            for key, data in summary.items():
                item = {"key": key}
                item.update(data)
                result.append(item)

            # Sort by total credits
            result.sort(key=lambda x: x["total_credits"], reverse=True)

            return result

        except Exception as e:
            logger.error(f"Error getting usage summary: {str(e)}")
            raise

    async def get_transaction_history(
        self,
        organization_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get credit transaction history"""
        try:
            query = (
                self.supabase.table("credit_transactions")
                .select("*")
                .eq("organization_id", organization_id)
            )

            if transaction_type:
                query = query.eq("type", transaction_type)

            if start_date:
                query = query.gte("created_at", start_date.isoformat())

            if end_date:
                query = query.lte("created_at", end_date.isoformat())

            query = query.order("created_at", desc=True).limit(limit)

            result = query.execute()

            return [
                {
                    "id": tx["id"],
                    "type": tx["type"],
                    "amount": float(tx["amount"]),
                    "balance_after": float(tx["balance_after"]),
                    "description": tx["description"],
                    "metadata": tx["metadata"],
                    "stripe_payment_intent_id": tx["stripe_payment_intent_id"],
                    "created_at": tx["created_at"],
                    "created_by": tx["created_by"],
                }
                for tx in result.data
            ]

        except Exception as e:
            logger.error(f"Error getting transaction history: {str(e)}")
            raise

    async def get_agent_action_costs(self) -> List[Dict[str, Any]]:
        """Get configured costs for agent actions"""
        try:
            result = (
                self.supabase.table("agent_action_costs")
                .select("*")
                .eq("is_active", True)
                .execute()
            )

            return [
                {
                    "agent_type": cost["agent_type"],
                    "action": cost["action"],
                    "credit_cost": float(cost["credit_cost"]),
                    "description": cost["description"],
                }
                for cost in result.data
            ]

        except Exception as e:
            logger.error(f"Error getting agent action costs: {str(e)}")
            raise

    async def get_cost_for_action(self, agent_type: str, action: str) -> float:
        """Get credit cost for a specific agent action"""
        try:
            result = (
                self.supabase.table("agent_action_costs")
                .select("credit_cost")
                .eq("agent_type", agent_type)
                .eq("action", action)
                .eq("is_active", True)
                .execute()
            )

            if result.data:
                return float(result.data[0]["credit_cost"])

            # Default cost if not configured
            logger.warning(
                f"No cost configured for {agent_type}.{action}, using default"
            )
            return 1.0

        except Exception as e:
            logger.error(f"Error getting action cost: {str(e)}")
            return 1.0

    async def _check_department_limits(self, department_id: str, amount: float):
        """Check if department credit limits would be exceeded"""
        try:
            # Get department limits
            limits_result = (
                self.supabase.table("department_credit_limits")
                .select("*")
                .eq("department_id", department_id)
                .execute()
            )

            if not limits_result.data:
                return  # No limits set

            limits = limits_result.data[0]

            # Check daily limit
            if limits.get("daily_limit"):
                today_start = datetime.utcnow().replace(
                    hour=0, minute=0, second=0, microsecond=0
                )

                usage_result = (
                    self.supabase.table("credit_usage")
                    .select("credits_consumed")
                    .eq("department_id", department_id)
                    .gte("created_at", today_start.isoformat())
                    .execute()
                )

                today_usage = sum(
                    float(u["credits_consumed"]) for u in usage_result.data
                )

                if today_usage + amount > float(limits["daily_limit"]):
                    raise CreditLimitExceededError(
                        f"Daily limit of {limits['daily_limit']} credits would be exceeded"
                    )

            # Check monthly limit
            if limits.get("monthly_limit"):
                month_start = datetime.utcnow().replace(
                    day=1, hour=0, minute=0, second=0, microsecond=0
                )

                usage_result = (
                    self.supabase.table("credit_usage")
                    .select("credits_consumed")
                    .eq("department_id", department_id)
                    .gte("created_at", month_start.isoformat())
                    .execute()
                )

                month_usage = sum(
                    float(u["credits_consumed"]) for u in usage_result.data
                )

                if month_usage + amount > float(limits["monthly_limit"]):
                    raise CreditLimitExceededError(
                        f"Monthly limit of {limits['monthly_limit']} credits would be exceeded"
                    )

        except CreditLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Error checking department limits: {str(e)}")
            # Don't block on error checking limits

    async def set_department_limits(
        self,
        department_id: str,
        daily_limit: Optional[float] = None,
        monthly_limit: Optional[float] = None,
    ):
        """Set credit limits for a department"""
        try:
            # Check if limits exist
            existing = (
                self.supabase.table("department_credit_limits")
                .select("id")
                .eq("department_id", department_id)
                .execute()
            )

            limit_data = {
                "department_id": department_id,
                "daily_limit": daily_limit,
                "monthly_limit": monthly_limit,
            }

            if existing.data:
                # Update existing
                self.supabase.table("department_credit_limits").update(limit_data).eq(
                    "department_id", department_id
                ).execute()
            else:
                # Insert new
                self.supabase.table("department_credit_limits").insert(
                    limit_data
                ).execute()

        except Exception as e:
            logger.error(f"Error setting department limits: {str(e)}")
            raise

    async def _emit_low_balance_event(self, organization_id: str, balance: float):
        """Emit event when balance is low"""
        try:
            # This could integrate with your event system or notification service
            logger.warning(
                f"Low credit balance for organization {organization_id}: {balance} credits remaining"
            )

            # TODO: Integrate with FeedbackLoopAgent or notification system

        except Exception as e:
            logger.error(f"Error emitting low balance event: {str(e)}")

    async def reserve_credits(
        self, organization_id: str, amount: float, reservation_id: str
    ) -> bool:
        """Reserve credits for future use (e.g., long-running tasks)"""
        try:
            # Get current balance
            balance = await self.get_balance(organization_id)

            if balance["available"] < amount:
                return False

            # Move credits from available to reserved
            new_available = balance["available"] - amount
            new_reserved = balance["reserved"] + amount

            self.supabase.table("credit_balances").update(
                {"available_credits": new_available, "reserved_credits": new_reserved}
            ).eq("organization_id", organization_id).execute()

            # Store reservation details in metadata
            await self.add_credits(
                organization_id,
                0,  # No actual credit change, just tracking
                "adjustment",
                f"Reserved {amount} credits for {reservation_id}",
            )

            return True

        except Exception as e:
            logger.error(f"Error reserving credits: {str(e)}")
            return False

    async def release_reserved_credits(
        self,
        organization_id: str,
        amount: float,
        reservation_id: str,
        consume: bool = False,
    ):
        """Release or consume reserved credits"""
        try:
            # Get current balance
            balance = await self.get_balance(organization_id)

            if consume:
                # Consume from reserved
                new_reserved = max(0, balance["reserved"] - amount)
                new_consumed = balance["total_consumed"] + amount

                self.supabase.table("credit_balances").update(
                    {"reserved_credits": new_reserved, "total_consumed": new_consumed}
                ).eq("organization_id", organization_id).execute()

                # Record consumption
                await self.add_credits(
                    organization_id,
                    0,
                    "consumption",
                    f"Consumed {amount} reserved credits for {reservation_id}",
                )
            else:
                # Return to available
                new_reserved = max(0, balance["reserved"] - amount)
                new_available = balance["available"] + amount

                self.supabase.table("credit_balances").update(
                    {
                        "available_credits": new_available,
                        "reserved_credits": new_reserved,
                    }
                ).eq("organization_id", organization_id).execute()

                # Record release
                await self.add_credits(
                    organization_id,
                    0,
                    "adjustment",
                    f"Released {amount} reserved credits for {reservation_id}",
                )

        except Exception as e:
            logger.error(f"Error releasing reserved credits: {str(e)}")
