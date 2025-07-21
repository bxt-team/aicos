import os
import json
import subprocess
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
from PIL import Image, ImageDraw, ImageFont
import tempfile
from app.agents.crews.base_crew import BaseCrew
from crewai import Agent, Task, Crew
from crewai.llm import LLM
from app.core.storage import StorageFactory
import asyncio

class VideoGenerationAgent(BaseCrew):
    """Agent for creating Instagram Reels videos from one or more images"""
    
    def __init__(self, openai_api_key: str):
        # Get storage adapter from factory for multi-tenant support
        storage_adapter = StorageFactory.get_adapter()
        super().__init__(storage_adapter=storage_adapter)
        
        self.openai_api_key = openai_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Collection name for videos
        self.collection = "videos"
        
        # Legacy storage for backward compatibility
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/videos_storage.json")
        self.videos_storage = self._load_videos_storage()
        
        # Output directory for created videos
        self.output_dir = os.path.join(os.path.dirname(__file__), "../../static/videos")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Temp directory for processing
        self.temp_dir = os.path.join(os.path.dirname(__file__), "../../static/temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Create the video generation agent
        self.video_agent = self.create_agent("video_generation_agent", llm=self.llm)
        
        # Instagram Reels dimensions (9:16 aspect ratio)
        self.reel_width = 1080
        self.reel_height = 1920
        
        # Video settings
        self.default_fps = 30
        self.default_duration = 15  # seconds
        
        # Check if ffmpeg is available
        self.ffmpeg_available = self._check_ffmpeg()
    
    def _run_async(self, coro):
        """Helper to run async code in sync context"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(coro)
        
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _load_videos_storage(self) -> Dict[str, Any]:
        """Load previously created videos"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading videos storage: {e}")
        return {"videos": [], "by_hash": {}}
    
    def _save_videos_storage(self):
        """Save created videos to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.videos_storage, f, indent=2)
        except Exception as e:
            print(f"Error saving videos storage: {e}")
    
    def _generate_video_hash(self, image_paths: List[str], video_type: str, options: Dict[str, Any]) -> str:
        """Generate a hash for the video parameters"""
        video_key = f"{','.join(sorted(image_paths))}_{video_type}_{json.dumps(options, sort_keys=True)}"
        return hashlib.md5(video_key.encode()).hexdigest()
    
    def create_video(self, image_paths: List[str], video_type: str = "slideshow", 
                    duration: int = 15, fps: int = 30, options: Dict[str, Any] = None,
                    force_new: bool = False) -> Dict[str, Any]:
        """Create a video from one or more images"""
        try:
            if not self.ffmpeg_available:
                return {
                    "success": False,
                    "error": "FFmpeg not available",
                    "message": "FFmpeg ist nicht verfügbar. Bitte installieren Sie FFmpeg."
                }
            
            # Validate input
            if not image_paths:
                return {
                    "success": False,
                    "error": "No images provided",
                    "message": "Keine Bilder bereitgestellt"
                }
            
            # Check if all images exist
            for img_path in image_paths:
                if not os.path.exists(img_path):
                    return {
                        "success": False,
                        "error": f"Image not found: {img_path}",
                        "message": f"Bild nicht gefunden: {img_path}"
                    }
            
            # Check if video already exists
            video_options = options or {}
            video_hash = self._generate_video_hash(image_paths, video_type, video_options)
            
            if not force_new and video_hash in self.videos_storage.get("by_hash", {}):
                existing_video = self.videos_storage["by_hash"][video_hash]
                if os.path.exists(existing_video["file_path"]):
                    return {
                        "success": True,
                        "video": existing_video,
                        "source": "existing",
                        "message": "Bestehendes Video abgerufen"
                    }
            
            # Generate video based on type
            if video_type == "slideshow":
                video_result = self._create_slideshow_video(image_paths, duration, fps, video_options)
            elif video_type == "ken_burns":
                video_result = self._create_ken_burns_video(image_paths, duration, fps, video_options)
            elif video_type == "transition":
                video_result = self._create_transition_video(image_paths, duration, fps, video_options)
            elif video_type == "zoom_in":
                video_result = self._create_zoom_video(image_paths, duration, fps, video_options, zoom_type="in")
            elif video_type == "zoom_out":
                video_result = self._create_zoom_video(image_paths, duration, fps, video_options, zoom_type="out")
            elif video_type == "parallax":
                video_result = self._create_parallax_video(image_paths, duration, fps, video_options)
            else:
                return {
                    "success": False,
                    "error": f"Unknown video type: {video_type}",
                    "message": f"Unbekannter Videotyp: {video_type}"
                }
            
            if not video_result["success"]:
                return video_result
            
            # Store video information
            video_info = {
                "id": video_hash,
                "video_type": video_type,
                "image_paths": image_paths,
                "duration": duration,
                "fps": fps,
                "options": video_options,
                "file_path": video_result["output_path"],
                "file_url": video_result["output_url"],
                "filename": video_result["filename"],
                "file_size": video_result.get("file_size", 0),
                "created_at": datetime.now().isoformat(),
                "dimensions": {
                    "width": self.reel_width,
                    "height": self.reel_height
                }
            }
            
            # Save to multi-tenant storage
            if self.validate_context():
                video_id = self._run_async(
                    self.save_result(self.collection, video_info)
                )
            else:
                video_id = self._run_async(
                    self.storage_adapter.save(self.collection, video_info)
                )
            video_info["id"] = video_id
            
            # Also save to legacy storage for backward compatibility
            self.videos_storage["videos"].append(video_info)
            self.videos_storage["by_hash"][video_hash] = video_info
            self._save_videos_storage()
            
            return {
                "success": True,
                "video": video_info,
                "source": "generated",
                "message": f"{video_type} Video erstellt"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Videos"
            }
    
    def _create_slideshow_video(self, image_paths: List[str], duration: int, fps: int, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a slideshow video with transitions"""
        try:
            # Calculate duration per image
            duration_per_image = duration / len(image_paths)
            
            # Prepare images for video
            prepared_images = []
            for img_path in image_paths:
                prepared_path = self._prepare_image_for_video(img_path)
                if prepared_path:
                    prepared_images.append(prepared_path)
            
            if not prepared_images:
                return {
                    "success": False,
                    "error": "Failed to prepare images",
                    "message": "Fehler beim Vorbereiten der Bilder"
                }
            
            # Create video using ffmpeg
            output_filename = f"slideshow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Build ffmpeg command for slideshow
            cmd = [
                'ffmpeg',
                '-y',  # Overwrite output file
                '-framerate', f'1/{duration_per_image}',  # Duration per image
                '-pattern_type', 'sequence',
                '-i', os.path.join(self.temp_dir, 'slide_%d.jpg'),
                '-vf', f'fps={fps}',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
            
            # Copy images to temp directory with sequence names
            for i, img_path in enumerate(prepared_images):
                temp_path = os.path.join(self.temp_dir, f'slide_{i+1}.jpg')
                shutil.copy2(img_path, temp_path)
            
            # Run ffmpeg
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Clean up temp files
            for i in range(len(prepared_images)):
                temp_path = os.path.join(self.temp_dir, f'slide_{i+1}.jpg')
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"FFmpeg error: {result.stderr}",
                    "message": "Fehler beim Erstellen des Slideshow-Videos"
                }
            
            # Get file size
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": f"/static/videos/{output_filename}",
                "filename": output_filename,
                "file_size": file_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Slideshow-Videos"
            }
    
    def _create_ken_burns_video(self, image_paths: List[str], duration: int, fps: int, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Ken Burns effect video (zoom and pan)"""
        try:
            # For Ken Burns, we'll use the first image or combine multiple
            main_image = image_paths[0]
            prepared_image = self._prepare_image_for_video(main_image)
            
            if not prepared_image:
                return {
                    "success": False,
                    "error": "Failed to prepare image",
                    "message": "Fehler beim Vorbereiten des Bildes"
                }
            
            output_filename = f"ken_burns_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Ken Burns effect: zoom in and pan
            zoom_start = options.get("zoom_start", 1.0)
            zoom_end = options.get("zoom_end", 1.2)
            pan_start = options.get("pan_start", "0:0")
            pan_end = options.get("pan_end", "100:100")
            
            cmd = [
                'ffmpeg',
                '-y',
                '-loop', '1',
                '-i', prepared_image,
                '-vf', f'scale={self.reel_width}:{self.reel_height}:force_original_aspect_ratio=increase,'
                       f'crop={self.reel_width}:{self.reel_height},'
                       f'zoompan=z\'min(zoom+0.0015,{zoom_end})\':d={fps*duration}:x\'iw/2-(iw/zoom/2)\':y\'ih/2-(ih/zoom/2)\':s={self.reel_width}x{self.reel_height}',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"FFmpeg error: {result.stderr}",
                    "message": "Fehler beim Erstellen des Ken Burns Videos"
                }
            
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": f"/static/videos/{output_filename}",
                "filename": output_filename,
                "file_size": file_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Ken Burns Videos"
            }
    
    def _create_transition_video(self, image_paths: List[str], duration: int, fps: int, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a video with smooth transitions between images"""
        try:
            if len(image_paths) < 2:
                return {
                    "success": False,
                    "error": "At least 2 images required for transitions",
                    "message": "Mindestens 2 Bilder für Übergänge erforderlich"
                }
            
            # Prepare images
            prepared_images = []
            for img_path in image_paths:
                prepared_path = self._prepare_image_for_video(img_path)
                if prepared_path:
                    prepared_images.append(prepared_path)
            
            if len(prepared_images) < 2:
                return {
                    "success": False,
                    "error": "Failed to prepare enough images",
                    "message": "Fehler beim Vorbereiten der Bilder"
                }
            
            output_filename = f"transition_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Build complex filter for transitions
            duration_per_image = duration / len(prepared_images)
            transition_duration = options.get("transition_duration", 1.0)
            
            # Create input arguments
            inputs = []
            for img in prepared_images:
                inputs.extend(['-loop', '1', '-t', str(duration_per_image + transition_duration), '-i', img])
            
            # Create filter complex for crossfade transitions
            filter_complex = ""
            for i in range(len(prepared_images) - 1):
                if i == 0:
                    filter_complex += f"[0:v][1:v]xfade=transition=fade:duration={transition_duration}:offset={duration_per_image}[v01];"
                else:
                    filter_complex += f"[v{i-1}{i}][{i+1}:v]xfade=transition=fade:duration={transition_duration}:offset={duration_per_image*(i+1)}[v{i}{i+1}];"
            
            # Final output
            final_output = f"v{len(prepared_images)-2}{len(prepared_images)-1}" if len(prepared_images) > 2 else "v01"
            
            cmd = [
                'ffmpeg',
                '-y'
            ] + inputs + [
                '-filter_complex', filter_complex,
                '-map', f'[{final_output}]',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"FFmpeg error: {result.stderr}",
                    "message": "Fehler beim Erstellen des Übergangs-Videos"
                }
            
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": f"/static/videos/{output_filename}",
                "filename": output_filename,
                "file_size": file_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Übergangs-Videos"
            }
    
    def _create_zoom_video(self, image_paths: List[str], duration: int, fps: int, options: Dict[str, Any], zoom_type: str = "in") -> Dict[str, Any]:
        """Create a zoom in/out video effect"""
        try:
            main_image = image_paths[0]
            prepared_image = self._prepare_image_for_video(main_image)
            
            if not prepared_image:
                return {
                    "success": False,
                    "error": "Failed to prepare image",
                    "message": "Fehler beim Vorbereiten des Bildes"
                }
            
            output_filename = f"zoom_{zoom_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Zoom settings
            if zoom_type == "in":
                zoom_start = options.get("zoom_start", 1.0)
                zoom_end = options.get("zoom_end", 1.5)
            else:  # zoom out
                zoom_start = options.get("zoom_start", 1.5)
                zoom_end = options.get("zoom_end", 1.0)
            
            cmd = [
                'ffmpeg',
                '-y',
                '-loop', '1',
                '-i', prepared_image,
                '-vf', f'scale={self.reel_width}:{self.reel_height}:force_original_aspect_ratio=increase,'
                       f'crop={self.reel_width}:{self.reel_height},'
                       f'zoompan=z\'min(max(zoom,{zoom_start}),{zoom_end})\':d={fps*duration}:x\'iw/2-(iw/zoom/2)\':y\'ih/2-(ih/zoom/2)\':s={self.reel_width}x{self.reel_height}',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"FFmpeg error: {result.stderr}",
                    "message": f"Fehler beim Erstellen des Zoom-{zoom_type} Videos"
                }
            
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": f"/static/videos/{output_filename}",
                "filename": output_filename,
                "file_size": file_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Fehler beim Erstellen des Zoom-{zoom_type} Videos"
            }
    
    def _create_parallax_video(self, image_paths: List[str], duration: int, fps: int, options: Dict[str, Any]) -> Dict[str, Any]:
        """Create a parallax effect video"""
        try:
            main_image = image_paths[0]
            prepared_image = self._prepare_image_for_video(main_image)
            
            if not prepared_image:
                return {
                    "success": False,
                    "error": "Failed to prepare image",
                    "message": "Fehler beim Vorbereiten des Bildes"
                }
            
            output_filename = f"parallax_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # Parallax movement
            move_direction = options.get("direction", "right")  # right, left, up, down
            move_speed = options.get("speed", 2)
            
            if move_direction == "right":
                move_filter = f"crop=iw*0.8:ih*0.8:t*{move_speed}:0"
            elif move_direction == "left":
                move_filter = f"crop=iw*0.8:ih*0.8:iw*0.2-t*{move_speed}:0"
            elif move_direction == "up":
                move_filter = f"crop=iw*0.8:ih*0.8:0:ih*0.2-t*{move_speed}"
            else:  # down
                move_filter = f"crop=iw*0.8:ih*0.8:0:t*{move_speed}"
            
            cmd = [
                'ffmpeg',
                '-y',
                '-loop', '1',
                '-i', prepared_image,
                '-vf', f'scale={self.reel_width*1.2}:{self.reel_height*1.2}:force_original_aspect_ratio=increase,'
                       f'{move_filter},'
                       f'scale={self.reel_width}:{self.reel_height}',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-t', str(duration),
                output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "error": f"FFmpeg error: {result.stderr}",
                    "message": "Fehler beim Erstellen des Parallax-Videos"
                }
            
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            return {
                "success": True,
                "output_path": output_path,
                "output_url": f"/static/videos/{output_filename}",
                "filename": output_filename,
                "file_size": file_size
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Erstellen des Parallax-Videos"
            }
    
    def _prepare_image_for_video(self, image_path: str) -> Optional[str]:
        """Prepare image for video processing (resize to reel dimensions)"""
        try:
            # Load image
            img = Image.open(image_path)
            
            # Resize to reel dimensions
            img_resized = self._resize_to_reel_format(img)
            
            # Convert to RGB if needed
            if img_resized.mode != 'RGB':
                img_resized = img_resized.convert('RGB')
            
            # Save to temp directory
            temp_filename = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.jpg"
            temp_path = os.path.join(self.temp_dir, temp_filename)
            img_resized.save(temp_path, 'JPEG', quality=95)
            
            return temp_path
            
        except Exception as e:
            print(f"Error preparing image {image_path}: {e}")
            return None
    
    def _resize_to_reel_format(self, image: Image.Image) -> Image.Image:
        """Resize image to Instagram Reel format (9:16 - 1080x1920)"""
        # Calculate aspect ratios
        img_ratio = image.width / image.height
        reel_ratio = self.reel_width / self.reel_height
        
        if img_ratio > reel_ratio:
            # Image is wider than reel format - crop width
            new_height = self.reel_height
            new_width = int(new_height * img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop
            left = (new_width - self.reel_width) // 2
            image = image.crop((left, 0, left + self.reel_width, self.reel_height))
        else:
            # Image is taller than reel format - crop height
            new_width = self.reel_width
            new_height = int(new_width / img_ratio)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop
            top = (new_height - self.reel_height) // 2
            image = image.crop((0, top, self.reel_width, top + self.reel_height))
        
        return image
    
    def get_videos(self, video_type: str = None) -> Dict[str, Any]:
        """Get all videos, optionally filtered by type"""
        try:
            # Build filters
            filters = {}
            if video_type:
                filters["video_type"] = video_type
            
            # Get videos from multi-tenant storage
            if self.validate_context():
                videos = self._run_async(
                    self.list_results(
                        self.collection,
                        filters=filters,
                        order_by="created_at",
                        order_desc=True
                    )
                )
            else:
                videos = self._run_async(
                    self.storage_adapter.list(
                        self.collection,
                        filters=filters,
                        order_by="created_at",
                        order_desc=True
                    )
                )
            
            # Also check legacy storage for backward compatibility
            if not videos and self.videos_storage.get("videos"):
                legacy_videos = self.videos_storage.get("videos", [])
                if video_type:
                    legacy_videos = [video for video in legacy_videos if video.get("video_type") == video_type]
                videos.extend(legacy_videos)
            
            return {
                "success": True,
                "videos": videos,
                "count": len(videos),
                "video_type": video_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Abrufen der Videos"
            }
    
    def delete_video(self, video_id: str) -> Dict[str, Any]:
        """Delete a video"""
        try:
            # Find and remove from storage
            videos = self.videos_storage.get("videos", [])
            video_to_delete = None
            
            for i, video in enumerate(videos):
                if video["id"] == video_id:
                    video_to_delete = videos.pop(i)
                    break
            
            if not video_to_delete:
                return {
                    "success": False,
                    "error": "Video not found",
                    "message": "Video nicht gefunden"
                }
            
            # Remove from hash index
            if video_id in self.videos_storage.get("by_hash", {}):
                del self.videos_storage["by_hash"][video_id]
            
            # Delete file
            if os.path.exists(video_to_delete["file_path"]):
                os.remove(video_to_delete["file_path"])
            
            # Save updated storage
            self._save_videos_storage()
            
            return {
                "success": True,
                "message": "Video erfolgreich gelöscht"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Löschen des Videos"
            }
    
    def get_available_video_types(self) -> Dict[str, Any]:
        """Get list of available video types"""
        video_types = {
            "slideshow": {
                "name": "Diashow",
                "description": "Einfache Diashow mit Bildwechsel",
                "options": ["transition_duration"],
                "min_images": 1,
                "recommended_images": "2-5"
            },
            "ken_burns": {
                "name": "Ken Burns",
                "description": "Zoom und Schwenk-Effekt",
                "options": ["zoom_start", "zoom_end", "pan_start", "pan_end"],
                "min_images": 1,
                "recommended_images": "1"
            },
            "transition": {
                "name": "Übergänge",
                "description": "Sanfte Übergänge zwischen Bildern",
                "options": ["transition_duration"],
                "min_images": 2,
                "recommended_images": "2-4"
            },
            "zoom_in": {
                "name": "Zoom In",
                "description": "Hineinzoomen-Effekt",
                "options": ["zoom_start", "zoom_end"],
                "min_images": 1,
                "recommended_images": "1"
            },
            "zoom_out": {
                "name": "Zoom Out",
                "description": "Herauszoomen-Effekt",
                "options": ["zoom_start", "zoom_end"],
                "min_images": 1,
                "recommended_images": "1"
            },
            "parallax": {
                "name": "Parallax",
                "description": "Parallax-Bewegungseffekt",
                "options": ["direction", "speed"],
                "min_images": 1,
                "recommended_images": "1"
            }
        }
        
        return {
            "success": True,
            "video_types": video_types,
            "ffmpeg_available": self.ffmpeg_available
        }
    
    def cleanup_temp_files(self) -> Dict[str, Any]:
        """Clean up temporary files"""
        try:
            temp_files = []
            for file in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    temp_files.append(file)
            
            return {
                "success": True,
                "message": f"{len(temp_files)} temporäre Dateien gelöscht",
                "files_deleted": temp_files
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Löschen der temporären Dateien"
            }