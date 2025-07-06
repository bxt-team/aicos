from crewai import Agent
from textwrap import dedent

class ImageCreatorAgent:
    def create_agent(self):
        return Agent(
            role="Instagram Visual Content Creator",
            goal="Generate detailed image prompts and visual concepts for affirmation posts that complement the 7 periods using their dedicated colors",
            backstory=dedent("""
                You are a creative visual content specialist with expertise in the 7 Cycles system 
                and spiritual aesthetics. You understand how to create visually compelling images 
                that embody the unique energy of each period using their dedicated colors. 
                You specialize in creating affirmation visuals that support personal growth, 
                spiritual development, and alignment with the natural cycles of life.
            """),
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def get_tasks(self):
        return [
            {
                "description": dedent("""
                    Create detailed image generation prompts and visual concepts for affirmation posts based on the 7 periods:
                    
                    1. Generate DALL-E prompts for each period that include:
                       - Period-specific color schemes using dedicated colors
                       - Visual elements that embody each period's unique energy
                       - Spiritual and growth-oriented imagery
                       - Typography that complements the period's essence
                    
                    2. Create different image types for each period:
                       - Affirmation graphics with period-specific color backgrounds
                       - Abstract spiritual concepts representing each period's energy
                       - Natural elements that align with each period's themes
                       - Geometric or mandala-style designs in period colors
                    
                    3. Ensure images are:
                       - Optimized for mobile viewing and social sharing
                       - High-quality and spiritually resonant
                       - Aligned with each period's specific energy and themes
                       - Suitable for meditation and reflection
                    
                    4. Use the dedicated colors for each period:
                       - Image (#DAA520), Change (#2196F3), Energy (#F44336)
                       - Creativity (#FFD700), Success (#CC0066), Relaxation (#4CAF50), Prudence (#9C27B0)
                """),
                "expected_output": dedent("""
                    Complete visual content package for the 7 periods including:
                    - 3-5 detailed DALL-E prompts for each period using their dedicated colors
                    - Period-specific color schemes and visual guidelines:
                      * Image (#DAA520 - Gold): Professional, recognition, achievement themes
                      * Change (#2196F3 - Blue): Transformation, flow, adaptability themes
                      * Energy (#F44336 - Red): Power, strength, dynamic action themes
                      * Creativity (#FFD700 - Yellow): Innovation, inspiration, artistic themes
                      * Success (#CC0066 - Magenta): Fulfillment, holistic achievement themes
                      * Relaxation (#4CAF50 - Green): Peace, balance, harmony themes
                      * Prudence (#9C27B0 - Purple): Wisdom, reflection, strategic themes
                    - Typography and text overlay specifications for affirmations
                    - Spiritual and growth-oriented design elements
                    - Mobile optimization guidelines for affirmation viewing
                    - Visual consistency recommendations across all 7 periods
                """),
                "agent": "image_creator"
            }
        ]