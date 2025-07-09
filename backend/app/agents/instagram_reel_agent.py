import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import requests
from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM

class InstagramReelAgent(BaseCrew):
    """Agent for generating Instagram Reels using Runway AI and ChatGPT Sora"""
    
    def __init__(self, openai_api_key: str, runway_api_key: str = None):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.runway_api_key = runway_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Storage for generated reels
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/instagram_reels_storage.json")
        self.reels_storage = self._load_reels_storage()
        
        # Output directory for generated videos
        self.output_dir = os.path.join(os.path.dirname(__file__), "../../static/reels")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Create the reel generation agent
        self.reel_agent = self.create_agent("instagram_reel_agent", llm=self.llm)
        
        # 7 Cycles period themes for video generation
        self.period_themes = {
            "Image": {
                "color": "#DAA520",
                "mood": "inspiring and uplifting",
                "style": "golden hour, warm tones, cinematic"
            },
            "Veränderung": {
                "color": "#2196F3",
                "mood": "transformative and dynamic",
                "style": "flowing water, morphing shapes, blue tones"
            },
            "Energie": {
                "color": "#F44336",
                "mood": "energetic and powerful",
                "style": "rapid cuts, intense colors, red accents"
            },
            "Kreativität": {
                "color": "#FFD700",
                "mood": "creative and imaginative",
                "style": "artistic effects, paint splashes, yellow highlights"
            },
            "Erfolg": {
                "color": "#CC0066",
                "mood": "confident and successful",
                "style": "luxury aesthetic, magenta tones, elegant"
            },
            "Entspannung": {
                "color": "#4CAF50",
                "mood": "calm and peaceful",
                "style": "nature scenes, soft transitions, green tones"
            },
            "Umsicht": {
                "color": "#9C27B0",
                "mood": "thoughtful and wise",
                "style": "contemplative scenes, purple hues, gentle movement"
            }
        }
        
        # API settings
        self.runway_base_url = "https://api.runwayml.com/v1"
        self.runway_headers = {
            "Authorization": f"Bearer {runway_api_key}",
            "Content-Type": "application/json"
        } if runway_api_key else {}
        
        # Sora API settings (using OpenAI API for Sora)
        self.sora_headers = {
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        }
        
        # Video generation providers
        self.video_providers = {
            "runway": {
                "name": "Runway AI",
                "description": "Professional video generation with advanced AI",
                "max_duration": 30,
                "supports_loops": False,
                "formats": ["mp4"],
                "quality": "high"
            },
            "sora": {
                "name": "ChatGPT Sora",
                "description": "5-second loop videos optimized for social media",
                "max_duration": 5,
                "supports_loops": True,
                "formats": ["mp4"],
                "quality": "high"
            }
        }
    
    def _load_reels_storage(self) -> Dict[str, Any]:
        """Load previously generated reels"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading reels storage: {e}")
        return {"reels": [], "by_hash": {}}
    
    def _save_reels_storage(self):
        """Save generated reels to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.reels_storage, f, indent=2)
        except Exception as e:
            print(f"Error saving reels storage: {e}")
    
    def _generate_reel_hash(self, text: str, period: str, additional_input: str = "") -> str:
        """Generate a hash for the reel parameters"""
        reel_key = f"{text}_{period}_{additional_input}"
        return hashlib.md5(reel_key.encode()).hexdigest()
    
    def generate_video_script(self, instagram_text: str, period: str, 
                            additional_input: str = "", image_descriptions: List[str] = None) -> Dict[str, Any]:
        """Generate a video script for Instagram Reel"""
        try:
            # Create video script generation task
            script_task = Task(
                description=f"""
                Erstelle ein professionelles Video-Script für ein Instagram Reel basierend auf:
                
                Instagram Text: {instagram_text}
                7 Cycles Periode: {period}
                Zusätzlicher Input: {additional_input}
                Bildbeschreibungen: {image_descriptions or []}
                
                Das Script soll:
                1. Eine fesselnde Einleitung (Hook) haben
                2. Den Hauptinhalt strukturiert präsentieren
                3. Einen starken Call-to-Action enthalten
                4. Für die {period}-Periode der 7 Cycles Methode optimiert sein
                5. Visuelle Anweisungen für jede Szene enthalten
                6. 15-30 Sekunden Sprechzeit haben
                
                Periodenspezifische Stimmung: {self.period_themes.get(period, {}).get('mood', 'neutral')}
                
                Erstelle das Script im JSON-Format mit folgender Struktur:
                {{
                    "title": "Reel Titel",
                    "duration": "Geschätzte Dauer in Sekunden",
                    "scenes": [
                        {{
                            "scene_number": 1,
                            "duration": "3-5 Sekunden",
                            "spoken_text": "Text der gesprochen wird",
                            "visual_description": "Beschreibung der visuellen Elemente",
                            "camera_movement": "Kamerabewegung (optional)",
                            "effects": "Visuelle Effekte (optional)"
                        }}
                    ],
                    "call_to_action": "Abschließender Call-to-Action",
                    "hashtags": ["#7cycles", "#{period.lower()}", "zusätzliche Hashtags"],
                    "music_mood": "Beschreibung der gewünschten Musik"
                }}
                """,
                expected_output="Ein detailliertes Video-Script im JSON-Format für ein Instagram Reel",
                agent=self.reel_agent
            )
            
            # Execute script generation
            crew = Crew(
                agents=[self.reel_agent],
                tasks=[script_task],
                verbose=True
            )
            
            script_result = crew.kickoff()
            
            # Parse the generated script
            try:
                script_data = json.loads(script_result.raw)
            except json.JSONDecodeError:
                # If JSON parsing fails, create a simple script structure
                script_data = {
                    "title": f"{period} Reel",
                    "duration": "30",
                    "scenes": [
                        {
                            "scene_number": 1,
                            "duration": "10 Sekunden",
                            "spoken_text": instagram_text[:100] + "...",
                            "visual_description": f"Visuelle Darstellung des {period} Themas",
                            "camera_movement": "Langsamer Zoom",
                            "effects": "Sanfte Übergänge"
                        }
                    ],
                    "call_to_action": "Folge für mehr 7 Cycles Inhalte!",
                    "hashtags": ["#7cycles", f"#{period.lower()}", "#selfcare"],
                    "music_mood": self.period_themes.get(period, {}).get('mood', 'neutral')
                }
            
            return {
                "success": True,
                "script": script_data,
                "message": "Video-Script erfolgreich erstellt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Video-Scripts"
            }
    
    def generate_sora_prompt(self, script: Dict[str, Any], period: str, 
                           image_paths: List[str] = None, loop_style: str = "seamless") -> Dict[str, Any]:
        """Generate a ChatGPT Sora prompt for 5-second loop video generation"""
        try:
            period_theme = self.period_themes.get(period, {})
            
            # Create specialized 5-second loop prompt for Sora
            sora_prompt = f"""
            Create a mesmerizing 5-second looping video for the {period} period of the 7 Cycles method.
            
            Loop Style: {loop_style} loop
            Visual Theme: {period_theme.get('style', 'cinematic, professional')}
            Mood: {period_theme.get('mood', 'inspiring')}
            Color Palette: Emphasizing {period_theme.get('color', '#808080')}
            
            Content Focus: {script.get('scenes', [{}])[0].get('visual_description', 'Inspiring visual content')}
            
            Loop Requirements:
            - Perfect seamless loop (start and end frames should match)
            - Smooth, hypnotic movement that draws attention
            - Optimized for Instagram Reels autoplay
            - Vertical 9:16 aspect ratio
            - High visual impact in first 2 seconds
            
            Visual Elements:
            - Cinematic quality with professional lighting
            - Subtle but engaging motion (flowing, rotating, pulsing)
            - {period_theme.get('color', '#808080')} color dominance
            - Text overlay space at top and bottom thirds
            - Instagram-optimized contrast and saturation
            
            Movement Patterns:
            - Gentle camera movements (slow zoom, drift, or rotation)
            - Natural element motion (flowing water, floating particles, gentle wind)
            - Rhythmic patterns that create visual satisfaction
            - Loop-friendly transitions (circular or wave-like motions)
            
            Technical Specs:
            - 5 seconds exactly
            - 1080x1920 resolution (9:16)
            - 30fps for smooth motion
            - High contrast for mobile viewing
            - Optimized for sound-off viewing
            """
            
            return {
                "success": True,
                "prompt": sora_prompt.strip(),
                "settings": {
                    "duration": 5,
                    "aspect_ratio": "9:16",
                    "loop": True,
                    "loop_style": loop_style,
                    "quality": "high",
                    "fps": 30,
                    "style": period_theme.get('style', 'cinematic'),
                    "mood": period_theme.get('mood', 'inspiring'),
                    "color_theme": period_theme.get('color', '#808080')
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Sora Prompts"
            }

    def generate_runway_prompt(self, script: Dict[str, Any], period: str, 
                             image_paths: List[str] = None) -> Dict[str, Any]:
        """Generate a Runway AI prompt for video generation"""
        try:
            period_theme = self.period_themes.get(period, {})
            
            # Create comprehensive prompt for Runway
            runway_prompt = f"""
            Create a professional Instagram Reel for the {period} period of the 7 Cycles method.
            
            Visual Style: {period_theme.get('style', 'cinematic, professional')}
            Mood: {period_theme.get('mood', 'inspiring')}
            Duration: {script.get('duration', '30')} seconds
            
            Scenes:
            """
            
            for scene in script.get('scenes', []):
                runway_prompt += f"""
                Scene {scene.get('scene_number', 1)}: {scene.get('visual_description', '')}
                Duration: {scene.get('duration', '5 seconds')}
                Camera: {scene.get('camera_movement', 'Steady')}
                Effects: {scene.get('effects', 'None')}
                
                """
            
            runway_prompt += f"""
            
            Additional Requirements:
            - Vertical format (9:16 aspect ratio) for Instagram Reels
            - High quality, cinematic production value
            - Smooth transitions between scenes
            - Color palette emphasizing {period_theme.get('color', '#808080')}
            - Music mood: {script.get('music_mood', 'uplifting')}
            
            Text overlays should include key phrases from: {script.get('call_to_action', '')}
            """
            
            return {
                "success": True,
                "prompt": runway_prompt.strip(),
                "settings": {
                    "aspect_ratio": "9:16",
                    "duration": script.get('duration', '30'),
                    "quality": "high",
                    "style": period_theme.get('style', 'cinematic'),
                    "mood": period_theme.get('mood', 'inspiring')
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Runway Prompts"
            }
    
    def _generate_video_with_sora_api(self, prompt: str, settings: Dict[str, Any], 
                                    image_paths: List[str] = None) -> Dict[str, Any]:
        """Generate 5-second loop video using ChatGPT Sora API"""
        try:
            # Prepare Sora API request
            payload = {
                "model": "sora-1.0",
                "prompt": prompt,
                "size": "1080x1920",  # 9:16 aspect ratio
                "duration": settings.get("duration", 5),
                "loop": settings.get("loop", True),
                "quality": settings.get("quality", "high"),
                "fps": settings.get("fps", 30)
            }
            
            # Add image inputs if provided
            if image_paths:
                payload["image_inputs"] = []
                for img_path in image_paths:
                    if os.path.exists(img_path):
                        # Read and encode image for API
                        import base64
                        with open(img_path, 'rb') as img_file:
                            img_data = base64.b64encode(img_file.read()).decode('utf-8')
                            payload["image_inputs"].append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_data}"
                                }
                            })
            
            # Make API request to OpenAI Sora
            response = requests.post(
                "https://api.openai.com/v1/videos/generations",
                headers=self.sora_headers,
                json=payload,
                timeout=120  # 2 minutes timeout for 5-second videos
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Download generated video
                video_url = result.get("data", [{}])[0].get("url")
                if video_url:
                    video_filename = f"sora_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                    video_path = os.path.join(self.output_dir, video_filename)
                    
                    # Download video
                    video_response = requests.get(video_url)
                    with open(video_path, 'wb') as f:
                        f.write(video_response.content)
                    
                    return {
                        "success": True,
                        "file_path": video_path,
                        "file_url": f"/static/reels/{video_filename}",
                        "thumbnail_url": result.get("data", [{}])[0].get("thumbnail_url"),
                        "provider": "sora",
                        "duration": settings.get("duration", 5),
                        "loop": True
                    }
            
            return {
                "success": False,
                "error": f"Sora API error: {response.status_code}",
                "message": f"Fehler bei der Sora API Anfrage: {response.text}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler bei der Sora Video-Generierung"
            }

    def generate_reel_with_sora(self, instagram_text: str, period: str, 
                              additional_input: str = "", image_paths: List[str] = None,
                              image_descriptions: List[str] = None, loop_style: str = "seamless",
                              force_new: bool = False) -> Dict[str, Any]:
        """Generate Instagram Reel with 5-second Sora loop video"""
        try:
            # Check if reel already exists
            reel_hash = self._generate_reel_hash(instagram_text, period, f"{additional_input}_sora_{loop_style}")
            
            if not force_new and reel_hash in self.reels_storage.get("by_hash", {}):
                existing_reel = self.reels_storage["by_hash"][reel_hash]
                if os.path.exists(existing_reel.get("file_path", "")):
                    return {
                        "success": True,
                        "reel": existing_reel,
                        "source": "existing",
                        "message": "Bestehender Sora Reel abgerufen"
                    }
            
            # Generate video script optimized for 5-second loops
            script_result = self.generate_video_script(
                instagram_text, period, additional_input, image_descriptions
            )
            
            if not script_result["success"]:
                return script_result
            
            script = script_result["script"]
            
            # Generate Sora prompt
            prompt_result = self.generate_sora_prompt(script, period, image_paths, loop_style)
            
            if not prompt_result["success"]:
                return prompt_result
            
            # Generate video with Sora
            video_result = self._generate_video_with_sora_api(
                prompt_result["prompt"],
                prompt_result["settings"],
                image_paths
            )
            
            if not video_result["success"]:
                return video_result
            
            # Store reel information
            reel_info = {
                "id": reel_hash,
                "instagram_text": instagram_text,
                "period": period,
                "additional_input": additional_input,
                "period_color": self.period_themes.get(period, {}).get('color', '#808080'),
                "script": script,
                "sora_prompt": prompt_result["prompt"],
                "sora_settings": prompt_result["settings"],
                "loop_style": loop_style,
                "image_paths": image_paths or [],
                "image_descriptions": image_descriptions or [],
                "file_path": video_result["file_path"],
                "file_url": video_result["file_url"],
                "thumbnail_url": video_result.get("thumbnail_url"),
                "created_at": datetime.now().isoformat(),
                "duration": "5",
                "provider": "sora",
                "is_loop": True,
                "hashtags": script.get("hashtags", [])
            }
            
            # Save to storage
            self.reels_storage["reels"].append(reel_info)
            self.reels_storage["by_hash"][reel_hash] = reel_info
            self._save_reels_storage()
            
            return {
                "success": True,
                "reel": reel_info,
                "source": "generated",
                "message": f"5-Sekunden Sora Loop für {period} erstellt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Sora Reels"
            }

    def generate_reel_with_runway(self, instagram_text: str, period: str, 
                                 additional_input: str = "", image_paths: List[str] = None,
                                 image_descriptions: List[str] = None, force_new: bool = False) -> Dict[str, Any]:
        """Generate complete Instagram Reel using Runway AI"""
        try:
            # Check if reel already exists
            reel_hash = self._generate_reel_hash(instagram_text, period, additional_input)
            
            if not force_new and reel_hash in self.reels_storage.get("by_hash", {}):
                existing_reel = self.reels_storage["by_hash"][reel_hash]
                if os.path.exists(existing_reel.get("file_path", "")):
                    return {
                        "success": True,
                        "reel": existing_reel,
                        "source": "existing",
                        "message": "Bestehender Reel abgerufen"
                    }
            
            # Generate video script
            script_result = self.generate_video_script(
                instagram_text, period, additional_input, image_descriptions
            )
            
            if not script_result["success"]:
                return script_result
            
            script = script_result["script"]
            
            # Generate Runway prompt
            prompt_result = self.generate_runway_prompt(script, period, image_paths)
            
            if not prompt_result["success"]:
                return prompt_result
            
            # Generate video with Runway (if API key is available)
            if self.runway_api_key:
                video_result = self._generate_video_with_runway_api(
                    prompt_result["prompt"],
                    prompt_result["settings"],
                    image_paths
                )
            else:
                # Fallback: Create a mock video or placeholder
                video_result = self._create_placeholder_video(script, period, reel_hash)
            
            if not video_result["success"]:
                return video_result
            
            # Store reel information
            reel_info = {
                "id": reel_hash,
                "instagram_text": instagram_text,
                "period": period,
                "additional_input": additional_input,
                "period_color": self.period_themes.get(period, {}).get('color', '#808080'),
                "script": script,
                "runway_prompt": prompt_result["prompt"],
                "runway_settings": prompt_result["settings"],
                "image_paths": image_paths or [],
                "image_descriptions": image_descriptions or [],
                "file_path": video_result["file_path"],
                "file_url": video_result["file_url"],
                "thumbnail_url": video_result.get("thumbnail_url"),
                "created_at": datetime.now().isoformat(),
                "duration": script.get("duration", "30"),
                "hashtags": script.get("hashtags", [])
            }
            
            # Save to storage
            self.reels_storage["reels"].append(reel_info)
            self.reels_storage["by_hash"][reel_hash] = reel_info
            self._save_reels_storage()
            
            return {
                "success": True,
                "reel": reel_info,
                "source": "generated",
                "message": f"Instagram Reel für {period} erstellt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Instagram Reels"
            }
    
    def _generate_video_with_runway_api(self, prompt: str, settings: Dict[str, Any], 
                                      image_paths: List[str] = None) -> Dict[str, Any]:
        """Generate video using Runway API"""
        try:
            # Prepare Runway API request
            payload = {
                "prompt": prompt,
                "aspect_ratio": settings.get("aspect_ratio", "9:16"),
                "duration": int(settings.get("duration", "30")),
                "quality": settings.get("quality", "high")
            }
            
            # Add image inputs if provided
            if image_paths:
                payload["image_inputs"] = []
                for img_path in image_paths:
                    if os.path.exists(img_path):
                        # In a real implementation, you would upload the image to Runway
                        # For now, we'll just reference the path
                        payload["image_inputs"].append({
                            "path": img_path,
                            "type": "reference"
                        })
            
            # Make API request to Runway
            response = requests.post(
                f"{self.runway_base_url}/generate/video",
                headers=self.runway_headers,
                json=payload,
                timeout=300  # 5 minutes timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Download generated video
                video_url = result.get("video_url")
                if video_url:
                    video_filename = f"reel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                    video_path = os.path.join(self.output_dir, video_filename)
                    
                    # Download video
                    video_response = requests.get(video_url)
                    with open(video_path, 'wb') as f:
                        f.write(video_response.content)
                    
                    return {
                        "success": True,
                        "file_path": video_path,
                        "file_url": f"/static/reels/{video_filename}",
                        "thumbnail_url": result.get("thumbnail_url")
                    }
            
            return {
                "success": False,
                "error": f"Runway API error: {response.status_code}",
                "message": "Fehler bei der Runway API Anfrage"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler bei der Runway Video-Generierung"
            }
    
    def _create_placeholder_video(self, script: Dict[str, Any], period: str, reel_hash: str) -> Dict[str, Any]:
        """Create a placeholder video when Runway API is not available"""
        try:
            # Create a simple text-based video or placeholder
            video_filename = f"reel_placeholder_{period.lower()}_{reel_hash[:8]}.mp4"
            video_path = os.path.join(self.output_dir, video_filename)
            
            # Create a simple placeholder file
            with open(video_path, 'w') as f:
                f.write(f"Placeholder for {period} Reel\nScript: {json.dumps(script, indent=2)}")
            
            return {
                "success": True,
                "file_path": video_path,
                "file_url": f"/static/reels/{video_filename}",
                "thumbnail_url": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Placeholder Videos"
            }
    
    def get_generated_reels(self, period: str = None) -> Dict[str, Any]:
        """Get all generated reels, optionally filtered by period"""
        try:
            reels = self.reels_storage.get("reels", [])
            
            if period:
                reels = [reel for reel in reels if reel.get("period") == period]
            
            return {
                "success": True,
                "reels": reels,
                "count": len(reels),
                "filters": {"period": period}
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Abrufen der generierten Reels"
            }
    
    def delete_reel(self, reel_id: str) -> Dict[str, Any]:
        """Delete a generated reel"""
        try:
            reels = self.reels_storage.get("reels", [])
            reel_to_delete = None
            
            for i, reel in enumerate(reels):
                if reel["id"] == reel_id:
                    reel_to_delete = reels.pop(i)
                    break
            
            if not reel_to_delete:
                return {
                    "success": False,
                    "error": "Reel not found",
                    "message": "Reel nicht gefunden"
                }
            
            # Remove from hash index
            if reel_id in self.reels_storage.get("by_hash", {}):
                del self.reels_storage["by_hash"][reel_id]
            
            # Delete file
            if os.path.exists(reel_to_delete["file_path"]):
                os.remove(reel_to_delete["file_path"])
            
            # Save updated storage
            self._save_reels_storage()
            
            return {
                "success": True,
                "message": "Reel erfolgreich gelöscht"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Löschen des Reels"
            }
    
    def get_period_themes(self) -> Dict[str, Any]:
        """Get available period themes"""
        return {
            "success": True,
            "themes": self.period_themes
        }

    def get_video_providers(self) -> Dict[str, Any]:
        """Get available video generation providers"""
        return {
            "success": True,
            "providers": self.video_providers
        }

    def get_loop_styles(self) -> Dict[str, Any]:
        """Get available loop styles for Sora videos"""
        loop_styles = {
            "seamless": {
                "name": "Seamless Loop",
                "description": "Perfect loop with no visible transition",
                "best_for": "Meditation, ambient content, continuous motion"
            },
            "rhythmic": {
                "name": "Rhythmic Loop",
                "description": "Loop with a clear rhythm or beat",
                "best_for": "Energetic content, fitness, motivation"
            },
            "breathing": {
                "name": "Breathing Loop",
                "description": "Gentle in-and-out motion like breathing",
                "best_for": "Relaxation, mindfulness, wellness"
            },
            "flow": {
                "name": "Flow Loop",
                "description": "Continuous flowing motion",
                "best_for": "Water, wind, abstract movement"
            },
            "pulse": {
                "name": "Pulse Loop",
                "description": "Pulsing or heartbeat-like rhythm",
                "best_for": "Energy, vitality, life force themes"
            }
        }
        
        return {
            "success": True,
            "loop_styles": loop_styles
        }