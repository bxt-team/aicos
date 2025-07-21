import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM
from app.core.storage import StorageFactory
import asyncio

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
        # Get storage adapter from factory for multi-tenant support
        storage_adapter = StorageFactory.get_adapter()
        super().__init__(storage_adapter=storage_adapter)
        
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
        
        # Collection name for workflows
        self.collection = "workflows"
        
        # Legacy storage for backward compatibility
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/workflows_storage.json")
        
        # Create the workflow orchestration agent
        self.workflow_agent = self.create_agent("content_workflow_agent", llm=self.llm)
    
    def _propagate_context_to_agents(self):
        """Propagate context to all sub-agents"""
        if not self.validate_context():
            return
        
        # Propagate context to all sub-agents
        if hasattr(self.affirmations_agent, 'set_context'):
            self.affirmations_agent.set_context(self._context)
        if hasattr(self.visual_post_creator, 'set_context'):
            self.visual_post_creator.set_context(self._context)
        if hasattr(self.post_composition_agent, 'set_context'):
            self.post_composition_agent.set_context(self._context)
        if hasattr(self.video_generation_agent, 'set_context'):
            self.video_generation_agent.set_context(self._context)
        if hasattr(self.hashtag_research_agent, 'set_context'):
            self.hashtag_research_agent.set_context(self._context)
        if self.instagram_poster and hasattr(self.instagram_poster, 'set_context'):
            self.instagram_poster.set_context(self._context)
    
    async def _save_workflow_to_storage(self, workflow_data: Dict[str, Any]) -> str:
        """Save workflow to storage with multi-tenant support"""
        try:
            # Prepare data for storage
            storage_data = {
                "workflow_type": workflow_data.get("workflow_type", "content_generation"),
                "workflow_config": {
                    "period": workflow_data.get("period"),
                    "options": workflow_data.get("options", {}),
                    "workflow_id": workflow_data.get("id")
                },
                "status": workflow_data.get("status", "pending"),
                "result": workflow_data.get("results", {}),
                "error_message": workflow_data.get("error"),
                "started_at": workflow_data.get("started_at"),
                "completed_at": workflow_data.get("completed_at")
            }
            
            # Save to storage with context
            if self.validate_context():
                workflow_id = await self.save_result(self.collection, storage_data)
            else:
                # Fallback to direct storage if no context
                workflow_id = await self.storage_adapter.save(self.collection, storage_data)
            return workflow_id
        except Exception as e:
            print(f"Error saving workflow to storage: {e}")
            return ""
    
    async def _get_workflow_from_storage(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow from storage with multi-tenant support"""
        try:
            if self.validate_context():
                workflow = await self.load_result(self.collection, workflow_id)
            else:
                # Fallback to direct storage if no context
                workflow = await self.storage_adapter.load(self.collection, workflow_id)
            return workflow
        except Exception as e:
            print(f"Error loading workflow from storage: {e}")
            return None
        
    def _load_workflows_storage(self) -> Dict[str, Any]:
        """Load previously created workflows from legacy storage"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading workflows storage: {e}")
        return {"workflows": [], "by_hash": {}}
    
    def _save_workflows_storage(self, workflows_storage: Dict[str, Any]):
        """Save workflows to legacy storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(workflows_storage, f, indent=2)
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
            # Propagate context to all sub-agents
            self._propagate_context_to_agents()
            
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
            
            # Save workflow to Supabase
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                storage_id = loop.run_until_complete(
                    self._save_workflow_to_storage(workflow_result)
                )
                workflow_result["storage_id"] = storage_id
            finally:
                loop.close()
            
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
            
            # Get period info
            period_info = {
                "description": f"Focus on {period}",
                "color": options.get("period_color", "#DAA520")
            }
            
            # Run async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                affirmation_result = loop.run_until_complete(
                    self.affirmations_agent.generate_affirmations(
                        period_name=period,
                        period_info=period_info,
                        count=affirmation_count
                    )
                )
            finally:
                loop.close()
            
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
            
            # Define search tags based on period
            search_tags = self._generate_search_tags(period)
            
            # Find suitable background images
            image_result = self.visual_post_creator.find_background_images(
                tags=search_tags,
                count=options.get("image_count", 5)
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
            print(f"Step 3: Creating visual posts for period {period}")
            
            # Get affirmations and images from previous steps
            affirmations = workflow_results.get("affirmations", [])
            images = workflow_results.get("background_images", [])
            
            if not affirmations or not images:
                return {
                    "step": "post_composition",
                    "success": False,
                    "error": "Keine Affirmationen oder Bilder verfügbar",
                    "message": "Vorherige Schritte müssen erfolgreich sein"
                }
            
            # Create visual posts
            visual_posts = []
            for i, affirmation in enumerate(affirmations[:min(len(affirmations), len(images))]):
                # Use post composition agent to create post
                composition_result = self.post_composition_agent.create_visual_post(
                    affirmation_text=affirmation["text"],
                    background_image_url=images[i]["urls"]["large"],
                    period=period,
                    theme=affirmation.get("theme", period)
                )
                
                if composition_result["success"]:
                    visual_posts.append({
                        "affirmation": affirmation,
                        "image": images[i],
                        "post_data": composition_result["post_data"],
                        "created_at": datetime.now().isoformat()
                    })
            
            return {
                "step": "post_composition",
                "success": True,
                "data": visual_posts,
                "message": f"{len(visual_posts)} visuelle Posts erstellt"
            }
            
        except Exception as e:
            return {
                "step": "post_composition",
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen der visuellen Posts"
            }
    
    def _execute_video_generation_step(self, period: str, workflow_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute video generation step"""
        try:
            print(f"Step 4: Creating Instagram reels for period {period}")
            
            # Get affirmations from previous steps
            affirmations = workflow_results.get("affirmations", [])
            
            if not affirmations:
                return {
                    "step": "video_generation",
                    "success": False,
                    "error": "Keine Affirmationen verfügbar",
                    "message": "Affirmationen müssen zuerst generiert werden"
                }
            
            # Create reels
            reels = []
            for affirmation in affirmations[:options.get("reel_count", 2)]:
                # Generate reel using video generation agent
                reel_result = self.video_generation_agent.generate_instagram_reel(
                    theme=affirmation.get("theme", period),
                    content_type="affirmation",
                    text_content=affirmation["text"],
                    duration=options.get("reel_duration", 15),
                    include_voiceover=options.get("include_voiceover", True)
                )
                
                if reel_result["success"]:
                    reels.append({
                        "affirmation": affirmation,
                        "reel_data": reel_result["reel"],
                        "created_at": datetime.now().isoformat()
                    })
            
            return {
                "step": "video_generation",
                "success": True,
                "data": reels,
                "message": f"{len(reels)} Instagram Reels erstellt"
            }
            
        except Exception as e:
            return {
                "step": "video_generation",
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen der Instagram Reels"
            }
    
    def _execute_hashtag_research_step(self, period: str, workflow_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute hashtag research and caption generation step"""
        try:
            print(f"Step 5: Generating hashtags and captions for period {period}")
            
            # Get content from previous steps
            visual_posts = workflow_results.get("visual_posts", [])
            reels = workflow_results.get("reels", [])
            
            # Generate hashtags and captions for posts
            social_content = {
                "posts": [],
                "reels": []
            }
            
            # Process visual posts
            for post in visual_posts:
                hashtag_result = self.hashtag_research_agent.generate_hashtags_and_caption(
                    content_type="visual_post",
                    theme=period,
                    affirmation_text=post["affirmation"]["text"]
                )
                
                if hashtag_result["success"]:
                    social_content["posts"].append({
                        "post": post,
                        "caption": hashtag_result["caption"],
                        "hashtags": hashtag_result["hashtags"],
                        "engagement_tips": hashtag_result.get("engagement_tips", [])
                    })
            
            # Process reels
            for reel in reels:
                hashtag_result = self.hashtag_research_agent.generate_hashtags_and_caption(
                    content_type="reel",
                    theme=period,
                    affirmation_text=reel["affirmation"]["text"]
                )
                
                if hashtag_result["success"]:
                    social_content["reels"].append({
                        "reel": reel,
                        "caption": hashtag_result["caption"],
                        "hashtags": hashtag_result["hashtags"],
                        "engagement_tips": hashtag_result.get("engagement_tips", [])
                    })
            
            return {
                "step": "hashtag_research",
                "success": True,
                "data": social_content,
                "message": f"Hashtags und Captions für {len(social_content['posts'])} Posts und {len(social_content['reels'])} Reels generiert"
            }
            
        except Exception as e:
            return {
                "step": "hashtag_research",
                "success": False,
                "error": str(e),
                "message": "Fehler beim Generieren der Hashtags und Captions"
            }
    
    def _execute_scheduling_step(self, period: str, workflow_results: Dict[str, Any], options: Dict[str, Any]) -> Dict[str, Any]:
        """Execute post scheduling step"""
        try:
            print(f"Step 6: Scheduling posts for period {period}")
            
            # Get social content from previous step
            social_content = workflow_results.get("social_content", {})
            
            scheduled_posts = []
            
            # Schedule visual posts
            for i, post_data in enumerate(social_content.get("posts", [])):
                # Calculate schedule time
                base_time = datetime.now() + timedelta(days=options.get("start_delay_days", 1))
                schedule_time = base_time + timedelta(hours=i * options.get("post_interval_hours", 24))
                
                # Schedule the post
                schedule_result = self.instagram_poster.schedule_post(
                    image_url=post_data["post"]["image"]["urls"]["large"],
                    caption=post_data["caption"],
                    hashtags=post_data["hashtags"],
                    schedule_time=schedule_time
                )
                
                if schedule_result["success"]:
                    scheduled_posts.append({
                        "type": "visual_post",
                        "content": post_data,
                        "scheduled_time": schedule_time.isoformat(),
                        "schedule_result": schedule_result
                    })
            
            # Schedule reels
            for i, reel_data in enumerate(social_content.get("reels", [])):
                # Calculate schedule time (offset from posts)
                base_time = datetime.now() + timedelta(days=options.get("start_delay_days", 1) + 1)
                schedule_time = base_time + timedelta(hours=i * options.get("reel_interval_hours", 48))
                
                # Schedule the reel
                schedule_result = self.instagram_poster.schedule_reel(
                    video_url=reel_data["reel"]["reel_data"]["video_url"],
                    caption=reel_data["caption"],
                    hashtags=reel_data["hashtags"],
                    schedule_time=schedule_time
                )
                
                if schedule_result["success"]:
                    scheduled_posts.append({
                        "type": "reel",
                        "content": reel_data,
                        "scheduled_time": schedule_time.isoformat(),
                        "schedule_result": schedule_result
                    })
            
            return {
                "step": "scheduling",
                "success": True,
                "data": scheduled_posts,
                "message": f"{len(scheduled_posts)} Posts geplant"
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
            "Image": ["identity", "self-confidence", "personal-style", "authentic-self"],
            "Veränderung": ["transformation", "change", "growth", "adaptation"],
            "Energie": ["energy", "vitality", "power", "motivation"],
            "Kreativität": ["creativity", "innovation", "artistic", "inspiration"],
            "Erfolg": ["success", "achievement", "goals", "manifestation"],
            "Entspannung": ["relaxation", "calm", "balance", "peace"],
            "Umsicht": ["wisdom", "planning", "reflection", "strategy"]
        }
        
        return period_tags.get(period, ["inspiration", "motivation", "spiritual"])
    
    def get_workflows(self, period: str = None, status: str = None) -> Dict[str, Any]:
        """Get all workflows, optionally filtered by period and status"""
        try:
            # Build filters
            filters = {}
            if status:
                filters["status"] = status
            
            # Get workflows from storage with multi-tenant support
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if self.validate_context():
                    workflows = loop.run_until_complete(
                        self.list_results(
                            self.collection,
                            filters=filters,
                            order_by="created_at",
                            order_desc=True
                        )
                    )
                else:
                    # Fallback to direct storage if no context
                    workflows = loop.run_until_complete(
                        self.storage_adapter.list(
                            self.collection,
                            filters=filters,
                            order_by="created_at",
                            order_desc=True
                        )
                    )
            finally:
                loop.close()
            
            # Additional filtering for period (if needed)
            if period and workflows:
                workflows = [
                    w for w in workflows 
                    if w.get("workflow_config", {}).get("period") == period
                ]
            
            return {
                "success": True,
                "workflows": workflows,
                "count": len(workflows)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "workflows": []
            }
    
    def get_workflow_by_id(self, workflow_id: str) -> Dict[str, Any]:
        """Get a specific workflow by ID"""
        try:
            # Get workflow from storage
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                workflow = loop.run_until_complete(
                    self._get_workflow_from_storage(workflow_id)
                )
            finally:
                loop.close()
            
            if workflow:
                return {
                    "success": True,
                    "workflow": workflow
                }
            else:
                return {
                    "success": False,
                    "error": "Workflow nicht gefunden"
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete a workflow"""
        try:
            # For now, we can't delete from Supabase through the storage adapter
            # This would need to be implemented in the storage adapter
            return {
                "success": False,
                "error": "Delete operation not yet implemented for Supabase storage"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Löschen des Workflows"
            }
    
    def get_workflow_templates(self) -> Dict[str, Any]:
        """Get available workflow templates"""
        return {
            "success": True,
            "templates": {
                "full": {
                    "name": "Vollständiger Content-Workflow",
                    "description": "Generiert Affirmationen, erstellt visuelle Posts und Reels, fügt Hashtags hinzu und plant Posts",
                    "default_options": {
                        "affirmation_count": 5,
                        "image_count": 5,
                        "reel_count": 2,
                        "reel_duration": 15,
                        "include_voiceover": True,
                        "create_reels": True,
                        "schedule_posts": False,
                        "start_delay_days": 1,
                        "post_interval_hours": 24,
                        "reel_interval_hours": 48
                    }
                },
                "posts_only": {
                    "name": "Nur visuelle Posts",
                    "description": "Generiert Affirmationen und erstellt visuelle Posts mit Hashtags",
                    "default_options": {
                        "affirmation_count": 5,
                        "image_count": 5,
                        "create_reels": False,
                        "schedule_posts": False
                    }
                },
                "reels_only": {
                    "name": "Nur Instagram Reels",
                    "description": "Generiert Affirmationen und erstellt Instagram Reels mit Hashtags",
                    "default_options": {
                        "affirmation_count": 3,
                        "reel_count": 3,
                        "reel_duration": 15,
                        "include_voiceover": True,
                        "create_reels": True,
                        "schedule_posts": False
                    }
                },
                "minimal": {
                    "name": "Minimaler Workflow",
                    "description": "Generiert nur Affirmationen für die Periode",
                    "default_options": {
                        "affirmation_count": 5,
                        "image_count": 0,
                        "create_reels": False,
                        "schedule_posts": False
                    }
                }
            }
        }