import logging
from typing import Dict, Any, Optional, List
from crewai.tools import BaseTool
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MetaAdsTool(BaseTool):
    name: str = "Meta Ads Analytics Tool"
    description: str = """Analyze Meta Ads (Facebook/Instagram) campaign performance data. 
    Provides insights on campaign metrics, audience performance, creative effectiveness, 
    and optimization opportunities. Input should be campaign data or campaign ID."""
    
    def _run(self, input_data: str) -> Dict[str, Any]:
        """
        Analyze Meta Ads campaign data.
        
        Args:
            input_data: Campaign ID or campaign data JSON
            
        Returns:
            Dict containing campaign analysis
        """
        try:
            # Parse input
            if input_data.startswith("{"):
                campaign_data = json.loads(input_data)
            else:
                # Assume it's a campaign ID
                campaign_data = self._fetch_campaign_data(input_data)
            
            logger.info(f"Analyzing Meta Ads campaign: {campaign_data.get('campaign_id', 'Unknown')}")
            
            # Analyze campaign performance
            performance = self._analyze_performance(campaign_data)
            
            # Analyze audience segments
            audience = self._analyze_audience(campaign_data)
            
            # Analyze creative performance
            creatives = self._analyze_creatives(campaign_data)
            
            # Generate insights and recommendations
            insights = self._generate_insights(performance, audience, creatives)
            
            return {
                "success": True,
                "campaign_data": campaign_data,
                "performance_analysis": performance,
                "audience_analysis": audience,
                "creative_analysis": creatives,
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"Error analyzing Meta Ads campaign: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_data": self._get_fallback_data()
            }
    
    def _fetch_campaign_data(self, campaign_id: str) -> Dict[str, Any]:
        """Fetch campaign data from Meta Ads API (simulated)."""
        
        # In production, this would use the Meta Marketing API
        # For now, return simulated data
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": "Mobile App Install - Q1 2024",
            "objective": "APP_INSTALLS",
            "status": "ACTIVE",
            "daily_budget": 1000,
            "lifetime_spend": 25000,
            "start_date": "2024-01-01",
            "impressions": 1250000,
            "clicks": 37500,
            "installs": 1875,
            "ad_sets": self._get_sample_ad_sets(),
            "ads": self._get_sample_ads()
        }
    
    def _analyze_performance(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall campaign performance metrics."""
        
        impressions = campaign_data.get("impressions", 0)
        clicks = campaign_data.get("clicks", 0)
        installs = campaign_data.get("installs", 0)
        spend = campaign_data.get("lifetime_spend", 0)
        
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        cpi = (spend / installs) if installs > 0 else 0
        cvr = (installs / clicks * 100) if clicks > 0 else 0
        cpm = (spend / impressions * 1000) if impressions > 0 else 0
        
        return {
            "metrics": {
                "impressions": impressions,
                "clicks": clicks,
                "ctr": round(ctr, 2),
                "installs": installs,
                "conversion_rate": round(cvr, 2),
                "spend": spend,
                "cpi": round(cpi, 2),
                "cpm": round(cpm, 2)
            },
            "performance_rating": self._rate_performance(ctr, cpi, cvr),
            "trends": self._analyze_trends(campaign_data)
        }
    
    def _analyze_audience(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience segment performance."""
        
        ad_sets = campaign_data.get("ad_sets", [])
        
        audience_performance = []
        for ad_set in ad_sets:
            targeting = ad_set.get("targeting", {})
            metrics = ad_set.get("metrics", {})
            
            audience_performance.append({
                "ad_set_name": ad_set.get("name"),
                "targeting": {
                    "age_range": targeting.get("age_range", "18-65"),
                    "genders": targeting.get("genders", ["all"]),
                    "locations": targeting.get("locations", []),
                    "interests": targeting.get("interests", [])
                },
                "performance": {
                    "impressions": metrics.get("impressions", 0),
                    "installs": metrics.get("installs", 0),
                    "cpi": metrics.get("cpi", 0),
                    "performance_index": metrics.get("performance_index", 1.0)
                }
            })
        
        # Sort by performance
        audience_performance.sort(
            key=lambda x: x["performance"]["performance_index"], 
            reverse=True
        )
        
        return {
            "top_audiences": audience_performance[:5],
            "audience_insights": self._generate_audience_insights(audience_performance),
            "expansion_opportunities": self._identify_audience_opportunities(audience_performance)
        }
    
    def _analyze_creatives(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze creative performance."""
        
        ads = campaign_data.get("ads", [])
        
        creative_performance = []
        format_summary = {}
        
        for ad in ads:
            creative = ad.get("creative", {})
            metrics = ad.get("metrics", {})
            format_type = creative.get("format", "unknown")
            
            creative_performance.append({
                "ad_id": ad.get("id"),
                "ad_name": ad.get("name"),
                "format": format_type,
                "thumbnail": creative.get("thumbnail_url", ""),
                "metrics": {
                    "impressions": metrics.get("impressions", 0),
                    "clicks": metrics.get("clicks", 0),
                    "ctr": metrics.get("ctr", 0),
                    "installs": metrics.get("installs", 0),
                    "cpi": metrics.get("cpi", 0),
                    "engagement_rate": metrics.get("engagement_rate", 0)
                },
                "creative_score": self._calculate_creative_score(metrics)
            })
            
            # Aggregate by format
            if format_type not in format_summary:
                format_summary[format_type] = {
                    "count": 0,
                    "total_impressions": 0,
                    "total_installs": 0,
                    "total_spend": 0
                }
            
            format_summary[format_type]["count"] += 1
            format_summary[format_type]["total_impressions"] += metrics.get("impressions", 0)
            format_summary[format_type]["total_installs"] += metrics.get("installs", 0)
            format_summary[format_type]["total_spend"] += metrics.get("spend", 0)
        
        # Sort by performance
        creative_performance.sort(
            key=lambda x: x["creative_score"], 
            reverse=True
        )
        
        return {
            "top_creatives": creative_performance[:5],
            "format_performance": format_summary,
            "creative_insights": self._generate_creative_insights(creative_performance),
            "creative_fatigue": self._detect_creative_fatigue(ads)
        }
    
    def _generate_insights(self, performance: Dict, audience: Dict, creatives: Dict) -> Dict[str, Any]:
        """Generate actionable insights from analysis."""
        
        insights = {
            "key_findings": [],
            "opportunities": [],
            "risks": [],
            "recommendations": []
        }
        
        # Performance insights
        metrics = performance["metrics"]
        if metrics["ctr"] < 1.0:
            insights["key_findings"].append("CTR is below industry average (1.0%). Creative refresh needed.")
            insights["recommendations"].append({
                "area": "Creative",
                "action": "Test new ad formats and messaging to improve CTR",
                "priority": "high"
            })
        
        if metrics["cpi"] > 20:
            insights["key_findings"].append(f"CPI (${metrics['cpi']}) is high. Audience refinement needed.")
            insights["recommendations"].append({
                "area": "Targeting",
                "action": "Narrow audience targeting to high-intent users",
                "priority": "high"
            })
        
        # Audience insights
        top_audiences = audience.get("top_audiences", [])
        if top_audiences:
            best_audience = top_audiences[0]
            insights["opportunities"].append(
                f"Best performing audience: {best_audience['ad_set_name']} "
                f"with {best_audience['performance']['performance_index']}x performance"
            )
        
        # Creative insights
        creative_fatigue = creatives.get("creative_fatigue", {})
        if creative_fatigue.get("high_frequency_ads", []):
            insights["risks"].append(
                f"{len(creative_fatigue['high_frequency_ads'])} ads showing creative fatigue"
            )
            insights["recommendations"].append({
                "area": "Creative",
                "action": "Refresh high-frequency ads to maintain performance",
                "priority": "medium"
            })
        
        return insights
    
    def _rate_performance(self, ctr: float, cpi: float, cvr: float) -> str:
        """Rate overall campaign performance."""
        
        score = 0
        
        # CTR scoring
        if ctr >= 2.0:
            score += 3
        elif ctr >= 1.0:
            score += 2
        elif ctr >= 0.5:
            score += 1
        
        # CPI scoring
        if cpi <= 10:
            score += 3
        elif cpi <= 20:
            score += 2
        elif cpi <= 30:
            score += 1
        
        # CVR scoring
        if cvr >= 5.0:
            score += 3
        elif cvr >= 3.0:
            score += 2
        elif cvr >= 1.0:
            score += 1
        
        if score >= 7:
            return "Excellent"
        elif score >= 5:
            return "Good"
        elif score >= 3:
            return "Average"
        else:
            return "Needs Improvement"
    
    def _analyze_trends(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends."""
        
        # In production, this would analyze time-series data
        # For now, return simulated trends
        
        return {
            "cpi_trend": "decreasing",
            "ctr_trend": "stable",
            "scale_trend": "increasing",
            "weekly_performance": [
                {"week": 1, "cpi": 18.50, "installs": 350},
                {"week": 2, "cpi": 16.75, "installs": 425},
                {"week": 3, "cpi": 15.00, "installs": 500},
                {"week": 4, "cpi": 14.25, "installs": 600}
            ]
        }
    
    def _generate_audience_insights(self, audience_performance: List[Dict]) -> List[str]:
        """Generate insights from audience performance."""
        
        insights = []
        
        if audience_performance:
            # Compare top and bottom performers
            if len(audience_performance) >= 2:
                top = audience_performance[0]
                bottom = audience_performance[-1]
                
                if top["performance"]["cpi"] < bottom["performance"]["cpi"] * 0.7:
                    insights.append(
                        f"Top audience segment performs {round((1 - top['performance']['cpi']/bottom['performance']['cpi']) * 100)}% "
                        f"better than worst segment"
                    )
        
        return insights
    
    def _identify_audience_opportunities(self, audience_performance: List[Dict]) -> List[Dict]:
        """Identify audience expansion opportunities."""
        
        opportunities = []
        
        # Look for high-performing segments to expand
        for audience in audience_performance[:3]:
            if audience["performance"]["performance_index"] > 1.2:
                opportunities.append({
                    "type": "expansion",
                    "audience": audience["ad_set_name"],
                    "recommendation": "Create lookalike audience",
                    "expected_impact": "15-20% more quality installs"
                })
        
        return opportunities
    
    def _calculate_creative_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate a composite score for creative performance."""
        
        ctr_weight = 0.3
        cvr_weight = 0.4
        engagement_weight = 0.3
        
        ctr_score = min(metrics.get("ctr", 0) / 2.0, 1.0)  # Normalize to 0-1
        cvr_score = min(metrics.get("conversion_rate", 0) / 5.0, 1.0)
        engagement_score = min(metrics.get("engagement_rate", 0) / 10.0, 1.0)
        
        return (
            ctr_score * ctr_weight +
            cvr_score * cvr_weight +
            engagement_score * engagement_weight
        ) * 100
    
    def _generate_creative_insights(self, creative_performance: List[Dict]) -> List[str]:
        """Generate insights from creative performance."""
        
        insights = []
        
        # Analyze format performance
        video_ads = [c for c in creative_performance if c["format"] == "video"]
        image_ads = [c for c in creative_performance if c["format"] == "image"]
        
        if video_ads and image_ads:
            avg_video_score = sum(v["creative_score"] for v in video_ads) / len(video_ads)
            avg_image_score = sum(i["creative_score"] for i in image_ads) / len(image_ads)
            
            if avg_video_score > avg_image_score * 1.2:
                insights.append("Video ads outperform image ads by 20%+")
        
        return insights
    
    def _detect_creative_fatigue(self, ads: List[Dict]) -> Dict[str, Any]:
        """Detect signs of creative fatigue."""
        
        high_frequency_ads = []
        
        for ad in ads:
            metrics = ad.get("metrics", {})
            frequency = metrics.get("frequency", 0)
            
            if frequency > 3.5:
                high_frequency_ads.append({
                    "ad_id": ad.get("id"),
                    "ad_name": ad.get("name"),
                    "frequency": frequency,
                    "recommendation": "Refresh creative or pause ad"
                })
        
        return {
            "avg_frequency": 2.8,
            "fatigue_threshold": 3.5,
            "high_frequency_ads": high_frequency_ads
        }
    
    def _get_sample_ad_sets(self) -> List[Dict[str, Any]]:
        """Get sample ad set data."""
        
        return [
            {
                "id": "12345",
                "name": "Mobile Gamers 18-34",
                "targeting": {
                    "age_range": "18-34",
                    "genders": ["all"],
                    "interests": ["Mobile gaming", "Casual games"],
                    "locations": ["United States"]
                },
                "metrics": {
                    "impressions": 500000,
                    "installs": 750,
                    "cpi": 12.00,
                    "performance_index": 1.35
                }
            },
            {
                "id": "12346",
                "name": "Lookalike 1% - High Value Users",
                "targeting": {
                    "age_range": "18-65",
                    "genders": ["all"],
                    "custom_audience": "Lookalike 1%",
                    "locations": ["United States", "Canada"]
                },
                "metrics": {
                    "impressions": 400000,
                    "installs": 600,
                    "cpi": 14.50,
                    "performance_index": 1.15
                }
            }
        ]
    
    def _get_sample_ads(self) -> List[Dict[str, Any]]:
        """Get sample ad data."""
        
        return [
            {
                "id": "ad_123",
                "name": "Gameplay Video - Action",
                "creative": {
                    "format": "video",
                    "thumbnail_url": "https://example.com/thumb1.jpg"
                },
                "metrics": {
                    "impressions": 300000,
                    "clicks": 12000,
                    "ctr": 4.0,
                    "installs": 450,
                    "cpi": 11.00,
                    "engagement_rate": 8.5,
                    "frequency": 2.3
                }
            },
            {
                "id": "ad_124",
                "name": "Feature Carousel",
                "creative": {
                    "format": "carousel",
                    "thumbnail_url": "https://example.com/thumb2.jpg"
                },
                "metrics": {
                    "impressions": 250000,
                    "clicks": 7500,
                    "ctr": 3.0,
                    "installs": 300,
                    "cpi": 15.00,
                    "engagement_rate": 6.0,
                    "frequency": 2.8
                }
            }
        ]
    
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Return fallback data for testing."""
        
        return {
            "campaign_id": "test_campaign",
            "campaign_name": "Test Mobile App Campaign",
            "performance": {
                "impressions": 1000000,
                "clicks": 25000,
                "installs": 1250,
                "spend": 18750,
                "cpi": 15.00,
                "ctr": 2.5
            },
            "top_audiences": [
                "Mobile Gamers 25-34",
                "App Enthusiasts",
                "Tech Early Adopters"
            ],
            "recommendations": [
                "Increase budget for top-performing audiences",
                "Test new video creative formats",
                "Implement cost caps on underperforming ad sets"
            ]
        }