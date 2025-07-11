import logging
from typing import Dict, Any, Optional, List
from crewai.tools import BaseTool
import requests
from bs4 import BeautifulSoup
import re
import json

logger = logging.getLogger(__name__)


class PlayStoreScraperTool(BaseTool):
    name: str = "Play Store Scraper"
    description: str = """Scrape and analyze Google Play Store app listings. 
    Extracts app metadata, ratings, reviews, keywords, and visual assets information.
    Input should be a Play Store URL or package name."""
    
    def _run(self, input_data: str) -> Dict[str, Any]:
        """
        Scrape Play Store listing data.
        
        Args:
            input_data: Play Store URL or package name
            
        Returns:
            Dict containing app metadata and analysis
        """
        try:
            # Determine if input is URL or package name
            if input_data.startswith("http"):
                package_name = self._extract_package_from_url(input_data)
                url = input_data
            else:
                package_name = input_data
                url = f"https://play.google.com/store/apps/details?id={package_name}"
            
            logger.info(f"Scraping Play Store data for: {package_name}")
            
            # Fetch the page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract app data
            app_data = self._extract_app_data(soup, package_name)
            
            # Extract keywords from content
            keywords = self._extract_keywords(soup)
            
            # Extract visual assets info
            visual_info = self._extract_visual_info(soup)
            
            # Extract reviews sample
            reviews = self._extract_reviews(soup)
            
            return {
                "success": True,
                "app_data": app_data,
                "keywords": keywords,
                "visual_assets": visual_info,
                "recent_reviews": reviews,
                "url": url
            }
            
        except Exception as e:
            logger.error(f"Error scraping Play Store: {e}")
            return {
                "success": False,
                "error": str(e),
                "fallback_data": self._get_fallback_data(input_data)
            }
    
    def _extract_package_from_url(self, url: str) -> str:
        """Extract package name from Play Store URL."""
        match = re.search(r'id=([^&]+)', url)
        return match.group(1) if match else ""
    
    def _extract_app_data(self, soup: BeautifulSoup, package_name: str) -> Dict[str, Any]:
        """Extract basic app metadata."""
        
        # Note: Play Store HTML structure changes frequently
        # This is a simplified extraction that would need regular updates
        
        app_data = {
            "package_name": package_name,
            "app_name": self._safe_extract(soup, 'h1[itemprop="name"]'),
            "developer": self._safe_extract(soup, 'a[href*="/store/apps/developer"]'),
            "category": self._safe_extract(soup, 'a[itemprop="genre"]'),
            "rating": self._extract_rating(soup),
            "total_reviews": self._extract_review_count(soup),
            "downloads": self._safe_extract(soup, 'div:contains("Downloads")'),
            "last_updated": self._safe_extract(soup, 'div:contains("Updated")'),
            "description": self._extract_description(soup),
            "whats_new": self._extract_whats_new(soup)
        }
        
        return app_data
    
    def _safe_extract(self, soup: BeautifulSoup, selector: str) -> str:
        """Safely extract text from selector."""
        try:
            element = soup.select_one(selector)
            return element.get_text(strip=True) if element else ""
        except:
            return ""
    
    def _extract_rating(self, soup: BeautifulSoup) -> float:
        """Extract app rating."""
        try:
            rating_elem = soup.select_one('div[aria-label*="Rated"]')
            if rating_elem:
                rating_text = rating_elem.get('aria-label', '')
                match = re.search(r'([\d.]+) stars', rating_text)
                if match:
                    return float(match.group(1))
        except:
            pass
        return 0.0
    
    def _extract_review_count(self, soup: BeautifulSoup) -> int:
        """Extract total review count."""
        try:
            review_elem = soup.select_one('span:contains("reviews")')
            if review_elem:
                text = review_elem.get_text()
                # Remove commas and extract number
                match = re.search(r'([\d,]+)', text)
                if match:
                    return int(match.group(1).replace(',', ''))
        except:
            pass
        return 0
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract app description."""
        try:
            desc_elem = soup.select_one('div[data-g-id="description"]')
            if desc_elem:
                return desc_elem.get_text(separator=' ', strip=True)
        except:
            pass
        return ""
    
    def _extract_whats_new(self, soup: BeautifulSoup) -> str:
        """Extract what's new section."""
        try:
            whats_new = soup.select_one('div:contains("What\'s New")')
            if whats_new and whats_new.find_next_sibling():
                return whats_new.find_next_sibling().get_text(strip=True)
        except:
            pass
        return ""
    
    def _extract_keywords(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract and analyze keywords from the listing."""
        
        # Get all text content
        title = self._safe_extract(soup, 'h1[itemprop="name"]')
        description = self._extract_description(soup)
        
        # Simple keyword extraction (in production, use NLP)
        all_text = f"{title} {description}".lower()
        words = re.findall(r'\b\w+\b', all_text)
        
        # Count word frequency
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Skip short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return {
            "title_keywords": re.findall(r'\b\w+\b', title.lower()),
            "top_keywords": [kw[0] for kw in top_keywords],
            "keyword_frequency": dict(top_keywords)
        }
    
    def _extract_visual_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract information about visual assets."""
        
        visual_info = {
            "icon_url": self._extract_icon_url(soup),
            "screenshots": self._extract_screenshots(soup),
            "feature_graphic": self._extract_feature_graphic(soup),
            "has_video": self._check_for_video(soup)
        }
        
        return visual_info
    
    def _extract_icon_url(self, soup: BeautifulSoup) -> str:
        """Extract app icon URL."""
        try:
            icon = soup.select_one('img[alt*="Icon"]')
            if icon:
                return icon.get('src', '')
        except:
            pass
        return ""
    
    def _extract_screenshots(self, soup: BeautifulSoup) -> List[str]:
        """Extract screenshot URLs."""
        screenshots = []
        try:
            screenshot_elems = soup.select('img[alt*="Screenshot"]')
            for elem in screenshot_elems[:8]:  # Limit to 8
                url = elem.get('src', '')
                if url:
                    screenshots.append(url)
        except:
            pass
        return screenshots
    
    def _extract_feature_graphic(self, soup: BeautifulSoup) -> str:
        """Extract feature graphic URL."""
        try:
            feature = soup.select_one('img[alt*="Feature"]')
            if feature:
                return feature.get('src', '')
        except:
            pass
        return ""
    
    def _check_for_video(self, soup: BeautifulSoup) -> bool:
        """Check if the listing has a promo video."""
        try:
            video = soup.select_one('button[aria-label*="Play"]')
            return video is not None
        except:
            return False
    
    def _extract_reviews(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract a sample of recent reviews."""
        reviews = []
        try:
            review_elems = soup.select('div[jscontroller][jsdata*="review"]')[:5]
            
            for elem in review_elems:
                review = {
                    "rating": self._extract_review_rating(elem),
                    "text": self._extract_review_text(elem),
                    "date": self._extract_review_date(elem)
                }
                if review["text"]:
                    reviews.append(review)
        except Exception as e:
            logger.error(f"Error extracting reviews: {e}")
        
        return reviews
    
    def _extract_review_rating(self, elem) -> int:
        """Extract rating from review element."""
        try:
            stars = elem.select('span[aria-label*="stars"]')
            if stars:
                label = stars[0].get('aria-label', '')
                match = re.search(r'(\d+) stars', label)
                if match:
                    return int(match.group(1))
        except:
            pass
        return 0
    
    def _extract_review_text(self, elem) -> str:
        """Extract review text."""
        try:
            text_elem = elem.select_one('span[jsname]')
            if text_elem:
                return text_elem.get_text(strip=True)
        except:
            pass
        return ""
    
    def _extract_review_date(self, elem) -> str:
        """Extract review date."""
        try:
            date_elem = elem.select_one('span:contains("20")')
            if date_elem:
                return date_elem.get_text(strip=True)
        except:
            pass
        return ""
    
    def _get_fallback_data(self, input_data: str) -> Dict[str, Any]:
        """Return fallback data for testing."""
        return {
            "package_name": input_data,
            "app_name": "Sample App",
            "developer": "Sample Developer",
            "category": "Productivity",
            "rating": 4.3,
            "total_reviews": 50000,
            "downloads": "1,000,000+",
            "description": "This is a sample app for testing Play Store analysis.",
            "keywords": ["productivity", "tasks", "organize", "planner"],
            "visual_assets": {
                "screenshots_count": 6,
                "has_video": False,
                "has_feature_graphic": True
            }
        }