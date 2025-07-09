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
            # Download immediately to avoid URL expiration
            image_path = self._download_and_save_image(image_url, prompt)
            
            # Create a local URL for serving
            filename = os.path.basename(image_path)
            local_url = f"/static/generated/{filename}"
            
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
                "image_url": local_url,  # Use local URL instead of DALL-E URL
                "dalle_url": image_url,  # Keep original URL for reference
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
        """Enhance the prompt with style-specific instructions and feedback optimization in German"""
        style_enhancements = {
            "natural": "fotorealistisch, hohe Qualität, natürliche Beleuchtung, saubere Komposition",
            "minimalist": "minimalistisches Design, klare Linien, einfache Komposition, viel Weißraum, moderne Ästhetik",
            "warm": "warme Farbpalette, weiches Licht, gemütliche Atmosphäre, einladende Stimmung",
            "professional": "professionelle Fotografie, sauber, modern, hochwertige Ästhetik, Studio-Qualität",
            "inspirational": "erhebend, motivierend, hell und positiv, inspirierende Atmosphäre",
            "wellness": "Wellness und Selbstfürsorge-Thema, beruhigend, friedlich, zen-artig, natürliche Elemente",
            "dalle": "künstlerisch, kreativ, ausdrucksstark, visuell ansprechend, moderne digitale Kunst"
        }
        
        enhancement = style_enhancements.get(style, style_enhancements["natural"])
        
        # Apply feedback optimization if enabled
        if use_feedback_optimization:
            optimized_prompt = self.prompt_optimizer.optimize_prompt(prompt, style)
            enhanced_prompt = f"{optimized_prompt}, {enhancement}, Instagram-würdig, hohe Qualität, ansprechendes visuelles Erlebnis"
        else:
            enhanced_prompt = f"{prompt}, {enhancement}, Instagram-würdig, hohe Qualität, ansprechendes visuelles Erlebnis"
        
        return enhanced_prompt
    
    def _download_and_save_image(self, image_url: str, prompt: str) -> str:
        """Download and save the generated image"""
        try:
            print(f"Downloading image from: {image_url[:100]}...")  # Print first 100 chars
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_image_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            # Ensure directory exists
            os.makedirs(self.output_dir, exist_ok=True)
            
            print(f"Saving image to: {filepath}")
            image.save(filepath, "PNG")
            
            # Verify file was saved
            if not os.path.exists(filepath):
                raise Exception(f"Image file was not saved to {filepath}")
            
            print(f"Image successfully saved to: {filepath}")
            return filepath
        except Exception as e:
            print(f"ERROR in _download_and_save_image: {str(e)}")
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
    
    def optimize_prompt_with_feedback(self, original_prompt: str, feedback: str, rating: int, 
                                    style: str = "dalle", period: str = "", 
                                    existing_generation_params: Optional[Dict] = None) -> str:
        """
        Optimize a prompt based on user feedback for regeneration
        
        Args:
            original_prompt: The original DALL-E prompt that was used
            feedback: User's feedback about what they want changed
            rating: User's rating (1-5) of the original image
            style: Image style being used
            period: 7 Cycles period context
            existing_generation_params: Previous generation parameters
            
        Returns:
            Optimized prompt string
        """
        try:
            # Start with the original prompt as base
            optimized_prompt = original_prompt
            
            # Get general optimization recommendations from feedback system
            recommendations = self.prompt_optimizer.get_generation_recommendations()
            
            # Apply feedback-specific optimizations based on rating and comments
            # First, always remove specific unwanted elements regardless of rating
            optimized_prompt = self._remove_unwanted_elements(optimized_prompt, feedback)
            
            if rating <= 2:
                # Poor rating - major changes needed
                optimized_prompt = self._apply_major_optimizations(optimized_prompt, feedback, recommendations)
            elif rating == 3:
                # Moderate rating - some improvements needed
                optimized_prompt = self._apply_moderate_optimizations(optimized_prompt, feedback, recommendations)
            else:
                # Good rating - minor refinements
                optimized_prompt = self._apply_minor_optimizations(optimized_prompt, feedback, recommendations)
            
            # Apply period-specific enhancements if available
            if period:
                period_enhancements = self._get_period_enhancements(period)
                if period_enhancements:
                    optimized_prompt = f"{optimized_prompt}, {period_enhancements}"
            
            # Apply style-specific feedback optimizations
            style_optimizations = self._get_style_feedback_optimizations(style, recommendations)
            if style_optimizations:
                optimized_prompt = f"{optimized_prompt}, {style_optimizations}"
            
            return optimized_prompt
            
        except Exception as e:
            print(f"Error optimizing prompt with feedback: {e}")
            return original_prompt  # Fallback to original if optimization fails
    
    def _remove_unwanted_elements(self, prompt: str, feedback: str) -> str:
        """Remove specific elements mentioned in negative feedback"""
        feedback_lower = feedback.lower()
        
        # Remove specific elements mentioned in negative feedback
        if any(word in feedback_lower for word in ['butterfly', 'butterflies', 'schmetterling', 'schmetterlinge']):
            prompt = prompt.replace("butterflies", "").replace("butterfly", "")
            prompt = prompt.replace("Schmetterlinge", "").replace("Schmetterling", "")
        
        if any(word in feedback_lower for word in ['water', 'wasser', 'flowing water', 'fließendes wasser']):
            prompt = prompt.replace("flowing water", "").replace("water", "")
            prompt = prompt.replace("fließendes Wasser", "").replace("Wasser", "")
            
        if any(word in feedback_lower for word in ['color code', 'farbcode', 'color scale', 'farbskala', 'color scheme']):
            prompt = prompt.replace("color scheme", "").replace("#2196F3 color scheme", "")
            prompt = prompt.replace("Farbschema", "").replace("#2196F3", "")
        
        # Clean up the prompt (remove multiple spaces and commas)
        prompt = ' '.join(prompt.split())
        prompt = prompt.replace(", ,", ",").replace(",,", ",").strip()
        if prompt.startswith(", "):
            prompt = prompt[2:]
        if prompt.endswith(", "):
            prompt = prompt[:-2]
            
        return prompt
    
    def _apply_major_optimizations(self, prompt: str, feedback: str, recommendations: Dict) -> str:
        """Apply major changes for low-rated images with German prompts"""
        optimizations = []
        
        # Common issues from negative feedback
        feedback_lower = feedback.lower()
        
        # Lighting issues
        if any(word in feedback_lower for word in ['dark', 'too dark', 'darker', 'dunkel', 'zu dunkel']):
            optimizations.append("helles, gut beleuchtetes, lebendiges Licht")
        elif any(word in feedback_lower for word in ['bright', 'too bright', 'harsh', 'hell', 'zu hell', 'grell']):
            optimizations.append("weiches Licht, sanfte Beleuchtung")
            
        # Composition issues
        if any(word in feedback_lower for word in ['cluttered', 'busy', 'too much', 'überladen', 'zu viel', 'unübersichtlich']):
            optimizations.append("saubere, minimalistische, einfache Komposition")
        elif any(word in feedback_lower for word in ['empty', 'boring', 'plain', 'leer', 'langweilig', 'einfach']):
            optimizations.append("reiche Details, ansprechende Komposition")
            
        # Color issues
        if any(word in feedback_lower for word in ['colors', 'color', 'palette', 'farben', 'farbe', 'farbpalette']):
            optimizations.append("harmonische Farbpalette, professionelle Farbgebung")
            
        # Quality issues
        if any(word in feedback_lower for word in ['blurry', 'unclear', 'quality', 'unscharf', 'unklar', 'qualität']):
            optimizations.append("scharfer Fokus, hohe Auflösung, kristallklar")
        
        # Suggest alternatives for transformation theme
        optimizations.append("abstrakte geometrische Muster, natürliche Landschaften oder symbolische Bilder")
        
        # Add general quality improvements for low ratings in German
        optimizations.extend([
            "professionelle Fotografie-Qualität",
            "Instagram-würdig", 
            "visuell ansprechend",
            "spirituell und erhebend"
        ])
        
        if optimizations:
            return f"{prompt}, {', '.join(optimizations)}"
        return prompt
    
    def _apply_moderate_optimizations(self, prompt: str, feedback: str, recommendations: Dict) -> str:
        """Apply moderate changes for mid-rated images with German prompts"""
        optimizations = []
        feedback_lower = feedback.lower()
        
        # More targeted improvements
        if any(word in feedback_lower for word in ['composition', 'layout', 'komposition', 'aufbau', 'anordnung']):
            optimizations.append("verbesserte Komposition, ausgewogenes Layout")
        if any(word in feedback_lower for word in ['atmosphere', 'mood', 'feeling', 'atmosphäre', 'stimmung', 'gefühl']):
            optimizations.append("verstärkte Atmosphäre, emotionale Tiefe")
        if any(word in feedback_lower for word in ['detail', 'details', 'detailreich', 'einzelheiten']):
            optimizations.append("reiche Texturen, feine Details")
            
        # Add style consistency in German
        optimizations.extend([
            "verbesserte visuelle Anziehungskraft",
            "harmonische Gestaltung",
            "künstlerische Qualität"
        ])
        
        if optimizations:
            return f"{prompt}, {', '.join(optimizations)}"
        return prompt
    
    def _apply_minor_optimizations(self, prompt: str, feedback: str, recommendations: Dict) -> str:
        """Apply minor refinements for well-rated images with German prompts"""
        optimizations = []
        feedback_lower = feedback.lower()
        
        # Small refinements only
        if any(word in feedback_lower for word in ['perfect', 'love', 'great', 'beautiful', 'perfekt', 'liebe', 'großartig', 'schön', 'wunderbar']):
            # User loves it, just enhance quality
            optimizations.append("perfektionierte Details")
        elif feedback_lower.strip():
            # Minor specific feedback
            optimizations.append("verfeinerte Komposition")
            
        # Always add subtle enhancement for high-rated images
        optimizations.append("subtile Verbesserungen")
            
        if optimizations:
            return f"{prompt}, {', '.join(optimizations)}"
        return prompt
    
    def _get_period_enhancements(self, period: str) -> str:
        """Get period-specific visual enhancements for 7 Cycles in German"""
        period_map = {
            "Image": "goldene Töne, Identitätssymbole, selbstbewusste Bildsprache",
            "Veränderung": "Transformationsthemen, blaue Akzente, Wandel-Symbolik", 
            "Energie": "energetische Komposition, rote Elemente, Vitalitätsthemen",
            "Kreativität": "kreative Elemente, gelbe Highlights, Innovationssymbole",
            "Erfolg": "Erfolgsbilder, magenta Akzente, Errungenschaften-Themen",
            "Entspannung": "friedliche Atmosphäre, grüne Töne, ruhige Elemente",
            "Umsicht": "Weisheitsthemen, violette Akzente, nachdenkliche Stimmung"
        }
        return period_map.get(period, "")
    
    def _get_style_feedback_optimizations(self, style: str, recommendations: Dict) -> str:
        """Get style-specific optimizations based on feedback analytics in German"""
        try:
            style_data = recommendations.get('style_recommendations', {}).get(style, {})
            if style_data.get('needs_improvement', False):
                common_issues = style_data.get('common_negative_feedback', [])
                if common_issues:
                    # Address the most common issues for this style
                    return "Behandlung visueller Qualitätsbedenken, verbesserte Anziehungskraft"
            return ""
        except:
            return ""