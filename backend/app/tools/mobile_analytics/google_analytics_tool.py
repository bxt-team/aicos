import logging
from typing import Dict, Any, Optional, List
from crewai.tools import BaseTool
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class GoogleAnalyticsTool(BaseTool):
    name: str = "Google Analytics 4 Tool"
    description: str = """Analyze Google Analytics 4 mobile app data including user behavior, 
    conversion funnels, retention metrics, and revenue analytics. Provides insights for 
    app optimization and user experience improvements."""
    
    def _run(self, input_data: str) -> Dict[str, Any]:
        """
        Analyze Google Analytics 4 data.
        
        Args:
            input_data: Property ID or analytics data JSON
            
        Returns:
            Dict containing analytics insights
        """
        try:
            # Parse input
            if input_data.startswith("{"):
                analytics_data = json.loads(input_data)
            else:
                # Assume it's a property ID
                analytics_data = self._fetch_analytics_data(input_data)
            
            logger.info(f"Analyzing GA4 data for property: {analytics_data.get('property_id', 'Unknown')}")
            
            # Analyze user metrics
            user_analysis = self._analyze_user_metrics(analytics_data)
            
            # Analyze user behavior
            behavior = self._analyze_behavior(analytics_data)
            
            # Analyze conversions
            conversions = self._analyze_conversions(analytics_data)
            
            # Analyze retention
            retention = self._analyze_retention(analytics_data)
            
            # Generate insights
            insights = self._generate_insights(user_analysis, behavior, conversions, retention)
            
            return {
                "success": True,
                "analytics_data": analytics_data,
                "user_analysis": user_analysis,
                "behavior_analysis": behavior,
                "conversion_analysis": conversions,
                "retention_analysis": retention,
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Google Analytics data: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_data": self._get_fallback_data()
            }
    
    def _fetch_analytics_data(self, property_id: str) -> Dict[str, Any]:
        """Fetch GA4 data (simulated)."""
        
        # In production, this would use the Google Analytics Data API
        # For now, return simulated data
        
        return {
            "property_id": property_id,
            "app_name": "Mobile App",
            "date_range": {
                "start": (datetime.now() - timedelta(days=30)).isoformat(),
                "end": datetime.now().isoformat()
            },
            "users": self._get_sample_user_data(),
            "events": self._get_sample_events(),
            "conversions": self._get_sample_conversions(),
            "screens": self._get_sample_screens()
        }
    
    def _analyze_user_metrics(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user metrics and engagement."""
        
        users_data = analytics_data.get("users", {})
        
        total_users = users_data.get("total", 100000)
        new_users = users_data.get("new", 30000)
        returning_users = total_users - new_users
        
        # Calculate engagement metrics
        sessions = users_data.get("sessions", 320000)
        avg_session_duration = users_data.get("avg_session_duration", 180)
        screens_per_session = users_data.get("screens_per_session", 4.2)
        
        engagement_rate = self._calculate_engagement_rate(
            sessions, avg_session_duration, screens_per_session
        )
        
        return {
            "overview": {
                "total_users": total_users,
                "new_users": new_users,
                "returning_users": returning_users,
                "new_user_percentage": round(new_users / total_users * 100, 1)
            },
            "engagement": {
                "total_sessions": sessions,
                "sessions_per_user": round(sessions / total_users, 2),
                "avg_session_duration": avg_session_duration,
                "screens_per_session": screens_per_session,
                "engagement_rate": engagement_rate,
                "bounce_rate": users_data.get("bounce_rate", 25.5)
            },
            "active_users": {
                "daily": users_data.get("dau", 20000),
                "weekly": users_data.get("wau", 50000),
                "monthly": users_data.get("mau", 80000)
            },
            "user_quality_score": self._calculate_user_quality_score(users_data)
        }
    
    def _analyze_behavior(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user behavior patterns."""
        
        screens_data = analytics_data.get("screens", [])
        events_data = analytics_data.get("events", [])
        
        # Analyze screen performance
        screen_analysis = []
        for screen in screens_data:
            screen_analysis.append({
                "screen_name": screen["name"],
                "views": screen["views"],
                "unique_users": screen["unique_users"],
                "avg_time_on_screen": screen["avg_time"],
                "exit_rate": screen["exit_rate"],
                "performance_score": self._calculate_screen_score(screen)
            })
        
        # Sort by views
        screen_analysis.sort(key=lambda x: x["views"], reverse=True)
        
        # Analyze user flow
        user_flows = self._analyze_user_flows(screens_data, events_data)
        
        # Analyze events
        event_analysis = self._analyze_events(events_data)
        
        return {
            "top_screens": screen_analysis[:10],
            "screen_insights": self._generate_screen_insights(screen_analysis),
            "user_flows": user_flows,
            "event_analysis": event_analysis,
            "interaction_patterns": self._identify_interaction_patterns(events_data)
        }
    
    def _analyze_conversions(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze conversion funnels and goals."""
        
        conversions_data = analytics_data.get("conversions", {})
        
        # Analyze goals
        goals = conversions_data.get("goals", [])
        goal_analysis = []
        
        for goal in goals:
            completions = goal.get("completions", 0)
            sessions = goal.get("sessions", 1)
            conversion_rate = (completions / sessions * 100) if sessions > 0 else 0
            
            goal_analysis.append({
                "goal_name": goal["name"],
                "completions": completions,
                "conversion_rate": round(conversion_rate, 2),
                "value": goal.get("value", 0),
                "avg_value": goal.get("value", 0) / completions if completions > 0 else 0
            })
        
        # Analyze funnels
        funnels = conversions_data.get("funnels", {})
        funnel_analysis = self._analyze_funnels(funnels)
        
        # Revenue analysis
        revenue = conversions_data.get("revenue", {})
        revenue_analysis = self._analyze_revenue(revenue)
        
        return {
            "goals": goal_analysis,
            "goal_insights": self._generate_goal_insights(goal_analysis),
            "funnels": funnel_analysis,
            "funnel_optimization": self._identify_funnel_optimizations(funnel_analysis),
            "revenue": revenue_analysis,
            "conversion_score": self._calculate_conversion_score(goal_analysis, funnel_analysis)
        }
    
    def _analyze_retention(self, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user retention and churn."""
        
        users_data = analytics_data.get("users", {})
        
        # Get retention data
        retention_data = users_data.get("retention", {})
        
        retention_curve = {
            "day_1": retention_data.get("day_1", 60.0),
            "day_3": retention_data.get("day_3", 45.0),
            "day_7": retention_data.get("day_7", 30.0),
            "day_14": retention_data.get("day_14", 20.0),
            "day_30": retention_data.get("day_30", 15.0),
            "day_60": retention_data.get("day_60", 10.0),
            "day_90": retention_data.get("day_90", 8.0)
        }
        
        # Analyze cohorts
        cohorts = users_data.get("cohorts", [])
        cohort_analysis = self._analyze_cohorts(cohorts)
        
        # Identify churn factors
        churn_analysis = self._analyze_churn_factors(analytics_data)
        
        # Calculate retention score
        retention_score = self._calculate_retention_score(retention_curve)
        
        return {
            "retention_curve": retention_curve,
            "retention_insights": self._generate_retention_insights(retention_curve),
            "cohort_analysis": cohort_analysis,
            "churn_analysis": churn_analysis,
            "retention_score": retention_score,
            "ltv_estimate": self._estimate_ltv(retention_curve, analytics_data)
        }
    
    def _generate_insights(self, user_analysis: Dict, behavior: Dict, 
                          conversions: Dict, retention: Dict) -> Dict[str, Any]:
        """Generate actionable insights from all analyses."""
        
        insights = {
            "key_findings": [],
            "opportunities": [],
            "risks": [],
            "recommendations": []
        }
        
        # User insights
        engagement_rate = user_analysis["engagement"]["engagement_rate"]
        if engagement_rate < 60:
            insights["key_findings"].append(
                f"Engagement rate ({engagement_rate}%) is below target. "
                "Focus on improving user experience."
            )
            insights["recommendations"].append({
                "area": "Engagement",
                "action": "Analyze top exit screens and improve UX",
                "priority": "high",
                "expected_impact": "15-20% improvement in engagement"
            })
        
        # Behavior insights
        top_screens = behavior["top_screens"]
        if top_screens:
            high_exit_screens = [s for s in top_screens if s["exit_rate"] > 40]
            if high_exit_screens:
                insights["risks"].append(
                    f"{len(high_exit_screens)} screens have high exit rates (>40%)"
                )
        
        # Conversion insights
        funnel_data = conversions.get("funnels", {})
        if funnel_data:
            for funnel_name, funnel in funnel_data.items():
                if funnel.get("overall_conversion", 100) < 20:
                    insights["opportunities"].append(
                        f"Optimize {funnel_name} funnel - current conversion only "
                        f"{funnel.get('overall_conversion', 0)}%"
                    )
        
        # Retention insights
        day_7_retention = retention["retention_curve"]["day_7"]
        if day_7_retention < 25:
            insights["key_findings"].append(
                f"Day 7 retention ({day_7_retention}%) needs improvement"
            )
            insights["recommendations"].append({
                "area": "Retention",
                "action": "Implement day 3 and day 5 re-engagement campaigns",
                "priority": "critical",
                "expected_impact": "10-15% improvement in day 7 retention"
            })
        
        return insights
    
    def _calculate_engagement_rate(self, sessions: int, duration: float, screens: float) -> float:
        """Calculate engagement rate based on multiple factors."""
        
        # Simple engagement score calculation
        duration_score = min(duration / 180, 1.0) * 30  # Target 3 minutes
        screens_score = min(screens / 4, 1.0) * 30  # Target 4 screens
        frequency_score = 40  # Placeholder for session frequency
        
        return round(duration_score + screens_score + frequency_score, 1)
    
    def _calculate_user_quality_score(self, users_data: Dict) -> float:
        """Calculate overall user quality score."""
        
        factors = {
            "retention": users_data.get("day_7_retention", 30) / 30,  # Target 30%
            "engagement": users_data.get("engagement_rate", 60) / 60,  # Target 60%
            "revenue": users_data.get("paying_user_percentage", 5) / 5  # Target 5%
        }
        
        weights = {"retention": 0.4, "engagement": 0.3, "revenue": 0.3}
        
        score = sum(factors[k] * weights[k] for k in factors) * 100
        return min(round(score, 1), 100)
    
    def _calculate_screen_score(self, screen: Dict) -> float:
        """Calculate screen performance score."""
        
        # Lower exit rate is better
        exit_score = max(0, 100 - screen["exit_rate"])
        
        # Higher time on screen (up to a point)
        time_score = min(screen["avg_time"] / 60, 1.0) * 100  # Target 60 seconds
        
        # Engagement based on views
        view_score = min(screen["views"] / 10000, 1.0) * 100
        
        return round((exit_score * 0.4 + time_score * 0.3 + view_score * 0.3), 1)
    
    def _analyze_user_flows(self, screens: List, events: List) -> Dict[str, Any]:
        """Analyze common user flows through the app."""
        
        # Simulated flow analysis
        common_flows = [
            {
                "flow": "Launch -> Home -> Browse -> Product -> Purchase",
                "users": 15000,
                "completion_rate": 35.5,
                "avg_time": 240
            },
            {
                "flow": "Launch -> Home -> Search -> Results -> Product",
                "users": 12000,
                "completion_rate": 42.0,
                "avg_time": 180
            }
        ]
        
        drop_off_points = [
            {
                "from_screen": "RegistrationScreen",
                "to_screen": "Exit",
                "users_lost": 5500,
                "drop_off_rate": 45.0
            },
            {
                "from_screen": "CheckoutScreen",
                "to_screen": "Exit",
                "users_lost": 3200,
                "drop_off_rate": 32.0
            }
        ]
        
        return {
            "common_flows": common_flows,
            "drop_off_points": drop_off_points,
            "flow_insights": [
                "Search flow has higher completion rate than browse flow",
                "Registration is the biggest drop-off point"
            ]
        }
    
    def _analyze_events(self, events_data: List) -> Dict[str, Any]:
        """Analyze event data."""
        
        event_summary = {}
        for event in events_data:
            event_summary[event["name"]] = {
                "count": event["count"],
                "unique_users": event.get("unique_users", 0),
                "avg_per_user": event["count"] / event.get("unique_users", 1) if event.get("unique_users", 0) > 0 else 0
            }
        
        return {
            "top_events": sorted(events_data, key=lambda x: x["count"], reverse=True)[:10],
            "event_summary": event_summary,
            "custom_events": [e for e in events_data if e.get("is_custom", False)]
        }
    
    def _identify_interaction_patterns(self, events: List) -> List[str]:
        """Identify user interaction patterns."""
        
        patterns = []
        
        # Look for specific event patterns
        search_events = sum(1 for e in events if "search" in e["name"].lower())
        if search_events > 0:
            patterns.append("Users actively use search functionality")
        
        share_events = sum(1 for e in events if "share" in e["name"].lower())
        if share_events > 0:
            patterns.append("Social sharing is a key user behavior")
        
        return patterns
    
    def _analyze_funnels(self, funnels_data: Dict) -> Dict[str, Any]:
        """Analyze conversion funnels."""
        
        funnel_analysis = {}
        
        for funnel_name, funnel in funnels_data.items():
            steps = funnel.get("steps", [])
            
            if steps:
                overall_conversion = (steps[-1]["users"] / steps[0]["users"] * 100) if steps[0]["users"] > 0 else 0
                
                funnel_analysis[funnel_name] = {
                    "steps": steps,
                    "overall_conversion": round(overall_conversion, 2),
                    "biggest_drop": self._find_biggest_drop(steps)
                }
        
        return funnel_analysis
    
    def _find_biggest_drop(self, steps: List[Dict]) -> Dict[str, Any]:
        """Find the step with the biggest drop-off."""
        
        biggest_drop = {"from": "", "to": "", "drop_rate": 0}
        
        for i in range(1, len(steps)):
            if steps[i-1]["users"] > 0:
                drop_rate = ((steps[i-1]["users"] - steps[i]["users"]) / steps[i-1]["users"] * 100)
                if drop_rate > biggest_drop["drop_rate"]:
                    biggest_drop = {
                        "from": steps[i-1]["name"],
                        "to": steps[i]["name"],
                        "drop_rate": round(drop_rate, 2)
                    }
        
        return biggest_drop
    
    def _analyze_revenue(self, revenue_data: Dict) -> Dict[str, Any]:
        """Analyze revenue metrics."""
        
        total_revenue = revenue_data.get("total", 500000)
        transactions = revenue_data.get("transactions", 15000)
        paying_users = revenue_data.get("paying_users", 12000)
        total_users = revenue_data.get("total_users", 100000)
        
        return {
            "total_revenue": total_revenue,
            "transactions": transactions,
            "paying_users": paying_users,
            "conversion_to_paying": round(paying_users / total_users * 100, 2),
            "arpu": round(total_revenue / total_users, 2),
            "arppu": round(total_revenue / paying_users, 2) if paying_users > 0 else 0,
            "avg_transaction_value": round(total_revenue / transactions, 2) if transactions > 0 else 0,
            "revenue_trends": revenue_data.get("trends", {})
        }
    
    def _identify_funnel_optimizations(self, funnel_analysis: Dict) -> List[Dict]:
        """Identify funnel optimization opportunities."""
        
        optimizations = []
        
        for funnel_name, data in funnel_analysis.items():
            if data["overall_conversion"] < 30:
                optimizations.append({
                    "funnel": funnel_name,
                    "issue": f"Low overall conversion ({data['overall_conversion']}%)",
                    "recommendation": f"Focus on improving {data['biggest_drop']['from']} to {data['biggest_drop']['to']} transition",
                    "priority": "high" if data["overall_conversion"] < 20 else "medium"
                })
        
        return optimizations
    
    def _generate_goal_insights(self, goals: List[Dict]) -> List[str]:
        """Generate insights from goal data."""
        
        insights = []
        
        if goals:
            # Find best and worst performing goals
            goals_sorted = sorted(goals, key=lambda x: x["conversion_rate"], reverse=True)
            
            if len(goals_sorted) >= 2:
                best = goals_sorted[0]
                worst = goals_sorted[-1]
                
                insights.append(
                    f"'{best['goal_name']}' has the highest conversion rate ({best['conversion_rate']}%)"
                )
                
                if worst["conversion_rate"] < 5:
                    insights.append(
                        f"'{worst['goal_name']}' needs improvement (only {worst['conversion_rate']}% conversion)"
                    )
        
        return insights
    
    def _calculate_conversion_score(self, goals: List, funnels: Dict) -> float:
        """Calculate overall conversion score."""
        
        # Average goal conversion rate
        if goals:
            avg_goal_conversion = sum(g["conversion_rate"] for g in goals) / len(goals)
        else:
            avg_goal_conversion = 0
        
        # Average funnel conversion
        if funnels:
            funnel_conversions = [f["overall_conversion"] for f in funnels.values()]
            avg_funnel_conversion = sum(funnel_conversions) / len(funnel_conversions)
        else:
            avg_funnel_conversion = 0
        
        # Combined score (normalized to 100)
        score = (avg_goal_conversion * 0.5 + avg_funnel_conversion * 0.5) * 2
        return min(round(score, 1), 100)
    
    def _analyze_cohorts(self, cohorts: List[Dict]) -> Dict[str, Any]:
        """Analyze cohort data."""
        
        if not cohorts:
            return {"message": "No cohort data available"}
        
        # Sort by retention
        cohorts_sorted = sorted(cohorts, key=lambda x: x.get("day_30_retention", 0), reverse=True)
        
        return {
            "best_cohort": cohorts_sorted[0] if cohorts_sorted else None,
            "worst_cohort": cohorts_sorted[-1] if len(cohorts_sorted) > 1 else None,
            "cohort_insights": self._generate_cohort_insights(cohorts_sorted)
        }
    
    def _generate_cohort_insights(self, cohorts: List[Dict]) -> List[str]:
        """Generate insights from cohort analysis."""
        
        insights = []
        
        if len(cohorts) >= 2:
            best = cohorts[0]
            worst = cohorts[-1]
            
            retention_diff = best["day_30_retention"] - worst["day_30_retention"]
            if retention_diff > 10:
                insights.append(
                    f"Significant retention difference ({retention_diff}%) between best and worst cohorts"
                )
        
        return insights
    
    def _analyze_churn_factors(self, analytics_data: Dict) -> Dict[str, Any]:
        """Analyze factors contributing to churn."""
        
        # Simulated churn analysis
        churn_indicators = [
            {
                "factor": "Low first week engagement",
                "description": "Less than 3 sessions in first 7 days",
                "impact": "High",
                "affected_users_percentage": 35
            },
            {
                "factor": "No key action completion",
                "description": "Didn't complete onboarding or first purchase",
                "impact": "High",
                "affected_users_percentage": 42
            },
            {
                "factor": "Technical issues",
                "description": "Experienced crashes or errors",
                "impact": "Medium",
                "affected_users_percentage": 15
            }
        ]
        
        return {
            "churn_indicators": churn_indicators,
            "churn_prediction_accuracy": 78.5,
            "recommendations": [
                "Improve onboarding completion rate",
                "Implement engagement campaigns for low-activity users",
                "Fix technical issues affecting user experience"
            ]
        }
    
    def _generate_retention_insights(self, retention_curve: Dict) -> List[str]:
        """Generate insights from retention data."""
        
        insights = []
        
        # Day 1 retention
        if retention_curve["day_1"] < 50:
            insights.append("Critical: Day 1 retention below 50% indicates onboarding issues")
        
        # Day 7 retention
        if retention_curve["day_7"] < 20:
            insights.append("Day 7 retention needs immediate attention")
        
        # Long-term retention
        if retention_curve["day_30"] < 10:
            insights.append("Long-term retention is concerning - focus on value delivery")
        
        return insights
    
    def _calculate_retention_score(self, retention_curve: Dict) -> float:
        """Calculate retention score based on industry benchmarks."""
        
        # Weight different retention periods
        weights = {
            "day_1": 0.3,
            "day_7": 0.3,
            "day_30": 0.4
        }
        
        # Industry benchmarks (adjust based on app category)
        benchmarks = {
            "day_1": 50,
            "day_7": 20,
            "day_30": 10
        }
        
        score = 0
        for period, weight in weights.items():
            if period in retention_curve:
                actual = retention_curve[period]
                benchmark = benchmarks[period]
                period_score = min(actual / benchmark * 100, 100)
                score += period_score * weight
        
        return round(score, 1)
    
    def _estimate_ltv(self, retention_curve: Dict, analytics_data: Dict) -> float:
        """Estimate user lifetime value."""
        
        # Simple LTV estimation
        revenue_data = analytics_data.get("conversions", {}).get("revenue", {})
        arpu_daily = revenue_data.get("arpu_daily", 0.10)
        
        # Project retention for 180 days
        projected_days = 0
        for day in range(1, 181):
            if day == 1:
                retention = retention_curve.get("day_1", 60) / 100
            elif day == 7:
                retention = retention_curve.get("day_7", 30) / 100
            elif day == 30:
                retention = retention_curve.get("day_30", 15) / 100
            elif day == 90:
                retention = retention_curve.get("day_90", 8) / 100
            else:
                # Interpolate or extrapolate
                retention = max(0.05, retention_curve.get("day_90", 8) / 100 * (90 / day))
            
            projected_days += retention
        
        ltv = projected_days * arpu_daily
        return round(ltv, 2)
    
    def _get_sample_user_data(self) -> Dict[str, Any]:
        """Get sample user data."""
        
        return {
            "total": 125000,
            "new": 35000,
            "sessions": 400000,
            "avg_session_duration": 185,
            "screens_per_session": 4.5,
            "bounce_rate": 22.5,
            "dau": 25000,
            "wau": 65000,
            "mau": 100000,
            "retention": {
                "day_1": 65.0,
                "day_3": 48.0,
                "day_7": 35.0,
                "day_14": 25.0,
                "day_30": 18.0,
                "day_60": 14.0,
                "day_90": 12.0
            },
            "cohorts": [
                {
                    "name": "Organic - Content Marketing",
                    "users": 15000,
                    "day_30_retention": 28.0,
                    "ltv": 45.00
                },
                {
                    "name": "Paid Search - Brand",
                    "users": 20000,
                    "day_30_retention": 22.0,
                    "ltv": 38.00
                }
            ]
        }
    
    def _get_sample_events(self) -> List[Dict[str, Any]]:
        """Get sample event data."""
        
        return [
            {"name": "screen_view", "count": 1500000, "unique_users": 120000},
            {"name": "session_start", "count": 400000, "unique_users": 125000},
            {"name": "first_open", "count": 35000, "unique_users": 35000},
            {"name": "add_to_cart", "count": 85000, "unique_users": 45000},
            {"name": "begin_checkout", "count": 45000, "unique_users": 35000},
            {"name": "purchase", "count": 25000, "unique_users": 20000},
            {"name": "share", "count": 15000, "unique_users": 12000},
            {"name": "search", "count": 95000, "unique_users": 55000},
            {"name": "sign_up", "count": 28000, "unique_users": 28000, "is_custom": True},
            {"name": "tutorial_complete", "count": 18000, "unique_users": 18000, "is_custom": True}
        ]
    
    def _get_sample_conversions(self) -> Dict[str, Any]:
        """Get sample conversion data."""
        
        return {
            "goals": [
                {
                    "name": "Complete Purchase",
                    "completions": 25000,
                    "sessions": 400000,
                    "value": 750000
                },
                {
                    "name": "Sign Up",
                    "completions": 28000,
                    "sessions": 125000,
                    "value": 0
                },
                {
                    "name": "Add Payment Method",
                    "completions": 18000,
                    "sessions": 28000,
                    "value": 0
                }
            ],
            "funnels": {
                "purchase_funnel": {
                    "steps": [
                        {"name": "View Product", "users": 95000},
                        {"name": "Add to Cart", "users": 45000},
                        {"name": "Begin Checkout", "users": 28000},
                        {"name": "Add Payment", "users": 20000},
                        {"name": "Complete Purchase", "users": 15000}
                    ]
                },
                "onboarding_funnel": {
                    "steps": [
                        {"name": "App Launch", "users": 35000},
                        {"name": "Sign Up Start", "users": 28000},
                        {"name": "Email Verified", "users": 22000},
                        {"name": "Profile Complete", "users": 18000},
                        {"name": "First Action", "users": 15000}
                    ]
                }
            },
            "revenue": {
                "total": 750000,
                "transactions": 25000,
                "paying_users": 20000,
                "total_users": 125000,
                "arpu_daily": 0.20,
                "trends": {
                    "daily": [25000, 24000, 26000, 27000, 25500, 28000, 29000],
                    "growth_rate": 3.5
                }
            }
        }
    
    def _get_sample_screens(self) -> List[Dict[str, Any]]:
        """Get sample screen data."""
        
        return [
            {
                "name": "HomeScreen",
                "views": 450000,
                "unique_users": 120000,
                "avg_time": 45,
                "exit_rate": 15.2
            },
            {
                "name": "ProductListScreen",
                "views": 320000,
                "unique_users": 95000,
                "avg_time": 85,
                "exit_rate": 22.5
            },
            {
                "name": "ProductDetailScreen",
                "views": 280000,
                "unique_users": 85000,
                "avg_time": 120,
                "exit_rate": 28.5
            },
            {
                "name": "CartScreen",
                "views": 85000,
                "unique_users": 45000,
                "avg_time": 65,
                "exit_rate": 35.0
            },
            {
                "name": "CheckoutScreen",
                "views": 45000,
                "unique_users": 35000,
                "avg_time": 180,
                "exit_rate": 42.0
            },
            {
                "name": "RegistrationScreen",
                "views": 35000,
                "unique_users": 35000,
                "avg_time": 240,
                "exit_rate": 45.0
            }
        ]
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return fallback data for testing."""
        
        return {
            "property_id": "test_property",
            "app_name": "Test Mobile App",
            "metrics": {
                "users": 100000,
                "sessions": 300000,
                "screen_views": 1200000,
                "conversions": 15000
            },
            "insights": [
                "Focus on improving day 7 retention",
                "Optimize checkout funnel - 40% drop-off",
                "Leverage high-performing organic channel"
            ]
        }