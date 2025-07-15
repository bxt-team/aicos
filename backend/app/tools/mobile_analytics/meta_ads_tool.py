import logging
import os
from typing import Dict, Any
from crewai.tools import BaseTool
import json

# Import production tool if available
try:
    from .meta_ads_tool_production import MetaAdsToolProduction
    PRODUCTION_MODE = True
except ImportError:
    PRODUCTION_MODE = False

logger = logging.getLogger(__name__)


class MetaAdsTool(BaseTool):
    name: str = "Meta Ads Analytics Tool"
    description: str = """Analyze Meta Ads (Facebook/Instagram) campaign performance data. 
    Provides insights on campaign metrics, audience performance, creative effectiveness, 
    and optimization opportunities. Requires campaign ID and access token."""
    
    def __init__(self):
        super().__init__()
        # Check if we should use production mode
        self.use_production = PRODUCTION_MODE and all([
            os.getenv("META_APP_ID"),
            os.getenv("META_APP_SECRET"),
            os.getenv("META_AD_ACCOUNT_ID")
        ])
        
        if self.use_production:
            self.production_tool = MetaAdsToolProduction()
            logger.info("Meta Ads Tool initialized in PRODUCTION mode")
        else:
            logger.info("Meta Ads Tool initialized - Production credentials not configured")
    
    def _run(self, input_data: str) -> Dict[str, Any]:
        """
        Analyze Meta Ads campaign data.
        
        Args:
            input_data: Campaign ID or JSON with campaign_id and access_token
            
        Returns:
            Dict containing campaign analysis or error
        """
        try:
            # Parse input
            if input_data.startswith("{"):
                data = json.loads(input_data)
                campaign_id = data.get("campaign_id")
                access_token = data.get("access_token")
            else:
                # Legacy format - just campaign ID
                campaign_id = input_data
                access_token = None
            
            # Check if we have required credentials
            if not access_token:
                logger.error("No access token provided")
                return {
                    "success": False,
                    "error": "Authentication required",
                    "error_code": "NO_ACCESS_TOKEN",
                    "message": "Please provide a Meta access token to analyze campaigns. See META_ADS_PRODUCTION_SETUP.md for instructions."
                }
            
            # Check if production mode is available
            if not self.use_production:
                logger.error("Meta Ads API not configured")
                return {
                    "success": False,
                    "error": "Meta Ads API not configured",
                    "error_code": "API_NOT_CONFIGURED", 
                    "message": "Meta API credentials not found in environment. Please configure META_APP_ID, META_APP_SECRET, and META_AD_ACCOUNT_ID."
                }
            
            # Use production tool with real API
            return self.production_tool._run(input_data)
            
        except Exception as e:
            logger.error(f"Error in Meta Ads Tool: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "TOOL_ERROR",
                "message": "An error occurred while analyzing the campaign."
            }