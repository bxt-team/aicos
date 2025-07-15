import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from crewai.tools import BaseTool
import json

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.exceptions import FacebookRequestError

logger = logging.getLogger(__name__)


class MetaAdsToolProduction(BaseTool):
    name: str = "Meta Ads Analytics Tool"
    description: str = """Analyze Meta Ads (Facebook/Instagram) campaign performance data using real-time API. 
    Provides insights on campaign metrics, audience performance, creative effectiveness, 
    and optimization opportunities. Input should be campaign ID and access token."""
    
    def __init__(self):
        super().__init__()
        self.api = None
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
        
    def _initialize_api(self, access_token: str) -> None:
        """Initialize Facebook Ads API with access token."""
        if not self.api or self.api.access_token != access_token:
            FacebookAdsApi.init(
                app_id=os.getenv("META_APP_ID"),
                app_secret=os.getenv("META_APP_SECRET"),
                access_token=access_token
            )
            self.api = FacebookAdsApi.get_default_api()
    
    def _run(self, input_data: str) -> Dict[str, Any]:
        """
        Analyze Meta Ads campaign data using real API.
        
        Args:
            input_data: JSON string with campaign_id, access_token, and optional date_range
            
        Returns:
            Dict containing campaign analysis
        """
        try:
            # Parse input
            data = json.loads(input_data)
            campaign_id = data.get("campaign_id")
            access_token = data.get("access_token")
            date_range = data.get("date_range", {})
            
            if not campaign_id or not access_token:
                raise ValueError("Both campaign_id and access_token are required")
            
            # Initialize API
            self._initialize_api(access_token)
            
            logger.info(f"Fetching real-time data for campaign: {campaign_id}")
            
            # Fetch campaign data
            campaign_data = self._fetch_campaign_data(campaign_id, date_range)
            
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
                "insights": insights,
                "data_freshness": datetime.now().isoformat()
            }
            
        except FacebookRequestError as e:
            logger.error(f"Facebook API error: {e}")
            return {
                "success": False,
                "error": f"Facebook API error: {e.api_error_message()}",
                "error_code": e.api_error_code(),
                "error_type": e.api_error_type()
            }
        except Exception as e:
            logger.error(f"Error analyzing Meta Ads campaign: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _fetch_campaign_data(self, campaign_id: str, date_range: Dict[str, str]) -> Dict[str, Any]:
        """Fetch real campaign data from Meta Marketing API."""
        
        # Set up date parameters
        params = {
            'level': 'campaign',
            'fields': [
                'name',
                'objective',
                'status',
                'daily_budget',
                'lifetime_budget',
                'spend',
                'impressions',
                'clicks',
                'ctr',
                'cpm',
                'cpp',
                'cpc',
                'actions',
                'action_values',
                'cost_per_action_type',
                'conversion_values',
                'conversions',
                'reach',
                'frequency'
            ]
        }
        
        # Add date range if provided
        if date_range:
            if 'start' in date_range:
                params['time_range'] = {
                    'since': date_range['start'],
                    'until': date_range.get('end', datetime.now().strftime('%Y-%m-%d'))
                }
        else:
            # Default to last 30 days
            params['time_range'] = {
                'since': (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
                'until': datetime.now().strftime('%Y-%m-%d')
            }
        
        # Fetch campaign
        campaign = Campaign(campaign_id)
        campaign_info = campaign.api_get(fields=['name', 'objective', 'status', 'daily_budget', 'lifetime_budget'])
        
        # Fetch insights
        insights = campaign.get_insights(params=params)
        insight_data = insights[0] if insights else {}
        
        # Extract install/conversion data
        actions = insight_data.get('actions', [])
        installs = 0
        for action in actions:
            if action['action_type'] in ['mobile_app_install', 'app_install']:
                installs = int(action['value'])
                break
        
        # Get cost per install
        cost_per_actions = insight_data.get('cost_per_action_type', [])
        cpi = None
        for cpa in cost_per_actions:
            if cpa['action_type'] in ['mobile_app_install', 'app_install']:
                cpi = float(cpa['value'])
                break
        
        # Fetch ad sets
        ad_sets = self._fetch_ad_sets(campaign_id)
        
        # Fetch ads
        ads = self._fetch_ads(campaign_id)
        
        return {
            "campaign_id": campaign_id,
            "campaign_name": campaign_info.get('name'),
            "objective": campaign_info.get('objective'),
            "status": campaign_info.get('status'),
            "daily_budget": campaign_info.get('daily_budget'),
            "lifetime_budget": campaign_info.get('lifetime_budget'),
            "spend": float(insight_data.get('spend', 0)),
            "impressions": int(insight_data.get('impressions', 0)),
            "clicks": int(insight_data.get('clicks', 0)),
            "reach": int(insight_data.get('reach', 0)),
            "frequency": float(insight_data.get('frequency', 0)),
            "ctr": float(insight_data.get('ctr', 0)),
            "cpm": float(insight_data.get('cpm', 0)),
            "cpc": float(insight_data.get('cpc', 0)),
            "installs": installs,
            "cost_per_install": cpi,
            "ad_sets": ad_sets,
            "ads": ads,
            "date_range": params['time_range']
        }
    
    def _fetch_ad_sets(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Fetch ad sets for the campaign."""
        
        campaign = Campaign(campaign_id)
        ad_sets = campaign.get_ad_sets(fields=[
            'name',
            'status',
            'targeting',
            'daily_budget',
            'lifetime_budget'
        ])
        
        ad_set_data = []
        for ad_set in ad_sets:
            # Get insights for each ad set
            insights = ad_set.get_insights(params={
                'fields': [
                    'impressions',
                    'clicks',
                    'spend',
                    'actions',
                    'cost_per_action_type',
                    'ctr',
                    'cpm'
                ]
            })
            
            insight_data = insights[0] if insights else {}
            
            # Extract installs
            actions = insight_data.get('actions', [])
            installs = 0
            for action in actions:
                if action['action_type'] in ['mobile_app_install', 'app_install']:
                    installs = int(action['value'])
                    break
            
            # Extract CPI
            cost_per_actions = insight_data.get('cost_per_action_type', [])
            cpi = None
            for cpa in cost_per_actions:
                if cpa['action_type'] in ['mobile_app_install', 'app_install']:
                    cpi = float(cpa['value'])
                    break
            
            ad_set_data.append({
                "id": ad_set.get('id'),
                "name": ad_set.get('name'),
                "status": ad_set.get('status'),
                "targeting": ad_set.get('targeting', {}),
                "metrics": {
                    "impressions": int(insight_data.get('impressions', 0)),
                    "clicks": int(insight_data.get('clicks', 0)),
                    "spend": float(insight_data.get('spend', 0)),
                    "installs": installs,
                    "cpi": cpi,
                    "ctr": float(insight_data.get('ctr', 0)),
                    "cpm": float(insight_data.get('cpm', 0))
                }
            })
        
        return ad_set_data
    
    def _fetch_ads(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Fetch ads for the campaign."""
        
        campaign = Campaign(campaign_id)
        ads = campaign.get_ads(fields=[
            'name',
            'status',
            'creative'
        ])
        
        ad_data = []
        for ad in ads:
            # Get creative details
            creative_id = ad.get('creative', {}).get('id')
            creative_info = {}
            if creative_id:
                try:
                    creative = AdCreative(creative_id)
                    creative_data = creative.api_get(fields=[
                        'object_type',
                        'title',
                        'body',
                        'image_url',
                        'video_id',
                        'call_to_action_type'
                    ])
                    creative_info = {
                        "format": creative_data.get('object_type', 'unknown'),
                        "title": creative_data.get('title'),
                        "body": creative_data.get('body'),
                        "cta": creative_data.get('call_to_action_type'),
                        "has_video": bool(creative_data.get('video_id'))
                    }
                except:
                    pass
            
            # Get insights
            insights = ad.get_insights(params={
                'fields': [
                    'impressions',
                    'clicks',
                    'spend',
                    'actions',
                    'cost_per_action_type',
                    'ctr',
                    'frequency',
                    'video_play_actions',
                    'video_avg_time_watched_actions'
                ]
            })
            
            insight_data = insights[0] if insights else {}
            
            # Extract metrics
            actions = insight_data.get('actions', [])
            installs = 0
            for action in actions:
                if action['action_type'] in ['mobile_app_install', 'app_install']:
                    installs = int(action['value'])
                    break
            
            cost_per_actions = insight_data.get('cost_per_action_type', [])
            cpi = None
            for cpa in cost_per_actions:
                if cpa['action_type'] in ['mobile_app_install', 'app_install']:
                    cpi = float(cpa['value'])
                    break
            
            # Video metrics
            video_plays = 0
            video_actions = insight_data.get('video_play_actions', [])
            for action in video_actions:
                if action['action_type'] == 'video_view':
                    video_plays = int(action['value'])
                    break
            
            ad_data.append({
                "id": ad.get('id'),
                "name": ad.get('name'),
                "status": ad.get('status'),
                "creative": creative_info,
                "metrics": {
                    "impressions": int(insight_data.get('impressions', 0)),
                    "clicks": int(insight_data.get('clicks', 0)),
                    "spend": float(insight_data.get('spend', 0)),
                    "installs": installs,
                    "cpi": cpi,
                    "ctr": float(insight_data.get('ctr', 0)),
                    "frequency": float(insight_data.get('frequency', 0)),
                    "video_plays": video_plays
                }
            })
        
        return ad_data
    
    def _analyze_performance(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze overall campaign performance metrics."""
        
        impressions = campaign_data.get("impressions", 0)
        clicks = campaign_data.get("clicks", 0)
        installs = campaign_data.get("installs", 0)
        spend = campaign_data.get("spend", 0)
        reach = campaign_data.get("reach", 0)
        
        ctr = campaign_data.get("ctr", 0)
        cpi = campaign_data.get("cost_per_install", 0) or (spend / installs if installs > 0 else 0)
        cvr = (installs / clicks * 100) if clicks > 0 else 0
        cpm = campaign_data.get("cpm", 0)
        cpc = campaign_data.get("cpc", 0)
        frequency = campaign_data.get("frequency", 0)
        
        # Calculate ROAS if we have revenue data
        # This would need to be integrated with your app's revenue tracking
        estimated_roas = 0  # Placeholder - implement based on your revenue tracking
        
        return {
            "metrics": {
                "impressions": impressions,
                "reach": reach,
                "frequency": round(frequency, 2),
                "clicks": clicks,
                "ctr": round(ctr, 2),
                "installs": installs,
                "conversion_rate": round(cvr, 2),
                "spend": round(spend, 2),
                "cpi": round(cpi, 2),
                "cpm": round(cpm, 2),
                "cpc": round(cpc, 2),
                "estimated_roas": estimated_roas
            },
            "performance_rating": self._rate_performance(ctr, cpi, cvr),
            "daily_average": {
                "spend": round(spend / 30, 2),  # Adjust based on actual date range
                "installs": round(installs / 30, 2),
                "impressions": round(impressions / 30, 2)
            }
        }
    
    def _analyze_audience(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze audience segment performance."""
        
        ad_sets = campaign_data.get("ad_sets", [])
        
        # Sort by performance (lowest CPI)
        ad_sets_sorted = sorted(
            ad_sets, 
            key=lambda x: x["metrics"].get("cpi", float('inf'))
        )
        
        # Extract top performing audiences
        top_audiences = []
        for ad_set in ad_sets_sorted[:5]:
            targeting = ad_set.get("targeting", {})
            metrics = ad_set.get("metrics", {})
            
            # Calculate performance index (compared to campaign average)
            campaign_cpi = campaign_data.get("cost_per_install", 0)
            ad_set_cpi = metrics.get("cpi", 0)
            performance_index = (campaign_cpi / ad_set_cpi) if ad_set_cpi > 0 else 0
            
            top_audiences.append({
                "ad_set_name": ad_set.get("name"),
                "ad_set_id": ad_set.get("id"),
                "targeting": {
                    "age_min": targeting.get("age_min", 18),
                    "age_max": targeting.get("age_max", 65),
                    "genders": targeting.get("genders", []),
                    "geo_locations": targeting.get("geo_locations", {}),
                    "interests": targeting.get("interests", []),
                    "behaviors": targeting.get("behaviors", []),
                    "custom_audiences": targeting.get("custom_audiences", [])
                },
                "performance": {
                    "impressions": metrics.get("impressions", 0),
                    "installs": metrics.get("installs", 0),
                    "cpi": metrics.get("cpi", 0),
                    "ctr": metrics.get("ctr", 0),
                    "performance_index": round(performance_index, 2)
                }
            })
        
        return {
            "top_audiences": top_audiences,
            "audience_insights": self._generate_audience_insights(ad_sets),
            "expansion_opportunities": self._identify_audience_opportunities(ad_sets, campaign_data)
        }
    
    def _analyze_creatives(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze creative performance."""
        
        ads = campaign_data.get("ads", [])
        
        # Sort by performance (lowest CPI)
        ads_sorted = sorted(
            ads,
            key=lambda x: x["metrics"].get("cpi", float('inf'))
        )
        
        # Analyze by format
        format_performance = {}
        for ad in ads:
            format_type = ad.get("creative", {}).get("format", "unknown")
            metrics = ad.get("metrics", {})
            
            if format_type not in format_performance:
                format_performance[format_type] = {
                    "count": 0,
                    "total_impressions": 0,
                    "total_installs": 0,
                    "total_spend": 0,
                    "total_clicks": 0,
                    "avg_ctr": [],
                    "avg_frequency": []
                }
            
            format_performance[format_type]["count"] += 1
            format_performance[format_type]["total_impressions"] += metrics.get("impressions", 0)
            format_performance[format_type]["total_installs"] += metrics.get("installs", 0)
            format_performance[format_type]["total_spend"] += metrics.get("spend", 0)
            format_performance[format_type]["total_clicks"] += metrics.get("clicks", 0)
            format_performance[format_type]["avg_ctr"].append(metrics.get("ctr", 0))
            format_performance[format_type]["avg_frequency"].append(metrics.get("frequency", 0))
        
        # Calculate averages
        for format_type, data in format_performance.items():
            if data["avg_ctr"]:
                data["avg_ctr"] = round(sum(data["avg_ctr"]) / len(data["avg_ctr"]), 2)
            else:
                data["avg_ctr"] = 0
                
            if data["avg_frequency"]:
                data["avg_frequency"] = round(sum(data["avg_frequency"]) / len(data["avg_frequency"]), 2)
            else:
                data["avg_frequency"] = 0
            
            # Calculate CPI for format
            if data["total_installs"] > 0:
                data["cpi"] = round(data["total_spend"] / data["total_installs"], 2)
            else:
                data["cpi"] = 0
        
        # Get top creatives
        top_creatives = []
        for ad in ads_sorted[:5]:
            creative = ad.get("creative", {})
            metrics = ad.get("metrics", {})
            
            top_creatives.append({
                "ad_id": ad.get("id"),
                "ad_name": ad.get("name"),
                "format": creative.get("format", "unknown"),
                "has_video": creative.get("has_video", False),
                "cta": creative.get("cta"),
                "metrics": {
                    "impressions": metrics.get("impressions", 0),
                    "clicks": metrics.get("clicks", 0),
                    "ctr": metrics.get("ctr", 0),
                    "installs": metrics.get("installs", 0),
                    "cpi": metrics.get("cpi", 0),
                    "frequency": metrics.get("frequency", 0)
                }
            })
        
        return {
            "top_creatives": top_creatives,
            "format_performance": format_performance,
            "creative_insights": self._generate_creative_insights(ads),
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
        
        # CTR insights
        if metrics["ctr"] < 1.0:
            insights["key_findings"].append(f"CTR ({metrics['ctr']}%) is below industry average (1.0%). Creative optimization needed.")
            insights["recommendations"].append({
                "area": "Creative",
                "action": "Test new ad formats with stronger visual hooks and clearer value propositions",
                "priority": "high",
                "expected_impact": "Increase CTR by 30-50%"
            })
        elif metrics["ctr"] > 2.0:
            insights["key_findings"].append(f"Strong CTR performance ({metrics['ctr']}%) indicates engaging creative.")
        
        # CPI insights
        if metrics["cpi"] > 25:
            insights["key_findings"].append(f"High CPI (${metrics['cpi']}) affecting campaign ROI.")
            insights["recommendations"].append({
                "area": "Targeting",
                "action": "Refine audience targeting to focus on highest-converting segments",
                "priority": "high",
                "expected_impact": f"Reduce CPI by ${round(metrics['cpi'] * 0.2, 2)}"
            })
        
        # Frequency insights
        if metrics["frequency"] > 3.5:
            insights["risks"].append(f"High ad frequency ({metrics['frequency']}) may cause audience fatigue")
            insights["recommendations"].append({
                "area": "Reach",
                "action": "Expand audience targeting or add frequency cap",
                "priority": "medium",
                "expected_impact": "Reduce frequency to 2.5-3.0"
            })
        
        # Audience insights
        top_audiences = audience.get("top_audiences", [])
        if top_audiences:
            best_audience = top_audiences[0]
            if best_audience["performance"]["performance_index"] > 1.5:
                insights["opportunities"].append(
                    f"Top audience '{best_audience['ad_set_name']}' performs "
                    f"{best_audience['performance']['performance_index']}x better than average"
                )
                insights["recommendations"].append({
                    "area": "Budget",
                    "action": f"Increase budget allocation to '{best_audience['ad_set_name']}' by 50%",
                    "priority": "high",
                    "expected_impact": f"Generate {round(best_audience['performance']['installs'] * 0.5)} additional installs"
                })
        
        # Creative insights
        format_performance = creatives.get("format_performance", {})
        best_format = min(format_performance.items(), key=lambda x: x[1].get("cpi", float('inf'))) if format_performance else None
        
        if best_format and best_format[1]["cpi"] > 0:
            insights["opportunities"].append(
                f"{best_format[0].title()} ads show best CPI performance (${best_format[1]['cpi']})"
            )
            insights["recommendations"].append({
                "area": "Creative",
                "action": f"Create more {best_format[0]} format ads following top performer patterns",
                "priority": "medium",
                "expected_impact": "Improve overall campaign CPI by 15%"
            })
        
        # Creative fatigue insights
        creative_fatigue = creatives.get("creative_fatigue", {})
        if creative_fatigue.get("high_frequency_ads", []):
            insights["risks"].append(
                f"{len(creative_fatigue['high_frequency_ads'])} ads showing signs of creative fatigue"
            )
        
        return insights
    
    def _rate_performance(self, ctr: float, cpi: float, cvr: float) -> str:
        """Rate overall campaign performance."""
        
        score = 0
        
        # CTR scoring (mobile app install benchmarks)
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
    
    def _generate_audience_insights(self, ad_sets: List[Dict]) -> List[str]:
        """Generate insights from audience performance."""
        
        insights = []
        
        if not ad_sets:
            return insights
        
        # Find performance patterns
        cpi_values = [a["metrics"].get("cpi", 0) for a in ad_sets if a["metrics"].get("cpi", 0) > 0]
        if cpi_values:
            avg_cpi = sum(cpi_values) / len(cpi_values)
            best_cpi = min(cpi_values)
            
            if best_cpi < avg_cpi * 0.7:
                improvement = round((1 - best_cpi/avg_cpi) * 100)
                insights.append(
                    f"Top performing audience shows {improvement}% better CPI than average"
                )
        
        return insights
    
    def _identify_audience_opportunities(self, ad_sets: List[Dict], campaign_data: Dict) -> List[Dict]:
        """Identify audience expansion opportunities."""
        
        opportunities = []
        
        # Look for high-performing segments
        for ad_set in ad_sets:
            metrics = ad_set.get("metrics", {})
            cpi = metrics.get("cpi", 0)
            campaign_cpi = campaign_data.get("cost_per_install", 0)
            
            if cpi > 0 and campaign_cpi > 0 and cpi < campaign_cpi * 0.8:
                opportunities.append({
                    "type": "expansion",
                    "audience": ad_set.get("name"),
                    "recommendation": f"Create lookalike audience from '{ad_set.get('name')}'",
                    "expected_impact": "20-30% increase in quality installs"
                })
        
        return opportunities[:3]  # Return top 3 opportunities
    
    def _generate_creative_insights(self, ads: List[Dict]) -> List[str]:
        """Generate insights from creative performance."""
        
        insights = []
        
        # Analyze video vs static performance
        video_ads = [a for a in ads if a.get("creative", {}).get("has_video")]
        static_ads = [a for a in ads if not a.get("creative", {}).get("has_video")]
        
        if video_ads and static_ads:
            video_cpi = [a["metrics"].get("cpi", 0) for a in video_ads if a["metrics"].get("cpi", 0) > 0]
            static_cpi = [a["metrics"].get("cpi", 0) for a in static_ads if a["metrics"].get("cpi", 0) > 0]
            
            if video_cpi and static_cpi:
                avg_video_cpi = sum(video_cpi) / len(video_cpi)
                avg_static_cpi = sum(static_cpi) / len(static_cpi)
                
                if avg_video_cpi < avg_static_cpi * 0.8:
                    insights.append("Video ads show 20%+ better CPI performance than static ads")
                elif avg_static_cpi < avg_video_cpi * 0.8:
                    insights.append("Static ads outperform video ads - consider testing more image creatives")
        
        return insights
    
    def _detect_creative_fatigue(self, ads: List[Dict]) -> Dict[str, Any]:
        """Detect signs of creative fatigue."""
        
        high_frequency_ads = []
        frequencies = []
        
        for ad in ads:
            metrics = ad.get("metrics", {})
            frequency = metrics.get("frequency", 0)
            frequencies.append(frequency)
            
            if frequency > 3.5:
                high_frequency_ads.append({
                    "ad_id": ad.get("id"),
                    "ad_name": ad.get("name"),
                    "frequency": frequency,
                    "recommendation": "Refresh creative or reduce frequency cap"
                })
        
        avg_frequency = sum(frequencies) / len(frequencies) if frequencies else 0
        
        return {
            "avg_frequency": round(avg_frequency, 2),
            "fatigue_threshold": 3.5,
            "high_frequency_ads": high_frequency_ads
        }