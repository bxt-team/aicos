import os
import json
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib
import base64


class KlingAIClient:
    """Client for KlingAI video generation API"""
    
    def __init__(self, api_key: str, provider: str = "piapi"):
        """
        Initialize KlingAI client
        
        Args:
            api_key: API key for the chosen provider
            provider: API provider ("piapi", "appypie", or "segmind")
        """
        self.api_key = api_key
        self.provider = provider
        
        # Provider configurations
        self.providers = {
            "piapi": {
                "base_url": "https://api.piapi.ai/api/v1",
                "headers": {
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                },
                "models": ["kling"],  # Simple model name as per API docs
                "max_duration": 10,
                "supports_image_to_video": True,
                "supports_text_to_video": True,
                "supports_extend_video": True
            },
            "appypie": {
                "base_url": "https://gateway.appypie.com",
                "headers": {
                    "Subscription-Key": api_key,
                    "Content-Type": "application/json"
                },
                "models": ["kling"],
                "max_duration": 10,
                "supports_image_to_video": True,
                "supports_text_to_video": True,
                "supports_extend_video": False
            },
            "segmind": {
                "base_url": "https://api.segmind.com/v1",
                "headers": {
                    "x-api-key": api_key,
                    "Content-Type": "application/json"
                },
                "models": ["kling-image2video"],
                "max_duration": 5,
                "supports_image_to_video": True,
                "supports_text_to_video": False,
                "supports_extend_video": False
            }
        }
        
        if provider not in self.providers:
            raise ValueError(f"Unknown provider: {provider}. Choose from: {list(self.providers.keys())}")
        
        self.config = self.providers[provider]
    
    def generate_text_to_video(self, prompt: str, duration: int = 5, 
                             aspect_ratio: str = "9:16", model: str = None,
                             negative_prompt: str = None, cfg_scale: float = 0.5,
                             camera_control: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate video from text prompt
        
        Args:
            prompt: Text description of the video to generate
            duration: Video duration in seconds (5 or 10)
            aspect_ratio: Video aspect ratio (9:16 for Instagram Reels)
            model: Model version to use (default: latest)
            negative_prompt: What not to include in the video
            cfg_scale: Creativity scale (0.0-1.0)
            camera_control: Camera movement settings
            
        Returns:
            Dict with task_id and initial status
        """
        if not self.config["supports_text_to_video"]:
            return {
                "success": False,
                "error": f"{self.provider} does not support text-to-video generation"
            }
        
        if duration > self.config["max_duration"]:
            duration = self.config["max_duration"]
        
        if model is None:
            model = self.config["models"][0]
        
        print(f"[KlingAIClient] Using model: {model}, provider: {self.provider}")
        
        try:
            if self.provider == "piapi":
                return self._piapi_text_to_video(prompt, duration, aspect_ratio, model, 
                                               negative_prompt, cfg_scale, camera_control)
            elif self.provider == "appypie":
                return self._appypie_text_to_video(prompt, duration, aspect_ratio, 
                                                 negative_prompt, cfg_scale)
            else:
                return {
                    "success": False,
                    "error": f"{self.provider} does not support text-to-video"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_image_to_video(self, image_path: str, prompt: str = None,
                              duration: int = 5, aspect_ratio: str = "9:16",
                              model: str = None, cfg_scale: float = 0.5) -> Dict[str, Any]:
        """
        Generate video from image
        
        Args:
            image_path: Path to the input image
            prompt: Optional text prompt to guide video generation
            duration: Video duration in seconds
            aspect_ratio: Video aspect ratio
            model: Model version to use
            cfg_scale: Creativity scale
            
        Returns:
            Dict with task_id and initial status
        """
        if not self.config["supports_image_to_video"]:
            return {
                "success": False,
                "error": f"{self.provider} does not support image-to-video generation"
            }
        
        if duration > self.config["max_duration"]:
            duration = self.config["max_duration"]
        
        if model is None:
            model = self.config["models"][0]
        
        try:
            # Read and encode image
            with open(image_path, 'rb') as img_file:
                image_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            if self.provider == "piapi":
                return self._piapi_image_to_video(image_data, prompt, duration, 
                                                aspect_ratio, model, cfg_scale)
            elif self.provider == "appypie":
                return self._appypie_image_to_video(image_data, prompt, duration, 
                                                  aspect_ratio, cfg_scale)
            elif self.provider == "segmind":
                return self._segmind_image_to_video(image_data, prompt, cfg_scale)
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a video generation task
        
        Args:
            task_id: The task ID returned from generation request
            
        Returns:
            Dict with task status and video URL if completed
        """
        try:
            if self.provider == "piapi":
                return self._piapi_get_status(task_id)
            elif self.provider == "appypie":
                return self._appypie_get_status(task_id)
            elif self.provider == "segmind":
                # Segmind typically returns results immediately
                return {
                    "success": True,
                    "status": "completed",
                    "message": "Segmind returns results immediately"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def wait_for_completion(self, task_id: str, timeout: int = 300, 
                          poll_interval: int = 5) -> Dict[str, Any]:
        """
        Wait for a video generation task to complete
        
        Args:
            task_id: The task ID to monitor
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks in seconds
            
        Returns:
            Dict with final status and video URL if successful
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status_result = self.get_task_status(task_id)
            
            if not status_result["success"]:
                return status_result
            
            status = status_result.get("status", "").lower()
            
            if status in ["completed", "succeed", "success"]:
                return status_result
            elif status in ["failed", "error"]:
                return {
                    "success": False,
                    "error": f"Task failed: {status_result.get('message', 'Unknown error')}"
                }
            
            time.sleep(poll_interval)
        
        return {
            "success": False,
            "error": f"Timeout after {timeout} seconds waiting for task completion"
        }
    
    # Provider-specific implementations
    
    def _piapi_text_to_video(self, prompt: str, duration: int, aspect_ratio: str,
                           model: str, negative_prompt: str, cfg_scale: float,
                           camera_control: Dict[str, Any]) -> Dict[str, Any]:
        """PiAPI text-to-video implementation"""
        payload = {
            "model": model,
            "task_type": "video_generation",  # Correct task type per API docs
            "input": {
                "prompt": prompt,
                "duration": duration,  # API expects integer, not string
                "aspect_ratio": aspect_ratio
            }
        }
        
        # Only add optional fields if they have values
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        if cfg_scale is not None:
            payload["input"]["cfg_scale"] = cfg_scale
        
        if camera_control:
            payload["input"]["camera_control"] = camera_control
        
        print(f"[KlingAIClient] Sending payload to piapi: {payload}")
        
        response = requests.post(
            f"{self.config['base_url']}/task",
            headers=self.config["headers"],
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"[KlingAIClient] API Response: {result}")
            
            # Extract task_id from the response - it might be in data.task_id
            task_id = result.get("task_id") or result.get("data", {}).get("task_id")
            
            return {
                "success": True,
                "task_id": task_id,
                "status": "processing",
                "provider": "piapi"
            }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code} - {response.text}"
            }
    
    def _piapi_image_to_video(self, image_data: str, prompt: str, duration: int,
                            aspect_ratio: str, model: str, cfg_scale: float) -> Dict[str, Any]:
        """PiAPI image-to-video implementation"""
        payload = {
            "model": model,
            "task_type": "image_to_video",
            "input": {
                "image": f"data:image/jpeg;base64,{image_data}",
                "prompt": prompt or "",
                "cfg_scale": cfg_scale,
                "duration": duration,  # API expects integer, not string
                "aspect_ratio": aspect_ratio
            }
        }
        
        response = requests.post(
            f"{self.config['base_url']}/task",
            headers=self.config["headers"],
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "task_id": result.get("task_id"),
                "status": "processing",
                "provider": "piapi"
            }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code} - {response.text}"
            }
    
    def _piapi_get_status(self, task_id: str) -> Dict[str, Any]:
        """Get PiAPI task status"""
        response = requests.get(
            f"{self.config['base_url']}/task/{task_id}",
            headers=self.config["headers"]
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "").lower()
            
            if status == "succeed":
                return {
                    "success": True,
                    "status": "completed",
                    "video_url": result.get("output", {}).get("video_url"),
                    "thumbnail_url": result.get("output", {}).get("thumbnail_url"),
                    "duration": result.get("output", {}).get("duration"),
                    "raw_response": result
                }
            elif status == "failed":
                return {
                    "success": False,
                    "status": "failed",
                    "error": result.get("error", "Unknown error")
                }
            else:
                return {
                    "success": True,
                    "status": status,
                    "progress": result.get("progress", 0)
                }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code} - {response.text}"
            }
    
    def _appypie_text_to_video(self, prompt: str, duration: int, aspect_ratio: str,
                             negative_prompt: str, cfg_scale: float) -> Dict[str, Any]:
        """Appy Pie text-to-video implementation"""
        payload = {
            "prompt": prompt,
            "negative_prompt": negative_prompt or "",
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "cfg_scale": cfg_scale
        }
        
        response = requests.post(
            f"{self.config['base_url']}/kling-ai-video/v1/generateVideoTask",
            headers=self.config["headers"],
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "task_id": result.get("task_id"),
                "status": "processing",
                "provider": "appypie"
            }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code} - {response.text}"
            }
    
    def _appypie_image_to_video(self, image_data: str, prompt: str, duration: int,
                              aspect_ratio: str, cfg_scale: float) -> Dict[str, Any]:
        """Appy Pie image-to-video implementation"""
        payload = {
            "image": f"data:image/jpeg;base64,{image_data}",
            "prompt": prompt or "",
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "cfg_scale": cfg_scale
        }
        
        response = requests.post(
            f"{self.config['base_url']}/kling-ai-image2video/v1/generateVideoTask",
            headers=self.config["headers"],
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "task_id": result.get("task_id"),
                "status": "processing",
                "provider": "appypie"
            }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code} - {response.text}"
            }
    
    def _appypie_get_status(self, task_id: str) -> Dict[str, Any]:
        """Get Appy Pie task status"""
        response = requests.get(
            f"{self.config['base_url']}/kling-ai-polling/v1/getVideoStatus",
            headers=self.config["headers"],
            params={"task_id": task_id}
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "").lower()
            
            if status == "completed":
                return {
                    "success": True,
                    "status": "completed",
                    "video_url": result.get("video_url"),
                    "thumbnail_url": result.get("thumbnail_url"),
                    "duration": result.get("duration"),
                    "raw_response": result
                }
            elif status == "failed":
                return {
                    "success": False,
                    "status": "failed",
                    "error": result.get("error", "Unknown error")
                }
            else:
                return {
                    "success": True,
                    "status": status,
                    "progress": result.get("progress", 0)
                }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code} - {response.text}"
            }
    
    def _segmind_image_to_video(self, image_data: str, prompt: str, cfg_scale: float) -> Dict[str, Any]:
        """Segmind image-to-video implementation"""
        payload = {
            "image": f"data:image/jpeg;base64,{image_data}",
            "prompt": prompt or "",
            "cfg_scale": cfg_scale
        }
        
        response = requests.post(
            f"{self.config['base_url']}/kling-image2video",
            headers=self.config["headers"],
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            # Segmind typically returns the video immediately
            return {
                "success": True,
                "status": "completed",
                "video_url": result.get("video_url"),
                "video_data": result.get("video"),  # Base64 encoded video
                "provider": "segmind",
                "raw_response": result
            }
        else:
            return {
                "success": False,
                "error": f"API error: {response.status_code} - {response.text}"
            }