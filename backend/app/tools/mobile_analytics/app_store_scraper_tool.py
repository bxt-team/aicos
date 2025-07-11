import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)


class AppStoreScraperTool(BaseTool):
    name: str = "App Store Scraper"
    description: str = "Scrapes App Store listing data including metadata, ratings, and reviews"
    
    def _run(self, app_url: str = None, bundle_id: str = None) -> Dict[str, Any]:
        """
        Scrape App Store listing data.
        
        Args:
            app_url: Direct URL to the App Store listing
            bundle_id: iOS bundle identifier
            
        Returns:
            Dictionary containing scraped app data
        """
        try:
            # If bundle_id provided, construct URL
            if bundle_id and not app_url:
                # This would use iTunes Search API
                app_url = self._get_app_url_from_bundle_id(bundle_id)
            
            if not app_url:
                return {"error": "No app URL or bundle ID provided"}
            
            # Scrape the App Store page
            scraped_data = self._scrape_app_store_page(app_url)
            
            # Additionally, use iTunes API for structured data
            api_data = self._fetch_itunes_api_data(app_url)
            
            # Combine both data sources
            combined_data = {
                **scraped_data,
                **api_data,
                "scrape_timestamp": datetime.now().isoformat()
            }
            
            return combined_data
            
        except Exception as e:
            logger.error(f"Error scraping App Store: {e}")
            return {"error": str(e)}
    
    def _get_app_url_from_bundle_id(self, bundle_id: str) -> Optional[str]:
        """Get App Store URL from bundle ID using iTunes Search API."""
        try:
            search_url = f"https://itunes.apple.com/lookup?bundleId={bundle_id}"
            response = requests.get(search_url)
            data = response.json()
            
            if data.get("resultCount", 0) > 0:
                app_data = data["results"][0]
                return app_data.get("trackViewUrl")
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching app URL: {e}")
            return None
    
    def _scrape_app_store_page(self, app_url: str) -> Dict[str, Any]:
        """Scrape the actual App Store web page."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            
            response = requests.get(app_url, headers=headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract various elements from the page
            # Note: App Store page structure changes frequently
            data = {
                "page_title": soup.find('title').text if soup.find('title') else None,
                "screenshots_count": len(soup.find_all('picture', class_='we-screenshot')),
                # Additional scraping logic would go here
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error scraping page: {e}")
            return {}
    
    def _fetch_itunes_api_data(self, app_url: str) -> Dict[str, Any]:
        """Fetch structured data from iTunes API."""
        try:
            # Extract app ID from URL
            app_id = self._extract_app_id_from_url(app_url)
            if not app_id:
                return {}
            
            api_url = f"https://itunes.apple.com/lookup?id={app_id}"
            response = requests.get(api_url)
            data = response.json()
            
            if data.get("resultCount", 0) > 0:
                app_data = data["results"][0]
                
                return {
                    "app_id": app_data.get("trackId"),
                    "bundle_id": app_data.get("bundleId"),
                    "title": app_data.get("trackName"),
                    "subtitle": app_data.get("subtitle"),
                    "description": app_data.get("description"),
                    "price": app_data.get("price"),
                    "currency": app_data.get("currency"),
                    "rating_average": app_data.get("averageUserRating"),
                    "rating_count": app_data.get("userRatingCount"),
                    "current_version_rating": app_data.get("averageUserRatingForCurrentVersion"),
                    "current_version_rating_count": app_data.get("userRatingCountForCurrentVersion"),
                    "version": app_data.get("version"),
                    "release_date": app_data.get("releaseDate"),
                    "last_updated": app_data.get("currentVersionReleaseDate"),
                    "category": app_data.get("primaryGenreName"),
                    "categories": app_data.get("genres"),
                    "developer": app_data.get("artistName"),
                    "developer_id": app_data.get("artistId"),
                    "size_bytes": app_data.get("fileSizeBytes"),
                    "languages": app_data.get("languageCodesISO2A"),
                    "age_rating": app_data.get("contentAdvisoryRating"),
                    "screenshots": app_data.get("screenshotUrls"),
                    "ipad_screenshots": app_data.get("ipadScreenshotUrls"),
                    "icon_url": app_data.get("artworkUrl512"),
                    "supported_devices": app_data.get("supportedDevices"),
                    "minimum_os_version": app_data.get("minimumOsVersion"),
                    "release_notes": app_data.get("releaseNotes"),
                    "features": app_data.get("features", []),
                    "advisories": app_data.get("advisories", [])
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching API data: {e}")
            return {}
    
    def _extract_app_id_from_url(self, url: str) -> Optional[str]:
        """Extract app ID from App Store URL."""
        try:
            # URL format: https://apps.apple.com/us/app/app-name/id123456789
            if "/id" in url:
                app_id = url.split("/id")[-1].split("?")[0]
                return app_id
            return None
        except:
            return None