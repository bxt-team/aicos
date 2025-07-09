import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM

# Import all the agents we'll be using
from app.agents.affirmations_agent import AffirmationsAgent
from app.agents.visual_post_creator_agent import VisualPostCreatorAgent
from app.agents.post_composition_agent import PostCompositionAgent
from app.agents.video_generation_agent import VideoGenerationAgent
from app.agents.write_hashtag_research_agent import WriteHashtagResearchAgent
from app.agents.instagram_poster_agent import InstagramPosterAgent

class ContentWorkflowAgent(BaseCrew):
    """Agent for orchestrating the complete content workflow from affirmation to scheduled posts and reels"""
    
    def __init__(self, openai_api_key: str, pexels_api_key: str = None, instagram_access_token: str = None):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.pexels_api_key = pexels_api_key
        self.instagram_access_token = instagram_access_token
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize all agents
        self.affirmations_agent = AffirmationsAgent(openai_api_key)
        self.visual_post_creator = VisualPostCreatorAgent(openai_api_key, pexels_api_key)
        self.post_composition_agent = PostCompositionAgent(openai_api_key)
        self.video_generation_agent = VideoGenerationAgent(openai_api_key)
        self.hashtag_research_agent = WriteHashtagResearchAgent(openai_api_key)
        
        # Initialize Instagram poster if token is provided
        self.instagram_poster = None
        if instagram_access_token:
            self.instagram_poster = InstagramPosterAgent(openai_api_key, instagram_access_token)
        
        # Storage for workflows
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/workflows_storage.json")
        self.workflows_storage = self._load_workflows_storage()
        
        # Create the workflow orchestration agent
        self.workflow_agent = self.create_agent("content_workflow_agent", llm=self.llm)
        
    def _load_workflows_storage(self) -> Dict[str, Any]:
        """Load previously created workflows"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading workflows storage: {e}")
        return {"workflows": [], "by_hash": {}}
    
    def _save_workflows_storage(self):
        """Save workflows to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.workflows_storage, f, indent=2)
        except Exception as e:
            print(f"Error saving workflows storage: {e}")
    
    def _generate_workflow_hash(self, period: str, workflow_type: str, options: Dict[str, Any]) -> str:
        """Generate a hash for the workflow parameters"""
        workflow_key = f"{period}_{workflow_type}_{json.dumps(options, sort_keys=True)}"
        return hashlib.md5(workflow_key.encode()).hexdigest()
    
    def create_complete_content_workflow(self, period: str, workflow_type: str = "full", 
                                       options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a complete content workflow from affirmation to scheduled posts and reels"""
        try:
            workflow_options = options or {}
            workflow_hash = self._generate_workflow_hash(period, workflow_type, workflow_options)
            
            # Initialize workflow tracking
            workflow_result = {
                "id": workflow_hash,
                "period": period,
                "workflow_type": workflow_type,
                "options": workflow_options,
                "started_at": datetime.now().isoformat(),
                "steps": [],
                "status": "in_progress",
                "results": {}
            }
            
            # Step 1: Generate Affirmations
            step_result = self._execute_affirmation_step(period, workflow_options)
            workflow_result["steps"].append(step_result)
            
            if not step_result["success"]:
                workflow_result["status"] = "failed"
                workflow_result["error"] = "Failed at affirmation generation step"
                return workflow_result
            
            workflow_result["results"]["affirmations"] = step_result["data"]
            
            # Step 2: Find Background Images
            step_result = self._execute_image_finding_step(period, workflow_options)
            workflow_result["steps"].append(step_result)
            
            if not step_result["success"]:
                workflow_result["status"] = "failed"
                workflow_result["error"] = "Failed at image finding step"
                return workflow_result
            
            workflow_result["results"]["background_images"] = step_result["data"]
            
            # Step 3: Create Visual Posts
            step_result = self._execute_post_composition_step(period, workflow_result["results"], workflow_options)
            workflow_result["steps"].append(step_result)
            
            if not step_result["success"]:
                workflow_result["status"] = "failed"
                workflow_result["error"] = "Failed at post composition step"
                return workflow_result
            
            workflow_result["results"]["visual_posts"] = step_result["data"]
            
            # Step 4: Create Instagram Reels (if requested)
            if workflow_options.get("create_reels", True):
                step_result = self._execute_video_generation_step(period, workflow_result["results"], workflow_options)
                workflow_result["steps"].append(step_result)
                
                if not step_result["success"]:
                    workflow_result["status"] = "failed"
                    workflow_result["error"] = "Failed at video generation step"
                    return workflow_result
                
                workflow_result["results"]["reels"] = step_result["data"]
            
            # Step 5: Generate Hashtags and Captions
            step_result = self._execute_hashtag_research_step(period, workflow_result["results"], workflow_options)
            workflow_result["steps"].append(step_result)
            
            if not step_result["success"]:
                workflow_result["status"] = "failed"
                workflow_result["error"] = "Failed at hashtag research step"
                return workflow_result
            
            workflow_result["results"]["social_content"] = step_result["data"]
            
            # Step 6: Schedule Posts (if Instagram token is available)
            if self.instagram_poster and workflow_options.get("schedule_posts", False):
                step_result = self._execute_scheduling_step(period, workflow_result["results"], workflow_options)
                workflow_result["steps"].append(step_result)
                
                if not step_result["success"]:
                    workflow_result["status"] = "failed"
                    workflow_result["error"] = "Failed at scheduling step"
                    return workflow_result
                
                workflow_result["results"]["scheduled_posts"] = step_result["data"]
            
            # Complete workflow
            workflow_result["status"] = "completed"
            workflow_result["completed_at"] = datetime.now().isoformat()
            workflow_result["success"] = True
            
            # Save workflow
            self.workflows_storage["workflows"].append(workflow_result)
            self.workflows_storage["by_hash"][workflow_hash] = workflow_result
            self._save_workflows_storage()
            
            return workflow_result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Content-Workflows"
            }
    
    def _execute_affirmation_step(self, period: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute affirmation generation step"""
        try:
            print(f"Step 1: Generating affirmations for period {period}")
            
            # Generate affirmations for the period
            affirmation_count = options.get("affirmation_count", 5)
            affirmation_result = self.affirmations_agent.generate_affirmations(
                period=period,
                count=affirmation_count
            )
            
            if not affirmation_result["success"]:
                return {
                    "step": "affirmation_generation",
                    "success": False,
                    "error": affirmation_result["error"],
                    "message": "Fehler beim Generieren der Affirmationen"
                }
            
            return {
                "step": "affirmation_generation",
                "success": True,
                "data": affirmation_result["affirmations"],
                "message": f"{len(affirmation_result['affirmations'])} Affirmationen generiert"
            }
            
        except Exception as e:
            return {
                "step": "affirmation_generation",
                "success": False,
                "error": str(e),
                "message": "Fehler beim Generieren der Affirmationen"
            }
    
    def _execute_image_finding_step(self, period: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute image finding step"""
        try:
            print(f"Step 2: Finding background images for period {period}")
            
            # Generate search tags based on period
            search_tags = self._generate_search_tags(period)
            image_count = options.get("image_count", 3)
            
            # Find background images
            image_result = self.visual_post_creator.find_background_image(
                tags=search_tags,
                period=period,
                count=image_count
            )
            
            if not image_result["success"]:
                return {
                    "step": "image_finding",
                    "success": False,
                    "error": image_result["error"],
                    "message": "Fehler beim Finden der Hintergrundbilder"
                }
            
            return {
                "step": "image_finding",
                "success": True,
                "data": image_result["images"],
                "message": f"{len(image_result['images'])} Hintergrundbilder gefunden"
            }
            
        except Exception as e:
            return {
                "step": "image_finding",
                "success": False,
                "error": str(e),
                "message": "Fehler beim Finden der Hintergrundbilder"
            }
    
    def _execute_post_composition_step(self, period: str, workflow_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute post composition step"""
        try:
            print(f"Step 3: Composing visual posts for period {period}")
            
            affirmations = workflow_results.get("affirmations", [])
            background_images = workflow_results.get("background_images", [])
            
            if not affirmations or not background_images:
                return {
                    "step": "post_composition",
                    "success": False,
                    "error": "Missing affirmations or background images",
                    "message": "Affirmationen oder Hintergrundbilder fehlen"
                }
            
            composed_posts = []
            template_name = options.get("template_name", "default")
            post_format = options.get("post_format", "story")
            
            # Create posts by combining affirmations with background images
            for i, affirmation in enumerate(affirmations[:3]):  # Limit to first 3
                # Use different background images or cycle through them
                background_image = background_images[i % len(background_images)]
                
                # Compose the post
                composition_result = self.post_composition_agent.compose_post(
                    background_path=background_image["local_path"],
                    text=affirmation["text"],
                    period=period,
                    template_name=template_name,
                    post_format=post_format,
                    custom_options=options.get("composition_options", {})
                )
                
                if composition_result["success"]:
                    composed_posts.append({
                        "affirmation": affirmation,
                        "background_image": background_image,
                        "composition": composition_result["post"]
                    })
            
            if not composed_posts:
                return {
                    "step": "post_composition",
                    "success": False,
                    "error": "No posts could be composed",
                    "message": "Keine Posts konnten komponiert werden"
                }
            
            return {
                "step": "post_composition",
                "success": True,
                "data": composed_posts,
                "message": f"{len(composed_posts)} visuelle Posts komponiert"
            }
            
        except Exception as e:
            return {
                "step": "post_composition",
                "success": False,
                "error": str(e),
                "message": "Fehler beim Komponieren der Posts"
            }
    
    def _execute_video_generation_step(self, period: str, workflow_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute video generation step"""
        try:
            print(f"Step 4: Creating Instagram reels for period {period}")
            
            visual_posts = workflow_results.get("visual_posts", [])
            
            if not visual_posts:
                return {
                    "step": "video_generation",
                    "success": False,
                    "error": "No visual posts available for video creation",
                    "message": "Keine visuellen Posts für Video-Erstellung verfügbar"
                }
            
            created_reels = []
            video_type = options.get("video_type", "slideshow")
            video_duration = options.get("video_duration", 15)
            
            # Create videos from composed posts
            if video_type == "slideshow" and len(visual_posts) > 1:
                # Create slideshow from multiple posts
                image_paths = [post["composition"]["file_path"] for post in visual_posts]
                
                video_result = self.video_generation_agent.create_video(
                    image_paths=image_paths,
                    video_type=video_type,
                    duration=video_duration,
                    options=options.get("video_options", {})
                )
                
                if video_result["success"]:
                    created_reels.append({
                        "type": "slideshow",
                        "posts_used": visual_posts,
                        "video": video_result["video"]
                    })
            
            else:
                # Create individual videos for each post
                for i, post in enumerate(visual_posts[:2]):  # Limit to first 2 posts
                    video_result = self.video_generation_agent.create_video(
                        image_paths=[post["composition"]["file_path"]],
                        video_type=options.get("individual_video_type", "ken_burns"),
                        duration=video_duration,
                        options=options.get("video_options", {})
                    )
                    
                    if video_result["success"]:
                        created_reels.append({
                            "type": "individual",
                            "post_used": post,
                            "video": video_result["video"]
                        })
            
            if not created_reels:
                return {
                    "step": "video_generation",
                    "success": False,
                    "error": "No reels could be created",
                    "message": "Keine Reels konnten erstellt werden"
                }
            
            return {
                "step": "video_generation",
                "success": True,
                "data": created_reels,
                "message": f"{len(created_reels)} Instagram Reels erstellt"
            }
            
        except Exception as e:
            return {
                "step": "video_generation",
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen der Videos"
            }
    
    def _execute_hashtag_research_step(self, period: str, workflow_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hashtag research and caption generation step"""
        try:
            print(f"Step 5: Generating hashtags and captions for period {period}")
            
            social_content = []
            
            # Generate hashtags and captions for visual posts
            visual_posts = workflow_results.get("visual_posts", [])
            for post in visual_posts:
                hashtag_result = self.hashtag_research_agent.generate_instagram_post(
                    content=post["affirmation"]["text"],
                    period=period,
                    topic=post["affirmation"].get("topic", "")
                )
                
                if hashtag_result["success"]:
                    social_content.append({
                        "type": "visual_post",
                        "post": post,
                        "social_data": hashtag_result["post"]
                    })
            
            # Generate hashtags and captions for reels
            reels = workflow_results.get("reels", [])
            for reel in reels:
                # Use the first affirmation from the reel's posts
                if reel["type"] == "slideshow":
                    base_affirmation = reel["posts_used"][0]["affirmation"]
                else:
                    base_affirmation = reel["post_used"]["affirmation"]
                
                hashtag_result = self.hashtag_research_agent.generate_instagram_post(
                    content=base_affirmation["text"],
                    period=period,
                    topic=base_affirmation.get("topic", ""),
                    post_type="reel"
                )
                
                if hashtag_result["success"]:
                    social_content.append({
                        "type": "reel",
                        "reel": reel,
                        "social_data": hashtag_result["post"]
                    })
            
            if not social_content:
                return {
                    "step": "hashtag_research",
                    "success": False,
                    "error": "No social content could be generated",
                    "message": "Keine Social-Media-Inhalte konnten generiert werden"
                }
            
            return {
                "step": "hashtag_research",
                "success": True,
                "data": social_content,
                "message": f"Hashtags und Captions für {len(social_content)} Inhalte generiert"
            }
            
        except Exception as e:
            return {
                "step": "hashtag_research",
                "success": False,
                "error": str(e),
                "message": "Fehler beim Generieren der Hashtags und Captions"
            }
    
    def _execute_scheduling_step(self, period: str, workflow_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scheduling step"""
        try:
            print(f"Step 6: Scheduling posts for period {period}")
            
            if not self.instagram_poster:
                return {
                    "step": "scheduling",
                    "success": False,
                    "error": "Instagram poster not configured",
                    "message": "Instagram-Poster nicht konfiguriert"
                }
            
            social_content = workflow_results.get("social_content", [])
            
            if not social_content:
                return {
                    "step": "scheduling",
                    "success": False,
                    "error": "No social content available for scheduling",
                    "message": "Keine Social-Media-Inhalte zum Planen verfügbar"
                }
            
            scheduled_posts = []
            schedule_start = options.get("schedule_start_date", datetime.now())
            schedule_interval = options.get("schedule_interval_hours", 24)
            
            for i, content in enumerate(social_content):
                # Calculate posting time
                posting_time = schedule_start + timedelta(hours=i * schedule_interval)
                
                # For now, we'll just prepare the scheduling data
                # Actual scheduling would require Instagram Business API
                scheduled_posts.append({
                    "content": content,
                    "scheduled_time": posting_time.isoformat(),
                    "status": "prepared"
                })
            
            return {
                "step": "scheduling",
                "success": True,
                "data": scheduled_posts,
                "message": f"{len(scheduled_posts)} Posts zum Planen vorbereitet"
            }
            
        except Exception as e:
            return {
                "step": "scheduling",
                "success": False,
                "error": str(e),
                "message": "Fehler beim Planen der Posts"
            }
    
    def _generate_search_tags(self, period: str) -> List[str]:
        """Generate search tags based on period"""
        period_tags = {
            "Image": ["self-image", "confidence", "mirror", "reflection", "beauty"],
            "Veränderung": ["change", "transformation", "growth", "new beginning", "butterfly"],
            "Energie": ["energy", "power", "vitality", "dynamic", "strength"],
            "Kreativität": ["creativity", "art", "inspiration", "colorful", "artistic"],
            "Erfolg": ["success", "achievement", "victory", "goal", "mountain"],
            "Entspannung": ["relaxation", "calm", "peace", "meditation", "zen"],
            "Umsicht": ["wisdom", "contemplation", "mindfulness", "strategy", "planning"]
        }
        
        base_tags = ["lifestyle", "wellness", "inspiration"]
        period_specific = period_tags.get(period, ["general", "motivation"])
        
        return base_tags + period_specific[:3]  # Limit to 6 tags total
    
    def get_workflows(self, period: str = None, status: str = None) -> Dict[str, Any]:
        """Get all workflows, optionally filtered by period or status"""
        try:
            workflows = self.workflows_storage.get("workflows", [])
            
            if period:
                workflows = [w for w in workflows if w.get("period") == period]
            
            if status:
                workflows = [w for w in workflows if w.get("status") == status]
            
            return {
                "success": True,
                "workflows": workflows,
                "count": len(workflows),
                "filters": {"period": period, "status": status}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Abrufen der Workflows"
            }
    
    def get_workflow_by_id(self, workflow_id: str) -> Dict[str, Any]:
        """Get a specific workflow by ID"""
        try:
            workflow = self.workflows_storage.get("by_hash", {}).get(workflow_id)
            
            if not workflow:
                return {
                    "success": False,
                    "error": "Workflow not found",
                    "message": "Workflow nicht gefunden"
                }
            
            return {
                "success": True,
                "workflow": workflow
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Abrufen des Workflows"
            }
    
    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete a workflow and associated files"""
        try:
            # Find and remove from storage
            workflows = self.workflows_storage.get("workflows", [])
            workflow_to_delete = None
            
            for i, workflow in enumerate(workflows):
                if workflow["id"] == workflow_id:
                    workflow_to_delete = workflows.pop(i)
                    break
            
            if not workflow_to_delete:
                return {
                    "success": False,
                    "error": "Workflow not found",
                    "message": "Workflow nicht gefunden"
                }
            
            # Remove from hash index
            if workflow_id in self.workflows_storage.get("by_hash", {}):
                del self.workflows_storage["by_hash"][workflow_id]
            
            # Clean up associated files (optional, as they might be used by other workflows)
            # This could be implemented based on reference counting
            
            # Save updated storage
            self._save_workflows_storage()
            
            return {
                "success": True,
                "message": "Workflow erfolgreich gelöscht"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Löschen des Workflows"
            }
    
    def get_workflow_templates(self) -> Dict[str, Any]:
        """Get available workflow templates"""
        templates = {
            "full": {
                "name": "Vollständiger Workflow",
                "description": "Kompletter Workflow von Affirmationen bis zu geplanten Posts und Reels",
                "steps": [
                    "affirmation_generation",
                    "image_finding",
                    "post_composition",
                    "video_generation",
                    "hashtag_research",
                    "scheduling"
                ],
                "default_options": {
                    "affirmation_count": 5,
                    "image_count": 3,
                    "template_name": "default",
                    "post_format": "story",
                    "create_reels": True,
                    "video_type": "slideshow",
                    "video_duration": 15,
                    "schedule_posts": False
                }
            },
            "posts_only": {
                "name": "Nur Posts",
                "description": "Erstellt nur visuelle Posts ohne Reels",
                "steps": [
                    "affirmation_generation",
                    "image_finding",
                    "post_composition",
                    "hashtag_research"
                ],
                "default_options": {
                    "affirmation_count": 3,
                    "image_count": 2,
                    "template_name": "minimal",
                    "post_format": "post",
                    "create_reels": False,
                    "schedule_posts": False
                }
            },
            "reels_only": {
                "name": "Nur Reels",
                "description": "Erstellt nur Instagram Reels",
                "steps": [
                    "affirmation_generation",
                    "image_finding",
                    "post_composition",
                    "video_generation",
                    "hashtag_research"
                ],
                "default_options": {
                    "affirmation_count": 2,
                    "image_count": 3,
                    "template_name": "dramatic",
                    "post_format": "story",
                    "create_reels": True,
                    "video_type": "ken_burns",
                    "video_duration": 15,
                    "schedule_posts": False
                }
            }
        }
        
        return {
            "success": True,
            "templates": templates
        }