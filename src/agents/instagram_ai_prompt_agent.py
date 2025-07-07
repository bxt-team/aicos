from crewai import Agent, Task, Crew
from crewai.llm import LLM
import os
import json
from typing import Dict, Any, List
from datetime import datetime
import hashlib
from src.crews.base_crew import BaseCrew
from src.tools.image_generator import ImageGenerator

class InstagramAIPromptAgent(BaseCrew):
    """Agent for creating AI image prompts from complete Instagram post data"""
    
    def __init__(self, openai_api_key: str):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize image generator
        self.image_generator = ImageGenerator(openai_api_key)
        
        # Storage for generated prompts and images
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/ai_prompt_storage.json")
        self.generated_content = self._load_generated_content()
        
        # Create the prompt generation agent
        self.prompt_agent = self._create_prompt_agent()
        
        # 7 Cycles period colors and themes
        self.period_info = {
            "Image": {
                "color": "#DAA520",
                "themes": ["self-image", "identity", "authenticity", "confidence", "recognition", "professional appearance"],
                "visual_elements": ["mirrors", "golden light", "professional settings", "clear reflections", "polished surfaces"]
            },
            "Veränderung": {
                "color": "#2196F3", 
                "themes": ["transformation", "change", "growth", "adaptability", "flow", "evolution"],
                "visual_elements": ["flowing water", "butterflies", "seasonal changes", "metamorphosis", "bridges", "pathways"]
            },
            "Energie": {
                "color": "#F44336",
                "themes": ["vitality", "power", "strength", "dynamic action", "passion", "life force"],
                "visual_elements": ["fire", "lightning", "sunrise", "athletic movements", "vibrant energy", "dynamic poses"]
            },
            "Kreativität": {
                "color": "#FFD700",
                "themes": ["innovation", "inspiration", "artistic expression", "imagination", "creativity", "originality"],
                "visual_elements": ["paint brushes", "artistic tools", "colorful palettes", "creative chaos", "light bulbs", "artistic studios"]
            },
            "Erfolg": {
                "color": "#CC0066",
                "themes": ["achievement", "fulfillment", "manifestation", "goals", "success", "accomplishment"],
                "visual_elements": ["peaks", "trophies", "celebrations", "achievements", "upward arrows", "victory poses"]
            },
            "Entspannung": {
                "color": "#4CAF50",
                "themes": ["peace", "balance", "harmony", "rest", "tranquility", "inner calm"],
                "visual_elements": ["nature", "zen gardens", "peaceful water", "soft lighting", "meditation poses", "serene landscapes"]
            },
            "Umsicht": {
                "color": "#9C27B0",
                "themes": ["wisdom", "reflection", "strategic thinking", "mindfulness", "careful planning", "deep insight"],
                "visual_elements": ["wise figures", "thoughtful poses", "libraries", "contemplative settings", "chess pieces", "ancient symbols"]
            }
        }
    
    def _load_generated_content(self) -> Dict[str, Any]:
        """Load previously generated content"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading content storage: {e}")
        return {"prompts": [], "images": [], "by_instagram_post": {}}
    
    def _save_generated_content(self):
        """Save generated content to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.generated_content, f, indent=2)
        except Exception as e:
            print(f"Error saving content: {e}")
    
    def _create_prompt_agent(self) -> Agent:
        """Create the AI prompt generation agent"""
        return Agent(
            role="Instagram AI Image Prompt Creator",
            goal="Analyze complete Instagram posts and create intelligent DALL-E prompts that capture the essence of the post content, hashtags, and 7 Cycles period energy",
            backstory="""
            You are an expert AI prompt engineer specializing in the 7 Cycles system and Instagram content.
            You have deep understanding of:
            - How to analyze Instagram post text, hashtags, and call-to-actions to extract visual themes
            - The unique energy and visual representation of each 7 Cycles period
            - DALL-E prompt optimization for creating spiritually resonant and aesthetically pleasing images
            - Converting textual content into compelling visual concepts
            - Creating prompts that result in Instagram-worthy, professional quality images
            
            Your expertise includes:
            - Extracting key visual themes from hashtag collections
            - Understanding the emotional tone and energy of Instagram posts
            - Creating prompts that balance spiritual/personal development themes with visual appeal
            - Incorporating period-specific colors and elements naturally into image concepts
            - Ensuring generated images will work well as backgrounds for affirmation text overlays
            """,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm
        )
    
    def generate_ai_image_from_instagram_post(self, instagram_post_data: Dict[str, Any], 
                                            post_format: str = "post", image_style: str = "inspirational") -> Dict[str, Any]:
        """Generate an AI image based on complete Instagram post data"""
        try:
            # Extract data from Instagram post
            post_text = instagram_post_data.get("instagram_post_text", "")
            hashtags = instagram_post_data.get("instagram_hashtags", "")
            call_to_action = instagram_post_data.get("instagram_cta", "")
            period_name = instagram_post_data.get("period", "")
            affirmation = instagram_post_data.get("text", "")
            instagram_style = instagram_post_data.get("instagram_style", "inspirational")
            
            # Get period information
            period_info = self.period_info.get(period_name, {})
            
            # Check for existing content
            content_hash = hashlib.md5(f"{post_text}_{hashtags}_{period_name}_{image_style}".encode()).hexdigest()
            existing = self.generated_content.get("by_instagram_post", {}).get(content_hash)
            
            if existing:
                return {
                    "success": True,
                    "image": existing,
                    "source": "existing",
                    "message": f"Existing AI image for Instagram post retrieved"
                }
            
            # Create task for AI prompt generation
            task = Task(
                description=f"""
                Analyze this complete Instagram post and create a detailed DALL-E prompt for generating a background image:

                INSTAGRAM POST CONTENT:
                Post Text: "{post_text}"
                Hashtags: "{hashtags}"
                Call-to-Action: "{call_to_action}"
                Core Affirmation: "{affirmation}"
                Instagram Style: "{instagram_style}"
                
                7 CYCLES PERIOD INFORMATION:
                Period: {period_name}
                Period Color: {period_info.get('color', '#000000')}
                Period Themes: {', '.join(period_info.get('themes', []))}
                Visual Elements: {', '.join(period_info.get('visual_elements', []))}
                
                POST FORMAT: {post_format} ({"Instagram Post 4:5 ratio" if post_format == "post" else "Instagram Story 9:16 ratio"})
                IMAGE STYLE: {image_style}
                
                REQUIREMENTS:
                1. Analyze the complete Instagram content to understand the overall message and energy
                2. Extract visual themes from the hashtags collection
                3. Incorporate the period-specific color ({period_info.get('color', '#000000')}) naturally
                4. Create a prompt that results in a background suitable for text overlay
                5. Ensure the image supports the spiritual/personal development theme
                6. Make it Instagram-worthy and aesthetically pleasing
                
                Create a detailed DALL-E prompt (max 400 characters) that captures:
                - The essence of the Instagram post content
                - Key themes from the hashtags
                - The period's energy and color scheme
                - Visual elements that support the affirmation
                - Professional, inspiring aesthetic suitable for social media
                
                Format the response as JSON:
                {{
                    "dalle_prompt": "Detailed DALL-E prompt here",
                    "visual_themes": ["theme1", "theme2", "theme3"],
                    "color_palette": ["{period_info.get('color', '#000000')}", "complementary_color1", "complementary_color2"],
                    "image_description": "Brief description of expected image result",
                    "period_name": "{period_name}",
                    "instagram_analysis": "Brief analysis of what made this prompt based on the Instagram content"
                }}
                """,
                expected_output="JSON formatted DALL-E prompt with analysis and visual specifications",
                agent=self.prompt_agent
            )
            
            # Create and execute crew
            crew = Crew(
                agents=[self.prompt_agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                prompt_data = json.loads(str(result))
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                prompt_data = {
                    "dalle_prompt": self._create_fallback_prompt(period_name, affirmation, period_info),
                    "visual_themes": period_info.get('themes', [])[:3],
                    "color_palette": [period_info.get('color', '#000000'), "#FFFFFF", "#F5F5F5"],
                    "image_description": f"AI generated image for {period_name} period with {affirmation}",
                    "period_name": period_name,
                    "instagram_analysis": "Fallback prompt generated due to parsing error"
                }
            
            # Generate the actual image using DALL-E
            dalle_prompt = prompt_data.get("dalle_prompt", "")
            image_result = self.image_generator.generate_image(
                prompt=dalle_prompt,
                size="1024x1024",  # DALL-E 3 standard size
                style=image_style
            )
            
            if not image_result.get("success"):
                return {
                    "success": False,
                    "error": image_result.get("error", "Failed to generate image"),
                    "message": "Error generating AI image"
                }
            
            # Add metadata
            prompt_data["created_at"] = datetime.now().isoformat()
            prompt_data["id"] = content_hash
            prompt_data["image_url"] = image_result.get("image_url")
            prompt_data["image_path"] = image_result.get("image_path")
            prompt_data["post_format"] = post_format
            prompt_data["image_style"] = image_style
            prompt_data["instagram_post_data"] = instagram_post_data
            
            # Store the generated content
            self.generated_content["images"].append(prompt_data)
            self.generated_content["by_instagram_post"][content_hash] = prompt_data
            self._save_generated_content()
            
            return {
                "success": True,
                "image": prompt_data,
                "source": "generated",
                "message": f"AI image for {period_name} Instagram post successfully generated"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error generating AI image from Instagram post"
            }
    
    def _create_fallback_prompt(self, period_name: str, affirmation: str, period_info: Dict[str, Any]) -> str:
        """Create a fallback prompt if the main generation fails"""
        color = period_info.get('color', '#000000')
        themes = ', '.join(period_info.get('themes', [])[:2])
        visual_elements = ', '.join(period_info.get('visual_elements', [])[:2])
        
        return f"A beautiful, inspiring {period_name.lower()} themed background with {visual_elements}, {themes}, soft lighting, peaceful atmosphere, suitable for affirmation text overlay, {color} color scheme, professional photography style, spiritual and uplifting mood"
    
    def get_generated_images(self, period_name: str = None) -> Dict[str, Any]:
        """Get all generated AI images, optionally filtered by period"""
        try:
            if period_name:
                filtered_images = [
                    img for img in self.generated_content.get("images", [])
                    if img.get("period_name") == period_name
                ]
            else:
                filtered_images = self.generated_content.get("images", [])
            
            return {
                "success": True,
                "images": filtered_images,
                "count": len(filtered_images),
                "period_name": period_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }