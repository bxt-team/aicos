"""Real Threads profile scraper using web scraping."""

import asyncio
import json
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from urllib.parse import quote
import warnings

# Suppress SSL warnings for development
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

logger = logging.getLogger(__name__)

# Import mock data as fallback
from .threads_mock_data import get_mock_profile_data


class ThreadsScraper:
    """Scraper for Threads.net profiles using web scraping."""
    
    def __init__(self):
        self.base_url = "https://www.threads.net"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def scrape_profile_sync(self, username: str) -> Dict[str, Any]:
        """Scrape a Threads profile for posts and engagement data (synchronous version)."""
        try:
            # Clean username (remove @ if present)
            username = username.lstrip('@')
            
            # Try to fetch the profile page
            profile_url = f"{self.base_url}/@{username}"
            
            # For now, use mock data with a clear indication
            # TODO: Implement real scraping when Threads API or better scraping method is available
            logger.warning(f"Using mock data for {username}. Real Threads scraping requires JavaScript rendering.")
            
            # Get mock data
            mock_data = get_mock_profile_data(username)
            
            # Add a note that this is mock data
            mock_data["data_source"] = "mock"
            mock_data["note"] = "This is mock data. Real Threads scraping requires JavaScript rendering or API access."
            
            return mock_data
            
            # Original scraping code kept for reference when we can implement real scraping
            # response = requests.get(profile_url, headers=self.headers, verify=False)
            # 
            # if response.status_code != 200:
            #     logger.error(f"Failed to fetch profile: {response.status_code}")
            #     return self._get_empty_profile(username)
            # 
            # html = response.text
            # soup = BeautifulSoup(html, 'html.parser')
            # profile_data = self._extract_profile_data(soup, username)
            # posts_data = self._extract_posts_data(soup)
            # analysis = self._analyze_posts(posts_data)
            # 
            # return {
            #     **profile_data,
            #     **analysis,
            #     "posts_analyzed": len(posts_data),
            #     "raw_posts": posts_data[:10]
            # }
                    
        except Exception as e:
            logger.error(f"Error getting Threads profile {username}: {str(e)}")
            return self._get_empty_profile(username)
    
    async def scrape_profile(self, username: str) -> Dict[str, Any]:
        """Scrape a Threads profile for posts and engagement data (async wrapper)."""
        # Run the sync version in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.scrape_profile_sync, username)
    
    def _extract_profile_data(self, soup: BeautifulSoup, username: str) -> Dict[str, Any]:
        """Extract basic profile information."""
        try:
            # Try to find profile metadata in scripts
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'ProfilePage':
                        return self._parse_profile_metadata(data, username)
                except:
                    continue
            
            # Fallback to manual extraction
            profile_data = {
                "handle": username,
                "display_name": username,
                "bio": "",
                "verified": False,
                "followers": 0,
                "following": 0,
                "posts_count": 0
            }
            
            # Try to extract from meta tags
            meta_desc = soup.find('meta', {'property': 'og:description'})
            if meta_desc and meta_desc.get('content'):
                # Parse description like "123 Followers, 45 Following, 67 Posts"
                desc = meta_desc['content']
                numbers = re.findall(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)', desc)
                if len(numbers) >= 3:
                    profile_data['followers'] = self._parse_number(numbers[0])
                    profile_data['following'] = self._parse_number(numbers[1])
                    profile_data['posts_count'] = self._parse_number(numbers[2])
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            return {
                "handle": username,
                "error": "Could not extract profile data"
            }
    
    def _extract_posts_data(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract posts from the profile page."""
        posts = []
        
        try:
            # Look for post containers (these selectors may need adjustment)
            post_elements = soup.find_all('article') or soup.find_all('div', {'role': 'article'})
            
            for post in post_elements[:20]:  # Analyze up to 20 recent posts
                post_data = self._extract_single_post(post)
                if post_data:
                    posts.append(post_data)
            
            # If no posts found with articles, try alternative methods
            if not posts:
                # Try to find posts in script tags
                scripts = soup.find_all('script')
                for script in scripts:
                    if script.string and 'thread' in script.string.lower():
                        # Extract post data from JavaScript
                        posts.extend(self._extract_posts_from_script(script.string))
            
        except Exception as e:
            logger.error(f"Error extracting posts: {e}")
        
        return posts
    
    def _extract_single_post(self, post_element) -> Optional[Dict[str, Any]]:
        """Extract data from a single post element."""
        try:
            post_data = {
                "text": "",
                "likes": 0,
                "comments": 0,
                "reposts": 0,
                "hashtags": [],
                "mentions": [],
                "has_media": False,
                "post_type": "text"
            }
            
            # Extract post text
            text_elements = post_element.find_all(['span', 'div'], recursive=True)
            for elem in text_elements:
                if elem.string:
                    post_data["text"] += elem.string + " "
            
            post_data["text"] = post_data["text"].strip()
            
            # Extract hashtags from text
            hashtags = re.findall(r'#\w+', post_data["text"])
            post_data["hashtags"] = list(set(hashtags))
            
            # Extract mentions
            mentions = re.findall(r'@\w+', post_data["text"])
            post_data["mentions"] = list(set(mentions))
            
            # Check for media
            if post_element.find('img') or post_element.find('video'):
                post_data["has_media"] = True
                post_data["post_type"] = "media"
            
            # Try to extract engagement metrics
            # Look for like/comment/repost counts
            for elem in post_element.find_all(['span', 'div']):
                text = elem.get_text().strip()
                if 'like' in text.lower():
                    num = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)', text)
                    if num:
                        post_data["likes"] = self._parse_number(num.group(1))
                elif 'comment' in text.lower() or 'reply' in text.lower():
                    num = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)', text)
                    if num:
                        post_data["comments"] = self._parse_number(num.group(1))
                elif 'repost' in text.lower() or 'share' in text.lower():
                    num = re.search(r'(\d+(?:,\d+)*(?:\.\d+)?[KMB]?)', text)
                    if num:
                        post_data["reposts"] = self._parse_number(num.group(1))
            
            return post_data if post_data["text"] else None
            
        except Exception as e:
            logger.error(f"Error extracting single post: {e}")
            return None
    
    def _analyze_posts(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze posts to extract patterns and insights."""
        if not posts:
            return {
                "content_analysis": {
                    "error": "No posts found to analyze"
                }
            }
        
        # Collect all hashtags
        all_hashtags = []
        all_mentions = []
        total_likes = 0
        total_comments = 0
        total_reposts = 0
        post_types = {"text": 0, "media": 0}
        post_lengths = []
        
        for post in posts:
            all_hashtags.extend(post.get("hashtags", []))
            all_mentions.extend(post.get("mentions", []))
            total_likes += post.get("likes", 0)
            total_comments += post.get("comments", 0)
            total_reposts += post.get("reposts", 0)
            post_types[post.get("post_type", "text")] += 1
            post_lengths.append(len(post.get("text", "")))
        
        # Calculate averages
        avg_likes = total_likes / len(posts) if posts else 0
        avg_comments = total_comments / len(posts) if posts else 0
        avg_reposts = total_reposts / len(posts) if posts else 0
        avg_post_length = sum(post_lengths) / len(post_lengths) if post_lengths else 0
        
        # Get unique hashtags and their frequency
        hashtag_freq = {}
        for tag in all_hashtags:
            hashtag_freq[tag] = hashtag_freq.get(tag, 0) + 1
        
        # Sort hashtags by frequency
        top_hashtags = sorted(hashtag_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Analyze content themes based on text
        themes = self._analyze_themes(posts)
        
        return {
            "engagement_metrics": {
                "avg_likes": round(avg_likes, 2),
                "avg_comments": round(avg_comments, 2),
                "avg_reposts": round(avg_reposts, 2),
                "total_engagement": round(avg_likes + avg_comments + avg_reposts, 2)
            },
            "content_patterns": {
                "avg_post_length": round(avg_post_length),
                "post_types": post_types,
                "uses_hashtags": len(all_hashtags) > 0,
                "hashtag_count": len(set(all_hashtags)),
                "top_hashtags": [tag[0] for tag in top_hashtags],
                "hashtag_frequency": dict(top_hashtags),
                "mentions_others": len(all_mentions) > 0,
                "unique_mentions": len(set(all_mentions))
            },
            "content_themes": themes,
            "posting_behavior": {
                "total_posts_analyzed": len(posts),
                "has_consistent_style": self._check_style_consistency(posts)
            }
        }
    
    def _analyze_themes(self, posts: List[Dict[str, Any]]) -> List[str]:
        """Analyze common themes in posts."""
        themes = []
        
        # Keywords for different themes
        theme_keywords = {
            "Affirmations": ["affirm", "positive", "belief", "manifest", "intention"],
            "Spirituality": ["spiritual", "soul", "universe", "energy", "divine"],
            "Self-care": ["self-care", "wellness", "healing", "nurture", "care"],
            "Motivation": ["motivat", "inspire", "empower", "courage", "strength"],
            "Mindfulness": ["mindful", "present", "aware", "conscious", "meditat"],
            "Personal Growth": ["growth", "transform", "evolve", "develop", "journey"],
            "Community": ["community", "together", "support", "share", "connect"],
            "Gratitude": ["grateful", "gratitude", "thankful", "appreciate", "bless"]
        }
        
        # Count theme occurrences
        theme_counts = {}
        for post in posts:
            text = post.get("text", "").lower()
            for theme, keywords in theme_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        theme_counts[theme] = theme_counts.get(theme, 0) + 1
                        break
        
        # Get top themes
        sorted_themes = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
        themes = [theme[0] for theme in sorted_themes[:5]]
        
        return themes
    
    def _check_style_consistency(self, posts: List[Dict[str, Any]]) -> bool:
        """Check if posting style is consistent."""
        if len(posts) < 3:
            return False
        
        # Check for consistent hashtag usage
        hashtag_usage = [len(post.get("hashtags", [])) > 0 for post in posts]
        hashtag_consistency = hashtag_usage.count(True) / len(hashtag_usage) if hashtag_usage else 0
        
        # Check for consistent post length
        lengths = [len(post.get("text", "")) for post in posts]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            length_variance = sum((l - avg_length) ** 2 for l in lengths) / len(lengths)
            length_consistency = length_variance < (avg_length * 0.5) ** 2
        else:
            length_consistency = False
        
        return hashtag_consistency > 0.7 or length_consistency
    
    def _parse_number(self, num_str: str) -> int:
        """Parse number strings like '1.2K' or '1,234' to integers."""
        try:
            # Remove commas
            num_str = num_str.replace(',', '')
            
            # Handle K, M, B suffixes
            if num_str.endswith('K'):
                return int(float(num_str[:-1]) * 1000)
            elif num_str.endswith('M'):
                return int(float(num_str[:-1]) * 1000000)
            elif num_str.endswith('B'):
                return int(float(num_str[:-1]) * 1000000000)
            else:
                return int(float(num_str))
        except:
            return 0
    
    def _parse_profile_metadata(self, data: Dict[str, Any], username: str) -> Dict[str, Any]:
        """Parse profile metadata from structured data."""
        try:
            author = data.get('author', {})
            interaction_stats = author.get('interactionStatistic', [])
            
            stats = {
                "followers": 0,
                "following": 0,
                "posts_count": 0
            }
            
            for stat in interaction_stats:
                if stat.get('@type') == 'InteractionCounter':
                    interaction_type = stat.get('interactionType', '')
                    value = stat.get('userInteractionCount', 0)
                    
                    if 'Follow' in interaction_type:
                        stats['followers'] = value
                    elif 'Friend' in interaction_type:
                        stats['following'] = value
            
            return {
                "handle": username,
                "display_name": author.get('name', username),
                "bio": author.get('description', ''),
                "verified": author.get('verified', False),
                **stats
            }
        except:
            return {"handle": username}
    
    def _extract_posts_from_script(self, script_content: str) -> List[Dict[str, Any]]:
        """Extract posts from JavaScript content."""
        posts = []
        try:
            # Look for JSON-like structures in the script
            # This is a simplified approach - real implementation would need more sophisticated parsing
            json_matches = re.findall(r'\{[^{}]*"text"[^{}]*\}', script_content)
            
            for match in json_matches:
                try:
                    post_data = json.loads(match)
                    if 'text' in post_data:
                        posts.append({
                            "text": post_data.get('text', ''),
                            "likes": post_data.get('likes', 0),
                            "comments": post_data.get('comments', 0),
                            "reposts": post_data.get('reposts', 0),
                            "hashtags": re.findall(r'#\w+', post_data.get('text', '')),
                            "mentions": re.findall(r'@\w+', post_data.get('text', '')),
                            "has_media": bool(post_data.get('media')),
                            "post_type": "media" if post_data.get('media') else "text"
                        })
                except:
                    continue
        except Exception as e:
            logger.error(f"Error extracting posts from script: {e}")
        
        return posts
    
    def _get_empty_profile(self, username: str) -> Dict[str, Any]:
        """Return empty profile structure when scraping fails."""
        return {
            "handle": username,
            "error": "Could not fetch profile data",
            "followers": 0,
            "following": 0,
            "posts_count": 0,
            "engagement_metrics": {
                "avg_likes": 0,
                "avg_comments": 0,
                "avg_reposts": 0
            },
            "content_patterns": {
                "uses_hashtags": False,
                "top_hashtags": [],
                "content_themes": []
            }
        }


# Synchronous wrapper for use in CrewAI tools
def scrape_threads_profile(username: str) -> Dict[str, Any]:
    """Synchronous wrapper for the scraper."""
    scraper = ThreadsScraper()
    return scraper.scrape_profile_sync(username)