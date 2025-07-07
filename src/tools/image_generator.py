import openai
from PIL import Image
import requests
from io import BytesIO
import os
from typing import Dict, Any, Optional
import json
import datetime
from .feedback_system import FeedbackCollector, FeedbackAnalyzer, PromptOptimizer

class ImageGenerator:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        # Use absolute path for output directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_dir = os.path.join(current_dir, "..", "..", "static", "generated")
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize feedback system
        self.feedback_collector = FeedbackCollector()
        self.feedback_analyzer = FeedbackAnalyzer(self.feedback_collector)
        self.prompt_optimizer = PromptOptimizer(self.feedback_analyzer)
    
    def generate_image(self, prompt: str, style: str = "natural", size: str = "1024x1024", 
                      use_feedback_optimization: bool = True) -> Dict[str, Any]:
        """Generate an image using DALL-E 3 with optional feedback optimization"""
        try:
            # Get feedback-based recommendations
            if use_feedback_optimization:
                recommendations = self.prompt_optimizer.get_generation_recommendations()
                if recommendations["recommended_style"] and not style:
                    style = recommendations["recommended_style"]
                elif recommendations["recommended_style"] and recommendations["style_confidence"] > 0.8:
                    style = recommendations["recommended_style"]
            
            enhanced_prompt = self._enhance_prompt(prompt, style, use_feedback_optimization)
            
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=enhanced_prompt,
                size=size,
                quality="hd" if use_feedback_optimization else "standard",
                n=1,
            )
            
            image_url = response.data[0].url
            image_path = self._download_and_save_image(image_url, prompt)
            
            generation_params = {
                "prompt": enhanced_prompt,
                "original_prompt": prompt,
                "style": style,
                "size": size,
                "quality": "hd" if use_feedback_optimization else "standard",
                "feedback_optimized": use_feedback_optimization
            }
            
            return {
                "success": True,
                "image_url": image_url,
                "image_path": image_path,
                "generation_params": generation_params,
                **generation_params
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "prompt": prompt
            }
    
    def _enhance_prompt(self, prompt: str, style: str, use_feedback_optimization: bool = True) -> str:
        """Enhance the prompt with style-specific instructions and feedback optimization"""
        style_enhancements = {
            "natural": "photorealistic, high quality, natural lighting, clean composition",
            "minimalist": "minimalist design, clean lines, simple composition, plenty of white space, modern aesthetic",
            "warm": "warm color palette, soft lighting, cozy atmosphere, inviting mood",
            "professional": "professional photography, clean, modern, high-end aesthetic, studio quality",
            "inspirational": "uplifting, motivational, bright and positive, inspiring atmosphere",
            "wellness": "wellness and self-care theme, calming, peaceful, zen-like, natural elements"
        }
        
        enhancement = style_enhancements.get(style, style_enhancements["natural"])
        
        # Apply feedback optimization if enabled
        if use_feedback_optimization:
            optimized_prompt = self.prompt_optimizer.optimize_prompt(prompt, style)
            enhanced_prompt = f"{optimized_prompt}, {enhancement}, instagram-worthy, high quality, engaging visual"
        else:
            enhanced_prompt = f"{prompt}, {enhancement}, instagram-worthy, high quality, engaging visual"
        
        return enhanced_prompt
    
    def _download_and_save_image(self, image_url: str, prompt: str) -> str:
        """Download and save the generated image"""
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_image_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            image.save(filepath, "PNG")
            
            return filepath
        except Exception as e:
            raise Exception(f"Failed to download and save image: {str(e)}")
    
    def generate_multiple_images(self, prompts: list, style: str = "natural") -> Dict[str, Any]:
        """Generate multiple images from a list of prompts"""
        results = []
        
        for i, prompt in enumerate(prompts):
            print(f"Generating image {i+1}/{len(prompts)}: {prompt[:50]}...")
            result = self.generate_image(prompt, style)
            results.append(result)
        
        successful_generations = [r for r in results if r["success"]]
        failed_generations = [r for r in results if not r["success"]]
        
        return {
            "total_requested": len(prompts),
            "successful": len(successful_generations),
            "failed": len(failed_generations),
            "results": results,
            "successful_results": successful_generations,
            "failed_results": failed_generations
        }
    
    def create_instagram_post_images(self, visual_concepts: str) -> Dict[str, Any]:
        """Create Instagram-optimized images from visual concepts"""
        try:
            prompts = self._extract_prompts_from_concepts(visual_concepts)
            
            if not prompts:
                return {
                    "success": False,
                    "error": "No valid prompts found in visual concepts"
                }
            
            results = self.generate_multiple_images(prompts, style="inspirational")
            
            return {
                "success": True,
                "images_generated": results["successful"],
                "total_requested": results["total_requested"],
                "results": results["successful_results"],
                "failed": results["failed_results"]
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_prompts_from_concepts(self, visual_concepts: str) -> list:
        """Extract DALL-E prompts from the visual concepts text"""
        prompts = []
        
        lines = visual_concepts.split('\n')
        current_prompt = ""
        
        for line in lines:
            line = line.strip()
            if line.startswith('DALL-E Prompt') or line.startswith('Prompt') or line.startswith('**Prompt'):
                if current_prompt:
                    prompts.append(current_prompt.strip())
                current_prompt = ""
            elif line.startswith('-') and ('prompt' in line.lower() or 'image' in line.lower()):
                if current_prompt:
                    prompts.append(current_prompt.strip())
                current_prompt = line.lstrip('- ')
            elif current_prompt and line and not line.startswith('**'):
                current_prompt += " " + line
        
        if current_prompt:
            prompts.append(current_prompt.strip())
        
        if not prompts:
            prompts = [
                "A minimalist wellness-themed Instagram post with calming colors and inspirational text overlay",
                "A professional lifestyle image showcasing self-care and personal growth with warm lighting",
                "An abstract representation of personal transformation with uplifting visual elements"
            ]
        
        return prompts[:5]
    
    def add_feedback(self, image_path: str, rating: int, comments: str = "", 
                    generation_params: Dict[str, Any] = None, user_id: str = None,
                    tags: list = None) -> str:
        """Add feedback for a generated image"""
        return self.feedback_collector.add_feedback(
            image_path, rating, comments, generation_params, user_id, tags
        )
    
    def get_feedback_analytics(self) -> Dict[str, Any]:
        """Get comprehensive feedback analytics"""
        style_analysis = self.feedback_analyzer.analyze_style_preferences()
        prompt_analysis = self.feedback_analyzer.analyze_prompt_performance()
        recommendations = self.feedback_analyzer.get_optimization_recommendations()
        recent_trends = self.feedback_analyzer.get_recent_feedback_trends()
        
        return {
            "style_rankings": [
                {
                    "style": style,
                    "averageRating": data["average_rating"],
                    "count": data["count"],
                    "ratingDistribution": data["rating_distribution"]
                }
                for style, data in style_analysis["style_rankings"]
            ],
            "bestPerformingStyle": style_analysis["best_performing_style"],
            "promptRankings": [
                {
                    "prompt": data["prompt"],
                    "averageRating": data["average_rating"],
                    "count": data["count"],
                    "ratingDistribution": data["rating_distribution"]
                }
                for _, data in prompt_analysis["prompt_rankings"]
            ],
            "bestPerformingPrompts": [
                {
                    "prompt": data["prompt"],
                    "averageRating": data["average_rating"],
                    "count": data["count"],
                    "ratingDistribution": data["rating_distribution"]
                }
                for _, data in prompt_analysis["best_performing_prompts"]
            ],
            "overallMetrics": recommendations.get("overall_metrics", {}),
            "recentTrends": recent_trends
        }
    
    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for optimizing image generation"""
        return self.feedback_analyzer.get_optimization_recommendations()
    
    def get_feedback_for_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Get feedback for a specific image"""
        return self.feedback_collector.get_feedback_for_image(image_path)