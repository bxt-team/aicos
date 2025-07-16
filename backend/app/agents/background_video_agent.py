import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM
from app.services.klingai_client import KlingAIClient
from app.services.supabase_client import SupabaseClient
import logging

logger = logging.getLogger(__name__)


class BackgroundVideoAgent(BaseCrew):
    """Agent for generating short background videos for reels (5-10 seconds)"""
    
    def __init__(self, openai_api_key: str, klingai_api_key: str = None, klingai_provider: str = "piapi", supabase_client: SupabaseClient = None):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.klingai_api_key = klingai_api_key or os.getenv("KLINGAI_API_KEY")
        self.klingai_provider = klingai_provider or os.getenv("KLINGAI_PROVIDER", "piapi")
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize Supabase client
        self.supabase = supabase_client or SupabaseClient()
        
        # Initialize KlingAI client
        self.klingai_client = None
        if self.klingai_api_key:
            self.klingai_client = KlingAIClient(self.klingai_api_key, self.klingai_provider)
        
        # Output directory for generated videos
        self.output_dir = os.path.join(os.path.dirname(__file__), "../../static/background_videos")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create the video generation agent
        self.video_agent = self.create_agent("background_video_agent", llm=self.llm)
        
        # Simplified 7 Cycles period themes for background videos
        self.period_themes = {
            "Image": {
                "keywords": "golden light, sunburst, radiant glow",
                "mood": "inspiring"
            },
            "Veränderung": {
                "keywords": "flowing water, transformation, blue waves",
                "mood": "dynamic"
            },
            "Energie": {
                "keywords": "fire, lightning, red energy burst",
                "mood": "powerful"
            },
            "Kreativität": {
                "keywords": "paint splash, colorful abstract, yellow burst",
                "mood": "creative"
            },
            "Erfolg": {
                "keywords": "sparkling lights, celebration, magenta glow",
                "mood": "triumphant"
            },
            "Entspannung": {
                "keywords": "calm water, green nature, peaceful clouds",
                "mood": "relaxing"
            },
            "Umsicht": {
                "keywords": "purple mist, cosmic space, gentle stars",
                "mood": "contemplative"
            }
        }
    
    def _save_video_to_supabase(self, video_data: Dict[str, Any]) -> bool:
        """Save video data to Supabase"""
        try:
            if self.supabase.client:
                response = self.supabase.client.table('agent_background_videos').insert(video_data).execute()
                return True
            else:
                logger.warning("Supabase client not available, video not saved")
                return False
        except Exception as e:
            logger.error(f"Error saving video to Supabase: {e}")
            return False
    
    def _update_video_in_supabase(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update video data in Supabase"""
        try:
            if self.supabase.client:
                updates['updated_at'] = datetime.now().isoformat()
                response = self.supabase.client.table('agent_background_videos').update(updates).eq('task_id', task_id).execute()
                return True
            else:
                logger.warning("Supabase client not available, video not updated")
                return False
        except Exception as e:
            logger.error(f"Error updating video in Supabase: {e}")
            return False
    
    def _get_videos_from_supabase(self, period: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get videos from Supabase"""
        try:
            if self.supabase.client:
                query = self.supabase.client.table('agent_background_videos').select('*')
                if period:
                    query = query.eq('period', period)
                response = query.order('created_at', desc=True).execute()
                return response.data or []
            else:
                logger.warning("Supabase client not available")
                return []
        except Exception as e:
            logger.error(f"Error getting videos from Supabase: {e}")
            return []
    
    def generate_background_video(self, period: str, duration: int = 5, custom_prompt: Optional[str] = None, async_mode: bool = True) -> Dict[str, Any]:
        """Generate a short background video for a specific period"""
        print(f"[BackgroundVideoAgent] Starting video generation - Period: {period}, Duration: {duration}, Custom Prompt: {custom_prompt}")
        try:
            if not self.klingai_client:
                error_msg = "KlingAI client not initialized"
                print(f"[BackgroundVideoAgent] ERROR: {error_msg}")
                print(f"[BackgroundVideoAgent] KlingAI API Key present: {bool(self.klingai_api_key)}")
                return {
                    "success": False,
                    "error": error_msg,
                    "message": "KlingAI API key is required for video generation"
                }
            
            # Validate duration
            if duration not in [5, 10]:
                duration = 5  # Default to 5 seconds
            
            # Get period theme
            theme = self.period_themes.get(period, self.period_themes["Image"])
            
            # Create simple, focused prompt for background video
            if custom_prompt:
                prompt = f"{custom_prompt}. {duration} seconds, seamless loop, no text, no people"
            else:
                prompt = f"Abstract background video: {theme['keywords']}. {theme['mood']} mood. {duration} seconds, seamless loop, no text, no people, vertical format"
            
            # For now, use 5 seconds as it's more reliable across all models
            # You mentioned 5 seconds is fine
            actual_duration = 5 if duration == 10 else duration
            
            # Generate video with KlingAI
            print(f"[BackgroundVideoAgent] Generating video with prompt: {prompt}")
            print(f"[BackgroundVideoAgent] Calling KlingAI with duration={actual_duration}, aspect_ratio=9:16, model=kling, cfg_scale=0.5")
            
            try:
                
                video_result = self.klingai_client.generate_text_to_video(
                    prompt=prompt,
                    duration=actual_duration,
                    aspect_ratio="9:16",  # Vertical for reels
                    model="kling",  # Use simple model name as per API docs
                    cfg_scale=0.5  # Recommended by API docs for best results
                )
                print(f"[BackgroundVideoAgent] KlingAI response: {video_result}")
            except Exception as e:
                print(f"[BackgroundVideoAgent] ERROR calling KlingAI: {str(e)}")
                print(f"[BackgroundVideoAgent] Exception type: {type(e).__name__}")
                raise
            
            if not video_result.get("success", False):
                error_msg = video_result.get("error", "Unknown error")
                print(f"[BackgroundVideoAgent] Video generation failed: {error_msg}")
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to generate video: {error_msg}"
                }
            
            # Get task_id from the response
            task_id = video_result.get("task_id")
            if not task_id:
                print(f"[BackgroundVideoAgent] ERROR: No task_id in response")
                return {
                    "success": False,
                    "error": "No task_id returned",
                    "message": "Video generation started but no task ID was provided"
                }
            
            print(f"[BackgroundVideoAgent] Video generation started with task_id: {task_id}")
            
            # Generate output filename for future use
            video_hash = hashlib.md5(f"{period}_{prompt}_{datetime.now().isoformat()}".encode()).hexdigest()[:8]
            output_filename = f"{period.lower()}_background_{actual_duration}s_{video_hash}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Create initial task record
            task_info = {
                "task_id": task_id,
                "id": video_hash,
                "period": period,
                "duration": actual_duration,
                "prompt": prompt,
                "theme": theme,
                "file_path": output_path,
                "file_url": f"/static/background_videos/{output_filename}",
                "status": "processing",
                "provider": "klingai",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Store task info in Supabase
            task_data = {
                'task_id': task_id,
                'period': period,
                'duration': actual_duration,
                'prompt': prompt,
                'theme': theme,
                'file_path': output_path,
                'file_url': f"/static/background_videos/{output_filename}",
                'status': 'processing',
                'provider': 'klingai',
                'metadata': {
                    'custom_prompt': custom_prompt,
                    'additional_input': additionalInput if 'additionalInput' in locals() else None
                }
            }
            self._save_video_to_supabase(task_data)
            
            if async_mode:
                # Return immediately with task info
                print(f"[BackgroundVideoAgent] Returning task info for async processing")
                return {
                    "success": True,
                    "task": task_info,
                    "message": "Video generation started. Check status with task_id."
                }
            
            # Synchronous mode - wait for completion
            print(f"[BackgroundVideoAgent] Waiting for video to complete...")
            
            # Wait for the video to be generated (with longer timeout)
            completion_result = self.klingai_client.wait_for_completion(
                task_id=task_id,
                timeout=600,  # 10 minutes timeout
                poll_interval=5  # Check every 5 seconds
            )
            
            print(f"[BackgroundVideoAgent] Completion result: {completion_result}")
            
            if not completion_result.get("success", False):
                error_msg = completion_result.get("error", "Video generation failed")
                print(f"[BackgroundVideoAgent] Video generation failed after polling: {error_msg}")
                
                # Update task status in Supabase
                self._update_video_in_supabase(task_id, {
                    'status': 'failed',
                    'error': error_msg
                })
                
                return {
                    "success": False,
                    "error": error_msg,
                    "message": f"Failed to generate video: {error_msg}"
                }
            
            
            # Get video URL from completion result
            video_url = completion_result.get("video_url") or completion_result.get("output", {}).get("video", {}).get("url")
            print(f"[BackgroundVideoAgent] Video URL from KlingAI: {video_url}")
            if video_url:
                # For now, just store the URL (in production, you'd download and save locally)
                video_info = {
                    "id": video_hash,
                    "period": period,
                    "duration": actual_duration,
                    "prompt": prompt,
                    "theme": theme,
                    "file_path": output_path,
                    "file_url": f"/static/background_videos/{output_filename}",
                    "external_url": video_url,
                    "provider": "klingai",
                    "created_at": datetime.now().isoformat()
                }
                
                # Update video info in Supabase
                self._update_video_in_supabase(task_id, {
                    'status': 'completed',
                    'external_url': video_url,
                    'metadata': video_info
                })
                
                print(f"[BackgroundVideoAgent] Video generated successfully: {video_info['id']}")
                return {
                    "success": True,
                    "video": video_info,
                    "message": f"{actual_duration}s background video generated successfully"
                }
            else:
                print(f"[BackgroundVideoAgent] ERROR: No video URL in response")
                print(f"[BackgroundVideoAgent] Full response: {video_result}")
                return {
                    "success": False,
                    "error": "No video URL returned",
                    "message": "Video generation completed but no URL was provided"
                }
            
        except Exception as e:
            print(f"[BackgroundVideoAgent] EXCEPTION in generate_background_video: {str(e)}")
            print(f"[BackgroundVideoAgent] Exception type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "message": f"Error generating background video: {str(e)}"
            }
    
    def get_background_videos(self, period: Optional[str] = None) -> Dict[str, Any]:
        """Get all or period-specific background videos"""
        try:
            videos = self._get_videos_from_supabase(period)
            
            # Transform Supabase data to match expected format
            formatted_videos = []
            for video in videos:
                formatted_video = {
                    "id": video.get("id"),
                    "task_id": video.get("task_id"),
                    "period": video.get("period"),
                    "duration": video.get("duration"),
                    "prompt": video.get("prompt"),
                    "theme": video.get("theme", {}),
                    "file_path": video.get("file_path"),
                    "file_url": video.get("file_url"),
                    "external_url": video.get("external_url"),
                    "thumbnail_url": video.get("thumbnail_url"),
                    "status": video.get("status"),
                    "provider": video.get("provider"),
                    "created_at": video.get("created_at"),
                    "metadata": video.get("metadata", {})
                }
                formatted_videos.append(formatted_video)
            
            return {
                "success": True,
                "videos": formatted_videos,
                "count": len(formatted_videos)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error retrieving background videos"
            }
    
    def delete_background_video(self, video_id: str) -> Dict[str, Any]:
        """Delete a background video"""
        try:
            if self.supabase.client:
                # Delete from Supabase
                response = self.supabase.client.table('agent_background_videos').delete().eq('id', video_id).execute()
                
                if response.data:
                    # Delete physical file if exists
                    deleted_video = response.data[0] if response.data else None
                    if deleted_video and deleted_video.get("file_path") and os.path.exists(deleted_video["file_path"]):
                        try:
                            os.remove(deleted_video["file_path"])
                        except Exception as e:
                            logger.warning(f"Could not delete file: {e}")
                    
                    return {
                        "success": True,
                        "message": "Background video deleted successfully"
                    }
                else:
                    return {
                        "success": False,
                        "error": "Video not found",
                        "message": f"No video found with ID: {video_id}"
                    }
            else:
                return {
                    "success": False,
                    "error": "Supabase client not available",
                    "message": "Cannot delete video without database connection"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error deleting background video"
            }
    
    def check_video_task_status(self, task_id: str) -> Dict[str, Any]:
        """Check the status of a video generation task and update if complete"""
        try:
            # Get task info from Supabase
            if not self.supabase.client:
                return {
                    "success": False,
                    "error": "Supabase client not available",
                    "message": "Cannot check task status without database connection"
                }
            
            response = self.supabase.client.table('agent_background_videos').select('*').eq('task_id', task_id).execute()
            
            if not response.data:
                return {
                    "success": False,
                    "error": "Task not found",
                    "message": f"No task found with ID: {task_id}"
                }
            
            task_info = response.data[0]
            
            # If already completed or failed, return cached status
            if task_info["status"] in ["completed", "failed"]:
                return {
                    "success": True,
                    "task": task_info
                }
            
            # Check current status with KlingAI
            print(f"[BackgroundVideoAgent] Checking status for task: {task_id}")
            status_result = self.klingai_client.get_task_status(task_id)
            
            if not status_result.get("success"):
                return {
                    "success": False,
                    "error": status_result.get("error", "Failed to get status"),
                    "task": task_info
                }
            
            # Update task info based on status
            current_status = status_result.get("status", "").lower()
            
            if current_status in ["completed", "succeed", "success"]:
                # Get video URL
                video_url = status_result.get("video_url") or status_result.get("output", {}).get("video", {}).get("url")
                
                if video_url:
                    # Update in Supabase
                    self._update_video_in_supabase(task_id, {
                        'status': 'completed',
                        'external_url': video_url
                    })
                    task_info["status"] = "completed"
                    task_info["external_url"] = video_url
                else:
                    # Update in Supabase
                    self._update_video_in_supabase(task_id, {
                        'status': 'failed',
                        'error': 'No video URL returned'
                    })
                    task_info["status"] = "failed"
                    task_info["error"] = "No video URL returned"
            
            elif current_status in ["failed", "error"]:
                error_msg = status_result.get("message", "Video generation failed")
                # Update in Supabase
                self._update_video_in_supabase(task_id, {
                    'status': 'failed',
                    'error': error_msg
                })
                task_info["status"] = "failed"
                task_info["error"] = error_msg
            
            return {
                "success": True,
                "task": task_info
            }
            
        except Exception as e:
            print(f"[BackgroundVideoAgent] Error checking task status: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Error checking task status: {str(e)}"
            }
    
    def get_video_generation_status(self, video_id: str) -> Dict[str, Any]:
        """Check the status of a video generation job"""
        if not self.klingai_client:
            return {
                "success": False,
                "error": "KlingAI client not initialized"
            }
        
        try:
            status = self.klingai_client.get_video_status(video_id)
            return status
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error checking video status"
            }