from crewai import Agent
from textwrap import dedent

class ImageCreatorAgent:
    def create_agent(self):
        return Agent(
            role="Instagram Visual Content Creator",
            goal="Generate detailed image prompts and visual concepts for Instagram posts that complement the written content",
            backstory=dedent("""
                You are a creative visual content specialist with expertise in Instagram 
                aesthetics and visual storytelling. You understand how to create visually 
                compelling images that stop users from scrolling and encourage engagement. 
                You specialize in wellness, self-improvement, and motivational content 
                imagery that resonates with audiences seeking personal growth.
            """),
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def get_tasks(self):
        return [
            {
                "description": dedent("""
                    Create detailed image generation prompts and visual concepts for Instagram posts based on the written content:
                    
                    1. Generate DALL-E prompts for each post that include:
                       - Clear visual style guidelines (minimalist, warm, professional)
                       - Color palette suggestions (calming, energizing, earth tones)
                       - Composition elements (typography, imagery, layout)
                       - Mood and atmosphere specifications
                    
                    2. Create different image types:
                       - Quote graphics with beautiful typography
                       - Lifestyle/wellness scenes
                       - Abstract concepts representing growth/wellness
                       - Motivational/inspirational imagery
                    
                    3. Ensure images are:
                       - Instagram-optimized (square 1:1 or 4:5 ratio)
                       - High-quality and professional
                       - Aligned with wellness/self-improvement aesthetics
                       - Engaging and scroll-stopping
                    
                    4. Provide alternative visual concepts for A/B testing
                """),
                "expected_output": dedent("""
                    Complete visual content package including:
                    - 3-5 detailed DALL-E prompts for image generation
                    - Color palette and style guidelines for each image
                    - Typography and text overlay specifications
                    - Alternative visual concepts for testing
                    - Instagram optimization guidelines
                    - Visual consistency recommendations across posts
                    - Engagement-focused design elements
                """),
                "agent": "image_creator"
            }
        ]