import logging
from typing import Dict, List, Any
from crewai.tools import BaseTool
from app.tools.mobile_analytics.play_store_api_tool import PlayStoreAPITool
from app.tools.mobile_analytics.sentiment_analysis_tool import SentimentAnalysisTool

logger = logging.getLogger(__name__)


class ReviewExtractorTool(BaseTool):
    name: str = "Review Extractor and Analyzer"
    description: str = """Extract and analyze reviews from Play Store app data. 
    Input can be a package name, URL, or app info dictionary.
    Automatically fetches reviews and performs sentiment analysis."""
    
    def _run(self, input_data: Any) -> Dict[str, Any]:
        """
        Extract and analyze reviews based on input.
        
        Args:
            input_data: Can be a string (package name/URL) or dict with app info
            
        Returns:
            Dict containing reviews and sentiment analysis
        """
        try:
            # Initialize tools inline to avoid pydantic issues
            play_store_tool = PlayStoreAPITool()
            sentiment_tool = SentimentAnalysisTool()
            
            # First, determine what type of input we have
            if isinstance(input_data, str):
                # It's a package name or URL
                app_data_result = play_store_tool._run(input_data)
            elif isinstance(input_data, dict):
                # Check if it already contains app data
                if "package_name" in input_data or "url" in input_data:
                    # Extract package name or URL and fetch data
                    identifier = input_data.get("package_name") or input_data.get("url")
                    app_data_result = play_store_tool._run(identifier)
                else:
                    # Assume it's already fetched app data
                    app_data_result = input_data
            else:
                return {
                    "error": f"Invalid input type: {type(input_data)}. Expected string or dict."
                }
            
            # Check if we successfully got app data
            if not app_data_result.get("success", False):
                return {
                    "error": "Failed to fetch app data",
                    "details": app_data_result.get("error", "Unknown error")
                }
            
            # Extract reviews from the app data
            reviews = app_data_result.get("reviews", [])
            
            if not reviews:
                return {
                    "error": "No reviews found in app data",
                    "app_name": app_data_result.get("app_data", {}).get("app_name", "Unknown")
                }
            
            # Format reviews for sentiment analysis
            formatted_reviews = []
            for review in reviews:
                formatted_review = {
                    "text": review.get("text", ""),
                    "rating": review.get("rating", 0),
                    "date": review.get("date", "")
                }
                if formatted_review["text"]:  # Only include reviews with text
                    formatted_reviews.append(formatted_review)
            
            if not formatted_reviews:
                return {
                    "error": "No reviews with text content found"
                }
            
            # Perform sentiment analysis
            sentiment_analysis = sentiment_tool._run(formatted_reviews)
            
            # Combine results
            app_info = app_data_result.get("app_data", {})
            
            return {
                "success": True,
                "app_name": app_info.get("app_name", "Unknown App"),
                "package_name": app_info.get("package_name", ""),
                "total_reviews_fetched": len(reviews),
                "reviews_analyzed": len(formatted_reviews),
                "reviews": formatted_reviews[:10],  # Include first 10 reviews as sample
                "sentiment_analysis": sentiment_analysis,
                "app_rating": app_info.get("rating", 0),
                "total_app_reviews": app_info.get("total_reviews", 0)
            }
            
        except Exception as e:
            logger.error(f"Error in review extraction and analysis: {e}")
            return {
                "error": str(e),
                "error_type": type(e).__name__
            }