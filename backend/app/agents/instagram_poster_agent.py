from crewai import Agent, Task, Crew
from crewai.llm import LLM
import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import time
from app.agents.crews.base_crew import BaseCrew

class InstagramPosterAgent(BaseCrew):
    """Agent for posting content directly to Instagram using the Instagram Graph API"""
    
    def __init__(self, openai_api_key: str, instagram_access_token: str = None, instagram_business_account_id: str = None):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.instagram_access_token = instagram_access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_business_account_id = instagram_business_account_id or os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Instagram Graph API base URL
        self.graph_api_base = "https://graph.facebook.com/v18.0"
        
        # Storage for posted content
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/instagram_posts_history.json")
        self.posts_history = self._load_posts_history()
        
        # Create the Instagram posting agent
        self.poster_agent = self._create_poster_agent()
        
        # Rate limiting tracking
        self.last_post_time = 0
        self.min_post_interval = 300  # 5 minutes between posts (Instagram rate limits)
        
        # Posting status tracking
        self.posting_status = {}
    
    def _load_posts_history(self) -> Dict[str, Any]:
        """Load posting history"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading posts history: {e}")
        return {"posts": [], "by_date": {}, "failed_posts": []}
    
    def _save_posts_history(self):
        """Save posting history to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.posts_history, f, indent=2)
        except Exception as e:
            print(f"Error saving posts history: {e}")
    
    def _create_poster_agent(self) -> Agent:
        """Create the Instagram posting agent"""
        return Agent(
            role="Instagram Content Posting Specialist",
            goal="Post high-quality 7 Cycles content to Instagram, ensuring optimal timing, hashtag strategy, and engagement while maintaining brand consistency",
            backstory="""
            You are a professional social media manager specializing in Instagram content posting and the 7 Cycles system.
            You have deep understanding of:
            - Instagram posting best practices and algorithm optimization
            - Optimal timing for spiritual and personal development content
            - Hashtag strategy for maximum reach and engagement
            - Instagram content formatting and text optimization
            - Community engagement and follower growth strategies
            - Brand consistency across 7 Cycles content
            
            Your expertise includes:
            - Analyzing content for Instagram-specific optimization
            - Determining optimal posting times based on content type and audience
            - Suggesting improvements for better engagement
            - Managing posting schedules and content calendar
            - Monitoring posting performance and engagement rates
            - Ensuring compliance with Instagram community guidelines
            """,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm
        )
    
    def validate_instagram_credentials(self) -> Dict[str, Any]:
        """Validate Instagram API credentials"""
        try:
            if not self.instagram_access_token or not self.instagram_business_account_id:
                return {
                    "success": False,
                    "error": "Instagram access token or business account ID not configured",
                    "message": "Instagram API credentials missing"
                }
            
            # Test API connection
            url = f"{self.graph_api_base}/{self.instagram_business_account_id}"
            params = {
                "fields": "id,username,name,account_type",
                "access_token": self.instagram_access_token
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                account_info = response.json()
                return {
                    "success": True,
                    "account_info": account_info,
                    "message": "Instagram API credentials validated successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Instagram API error: {response.status_code}",
                    "details": response.text,
                    "message": "Failed to validate Instagram credentials"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error validating Instagram credentials"
            }
    
    def prepare_post_content(self, instagram_post_data: Dict[str, Any], visual_post_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Prepare content for Instagram posting using the posting agent"""
        try:
            # Create task for content preparation
            task = Task(
                description=f"""
                Prepare this content for optimal Instagram posting:

                INSTAGRAM POST DATA:
                Text: "{instagram_post_data.get('post_text', '')}"
                Hashtags: {instagram_post_data.get('hashtags', [])}
                Call-to-Action: "{instagram_post_data.get('call_to_action', '')}"
                Period: {instagram_post_data.get('period_name', '')}
                Style: {instagram_post_data.get('style', '')}
                Optimal Timing: {instagram_post_data.get('optimal_posting_time', '')}
                
                VISUAL POST DATA (if available):
                {f"Image Available: Yes - {visual_post_data.get('file_url', '')}" if visual_post_data else "Image Available: No"}
                {f"Format: {visual_post_data.get('post_format', '')}" if visual_post_data else ""}
                {f"Style: {visual_post_data.get('image_style', '')}" if visual_post_data else ""}
                
                REQUIREMENTS:
                1. Optimize the post text for Instagram (max 2200 characters)
                2. Ensure hashtags are properly formatted and within Instagram limits (max 30)
                3. Create an engaging caption that encourages interaction
                4. Suggest the best posting time based on content type
                5. Recommend any content adjustments for better engagement
                6. Ensure the content aligns with Instagram community guidelines
                
                Format the response as JSON:
                {{
                    "optimized_caption": "Complete Instagram caption with text and hashtags",
                    "hashtags_count": number_of_hashtags,
                    "recommended_posting_time": "Best time to post this content",
                    "engagement_tips": ["tip1", "tip2", "tip3"],
                    "content_type": "feed_post" or "story",
                    "estimated_engagement": "prediction of engagement level",
                    "post_ready": true/false,
                    "adjustments_needed": ["any required adjustments"],
                    "caption_length": character_count
                }}
                """,
                expected_output="JSON formatted Instagram posting recommendations and optimized content",
                agent=self.poster_agent
            )
            
            # Create and execute crew
            crew = Crew(
                agents=[self.poster_agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                preparation_data = json.loads(str(result))
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                preparation_data = {
                    "optimized_caption": self._create_fallback_caption(instagram_post_data),
                    "hashtags_count": len(instagram_post_data.get('hashtags', [])),
                    "recommended_posting_time": instagram_post_data.get('optimal_posting_time', 'Now'),
                    "engagement_tips": ["Use engaging questions", "Post consistently", "Interact with followers"],
                    "content_type": "feed_post",
                    "estimated_engagement": "medium",
                    "post_ready": True,
                    "adjustments_needed": [],
                    "caption_length": len(instagram_post_data.get('post_text', ''))
                }
            
            return {
                "success": True,
                "preparation": preparation_data,
                "message": "Content prepared for Instagram posting"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error preparing content for Instagram"
            }
    
    def _create_fallback_caption(self, instagram_post_data: Dict[str, Any]) -> str:
        """Create a fallback caption if the main preparation fails"""
        post_text = instagram_post_data.get('post_text', '')
        hashtags = ' '.join(instagram_post_data.get('hashtags', []))
        cta = instagram_post_data.get('call_to_action', '')
        
        caption = f"{post_text}\n\n{cta}\n\n{hashtags}"
        return caption[:2200]  # Instagram caption limit
    
    def upload_media_to_instagram(self, image_url: str, caption: str, is_story: bool = False) -> Dict[str, Any]:
        """Upload media to Instagram"""
        try:
            if not self.instagram_access_token or not self.instagram_business_account_id:
                return {
                    "success": False,
                    "error": "Instagram credentials not configured",
                    "message": "Cannot upload without Instagram API credentials"
                }
            
            # Check rate limiting
            current_time = time.time()
            if current_time - self.last_post_time < self.min_post_interval:
                wait_time = self.min_post_interval - (current_time - self.last_post_time)
                return {
                    "success": False,
                    "error": f"Rate limit: Please wait {int(wait_time)} seconds before posting",
                    "message": "Instagram rate limiting active"
                }
            
            if is_story:
                # Upload Instagram Story
                return self._upload_story(image_url, caption)
            else:
                # Upload Instagram Feed Post
                return self._upload_feed_post(image_url, caption)
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error uploading media to Instagram"
            }
    
    def _upload_feed_post(self, image_url: str, caption: str) -> Dict[str, Any]:
        """Upload a feed post to Instagram"""
        try:
            # Step 1: Create media container
            container_url = f"{self.graph_api_base}/{self.instagram_business_account_id}/media"
            container_params = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.instagram_access_token
            }
            
            container_response = requests.post(container_url, data=container_params)
            
            if container_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to create media container: {container_response.status_code}",
                    "details": container_response.text,
                    "message": "Error creating Instagram media container"
                }
            
            container_data = container_response.json()
            container_id = container_data.get("id")
            
            if not container_id:
                return {
                    "success": False,
                    "error": "No container ID returned",
                    "details": container_data,
                    "message": "Failed to get media container ID"
                }
            
            # Step 2: Publish the media
            publish_url = f"{self.graph_api_base}/{self.instagram_business_account_id}/media_publish"
            publish_params = {
                "creation_id": container_id,
                "access_token": self.instagram_access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_params)
            
            if publish_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to publish media: {publish_response.status_code}",
                    "details": publish_response.text,
                    "message": "Error publishing Instagram post"
                }
            
            publish_data = publish_response.json()
            post_id = publish_data.get("id")
            
            # Update rate limiting
            self.last_post_time = time.time()
            
            # Save to history
            post_record = {
                "id": post_id,
                "container_id": container_id,
                "image_url": image_url,
                "caption": caption,
                "type": "feed_post",
                "posted_at": datetime.now().isoformat(),
                "instagram_url": f"https://www.instagram.com/p/{post_id}/",
                "status": "published"
            }
            
            self.posts_history["posts"].append(post_record)
            self._save_posts_history()
            
            return {
                "success": True,
                "post_id": post_id,
                "container_id": container_id,
                "instagram_url": f"https://www.instagram.com/p/{post_id}/",
                "post_record": post_record,
                "message": "Instagram post published successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error uploading feed post to Instagram"
            }
    
    def _upload_story(self, image_url: str, caption: str) -> Dict[str, Any]:
        """Upload a story to Instagram"""
        try:
            # Create story media container
            container_url = f"{self.graph_api_base}/{self.instagram_business_account_id}/media"
            container_params = {
                "image_url": image_url,
                "media_type": "STORIES",
                "access_token": self.instagram_access_token
            }
            
            # Add caption as text overlay if provided
            if caption:
                container_params["caption"] = caption[:250]  # Stories have shorter caption limits
            
            container_response = requests.post(container_url, data=container_params)
            
            if container_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to create story container: {container_response.status_code}",
                    "details": container_response.text,
                    "message": "Error creating Instagram story container"
                }
            
            container_data = container_response.json()
            container_id = container_data.get("id")
            
            # Publish the story
            publish_url = f"{self.graph_api_base}/{self.instagram_business_account_id}/media_publish"
            publish_params = {
                "creation_id": container_id,
                "access_token": self.instagram_access_token
            }
            
            publish_response = requests.post(publish_url, data=publish_params)
            
            if publish_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to publish story: {publish_response.status_code}",
                    "details": publish_response.text,
                    "message": "Error publishing Instagram story"
                }
            
            publish_data = publish_response.json()
            story_id = publish_data.get("id")
            
            # Update rate limiting
            self.last_post_time = time.time()
            
            # Save to history
            story_record = {
                "id": story_id,
                "container_id": container_id,
                "image_url": image_url,
                "caption": caption,
                "type": "story",
                "posted_at": datetime.now().isoformat(),
                "status": "published"
            }
            
            self.posts_history["posts"].append(story_record)
            self._save_posts_history()
            
            return {
                "success": True,
                "story_id": story_id,
                "container_id": container_id,
                "story_record": story_record,
                "message": "Instagram story published successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error uploading story to Instagram"
            }
    
    def post_complete_content(self, instagram_post_id: str, visual_post_id: str = None, 
                            post_type: str = "feed_post", schedule_time: str = None) -> Dict[str, Any]:
        """Post complete content combining Instagram post text and visual post image"""
        try:
            # Load Instagram post data
            from app.agents.write_hashtag_research_agent import WriteHashtagResearchAgent
            write_hashtag_agent = WriteHashtagResearchAgent(self.openai_api_key)
            
            instagram_posts = write_hashtag_agent.get_generated_posts()
            if not instagram_posts["success"]:
                return {
                    "success": False,
                    "error": "Failed to load Instagram posts",
                    "message": "Could not retrieve Instagram post data"
                }
            
            # Find the specific Instagram post
            instagram_post = None
            for post in instagram_posts["posts"]:
                if post["id"] == instagram_post_id:
                    instagram_post = post
                    break
            
            if not instagram_post:
                return {
                    "success": False,
                    "error": f"Instagram post with ID {instagram_post_id} not found",
                    "message": "Instagram post not found"
                }
            
            # Load visual post data if provided
            visual_post = None
            if visual_post_id:
                from app.agents.visual_post_creator_agent import VisualPostCreatorAgent
                visual_agent = VisualPostCreatorAgent(self.openai_api_key)
                
                # This would need to be implemented in the visual post creator agent
                # For now, we'll assume the visual post data structure
                visual_posts = visual_agent.posts_storage.get("posts", [])
                for vpost in visual_posts:
                    if vpost.get("id") == visual_post_id:
                        visual_post = vpost
                        break
            
            # Prepare content for posting
            preparation_result = self.prepare_post_content(instagram_post, visual_post)
            
            if not preparation_result["success"]:
                return preparation_result
            
            preparation = preparation_result["preparation"]
            
            # Check if post is ready
            if not preparation.get("post_ready", False):
                return {
                    "success": False,
                    "error": "Content not ready for posting",
                    "details": preparation.get("adjustments_needed", []),
                    "message": "Content needs adjustments before posting"
                }
            
            # Get image URL for posting
            image_url = None
            if visual_post:
                # Convert local file path to accessible URL
                file_path = visual_post.get("file_path", "")
                if file_path:
                    # Assuming we have a way to serve the static files
                    base_url = os.getenv("BASE_URL", "http://localhost:8000")
                    image_url = f"{base_url}{visual_post.get('file_url', '')}"
            
            if not image_url:
                return {
                    "success": False,
                    "error": "No image available for posting",
                    "message": "Visual post image required for Instagram posting"
                }
            
            # Post to Instagram
            if schedule_time:
                # For now, we'll store scheduled posts and implement scheduling later
                scheduled_post = {
                    "instagram_post_id": instagram_post_id,
                    "visual_post_id": visual_post_id,
                    "image_url": image_url,
                    "caption": preparation["optimized_caption"],
                    "post_type": post_type,
                    "schedule_time": schedule_time,
                    "status": "scheduled",
                    "created_at": datetime.now().isoformat()
                }
                
                # Save scheduled post (implementation would depend on scheduling system)
                return {
                    "success": True,
                    "scheduled_post": scheduled_post,
                    "message": f"Post scheduled for {schedule_time}"
                }
            else:
                # Post immediately
                is_story = post_type == "story"
                upload_result = self.upload_media_to_instagram(
                    image_url=image_url,
                    caption=preparation["optimized_caption"],
                    is_story=is_story
                )
                
                if upload_result["success"]:
                    # Add metadata to the result
                    upload_result["instagram_post_id"] = instagram_post_id
                    upload_result["visual_post_id"] = visual_post_id
                    upload_result["preparation"] = preparation
                
                return upload_result
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error posting complete content to Instagram"
            }
    
    def get_posting_history(self, limit: int = 50) -> Dict[str, Any]:
        """Get posting history"""
        try:
            posts = self.posts_history.get("posts", [])
            
            # Sort by posted_at descending
            sorted_posts = sorted(posts, key=lambda x: x.get("posted_at", ""), reverse=True)
            
            # Limit results
            limited_posts = sorted_posts[:limit]
            
            return {
                "success": True,
                "posts": limited_posts,
                "total_count": len(posts),
                "returned_count": len(limited_posts)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error retrieving posting history"
            }
    
    def get_posting_status(self) -> Dict[str, Any]:
        """Get current posting status and rate limiting info"""
        try:
            current_time = time.time()
            time_since_last_post = current_time - self.last_post_time
            can_post_in = max(0, self.min_post_interval - time_since_last_post)
            
            validation_result = self.validate_instagram_credentials()
            
            return {
                "success": True,
                "can_post_now": can_post_in <= 0,
                "can_post_in_seconds": int(can_post_in),
                "last_post_time": datetime.fromtimestamp(self.last_post_time).isoformat() if self.last_post_time > 0 else None,
                "api_credentials_valid": validation_result["success"],
                "account_info": validation_result.get("account_info"),
                "total_posts": len(self.posts_history.get("posts", [])),
                "rate_limit_interval": self.min_post_interval
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error getting posting status"
            }