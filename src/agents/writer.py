from crewai import Agent
from textwrap import dedent

class WriterAgent:
    def create_agent(self):
        return Agent(
            role="Instagram Content Writer",
            goal="Create compelling, engaging Instagram captions and content that inspire, motivate, and connect with audiences",
            backstory=dedent("""
                You are a skilled social media content writer specializing in Instagram. 
                You have a deep understanding of what makes content viral and engaging on 
                Instagram. You excel at crafting captions that are authentic, motivational, 
                and optimized for maximum engagement. Your writing style is conversational, 
                inspiring, and perfectly suited for the Instagram platform.
            """),
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def get_tasks(self):
        return [
            {
                "description": dedent("""
                    Based on the research findings, create engaging Instagram content including:
                    
                    1. Write compelling captions (150-300 words) that include:
                       - Hook that grabs attention in the first line
                       - Valuable content that educates or inspires
                       - Call-to-action that encourages engagement
                       - Relevant hashtags (10-15 strategic hashtags)
                    
                    2. Create content variations for different post types:
                       - Inspirational quotes
                       - Educational carousels
                       - Personal stories/testimonials
                       - Tips and advice posts
                    
                    3. Ensure content is:
                       - Authentic and relatable
                       - Optimized for Instagram algorithm
                       - Engaging and shareable
                       - Aligned with wellness/self-improvement themes
                    
                    4. Include specific visual content suggestions for each post
                """),
                "expected_output": dedent("""
                    Complete Instagram content package including:
                    - 3-5 ready-to-post captions with hooks, body, and CTAs
                    - Strategic hashtag suggestions for each post
                    - Visual content recommendations (colors, style, imagery)
                    - Post timing and engagement strategy suggestions
                    - Content variations for different audience segments
                    - Engagement optimization tips for each post
                """),
                "agent": "writer"
            }
        ]