from crewai import Crew, Task
from app.agents.researcher import ResearcherAgent
from app.agents.writer import WriterAgent
from app.agents.image_creator import ImageCreatorAgent
from textwrap import dedent
import os
from typing import Dict, Any

class ContentGenerationWrapper:
    """Wrapper for CrewAI content generation without using Flow to avoid async issues"""
    
    def __init__(self):
        self.researcher_agent = ResearcherAgent()
        self.writer_agent = WriterAgent()
        self.image_creator_agent = ImageCreatorAgent()
        
        self.researcher = self.researcher_agent.create_agent()
        self.writer = self.writer_agent.create_agent()
        self.image_creator = self.image_creator_agent.create_agent()
    
    def run_sequential_generation(self) -> Dict[str, Any]:
        """Run content generation tasks sequentially"""
        try:
            # Task 1: Research
            research_task = Task(
                description=dedent("""
                    Analyze the knowledge files in the knowledge directory to identify 
                    the most compelling topics for Instagram content. Focus on:
                    
                    1. Extract key themes and concepts from affirmations and wellness content
                    2. Identify emotional triggers and motivational elements
                    3. Find trending wellness and self-improvement topics
                    4. Suggest 3-5 post ideas with strong engagement potential
                    5. Provide context and background for each suggested topic
                """),
                expected_output=dedent("""
                    A detailed research report containing:
                    - List of 3-5 high-potential Instagram post topics
                    - Analysis of why each topic would perform well
                    - Target audience insights for each topic
                """),
                agent=self.researcher
            )
            
            research_crew = Crew(
                agents=[self.researcher],
                tasks=[research_task],
                verbose=True
            )
            
            research_result = research_crew.kickoff()
            
            # Task 2: Writing
            writing_task = Task(
                description=dedent(f"""
                    Based on the research findings: {research_result}
                    
                    Create engaging Instagram content including:
                    
                    1. Write compelling captions (150-300 words) that include:
                       - Hook that grabs attention in the first line
                       - Valuable content that educates or inspires
                       - Call-to-action that encourages engagement
                       - Relevant hashtags (10-15 strategic hashtags)
                    
                    2. Ensure content is:
                       - Authentic and relatable
                       - Optimized for Instagram algorithm
                       - Engaging and shareable
                """),
                expected_output=dedent("""
                    Complete Instagram content package including:
                    - 3-5 ready-to-post captions with hooks, body, and CTAs
                    - Strategic hashtag suggestions for each post
                    - Visual content recommendations
                """),
                agent=self.writer
            )
            
            writing_crew = Crew(
                agents=[self.writer],
                tasks=[writing_task],
                verbose=True
            )
            
            writing_result = writing_crew.kickoff()
            
            # Task 3: Visual Concepts
            visual_task = Task(
                description=dedent(f"""
                    Create detailed image generation prompts and visual concepts for Instagram posts 
                    based on the written content: {writing_result}
                    
                    1. Generate DALL-E prompts for each post that include:
                       - Clear visual style guidelines
                       - Color palette suggestions
                       - Composition elements
                       - Mood and atmosphere specifications
                    
                    2. Ensure images are:
                       - Instagram-optimized (square 1:1 or 4:5 ratio)
                       - High-quality and professional
                       - Aligned with wellness/self-improvement aesthetics
                """),
                expected_output=dedent("""
                    Complete visual content package including:
                    - 3-5 detailed DALL-E prompts for image generation
                    - Color palette and style guidelines for each image
                    - Instagram optimization guidelines
                """),
                agent=self.image_creator
            )
            
            visual_crew = Crew(
                agents=[self.image_creator],
                tasks=[visual_task],
                verbose=True
            )
            
            visual_result = visual_crew.kickoff()
            
            return {
                "success": True,
                "data": {
                    "research_results": str(research_result),
                    "written_content": str(writing_result),
                    "visual_concepts": str(visual_result),
                    "flow_completed": True
                },
                "message": "Content generation completed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Content generation failed"
            }
    
    def create_visual_post_from_ai_image(self, visual_post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a visual post from AI-generated image data"""
        try:
            import json
            import hashlib
            import datetime
            
            # Generate unique ID for the visual post
            unique_string = f"{visual_post_data['text']}_{visual_post_data['period']}_{visual_post_data['image_style']}_{datetime.datetime.now().isoformat()}"
            post_id = hashlib.md5(unique_string.encode()).hexdigest()
            
            # Get AI image data
            ai_image_data = visual_post_data['ai_image_data']
            
            # Create visual post entry
            visual_post = {
                "id": post_id,
                "text": visual_post_data['text'],
                "period": visual_post_data['period'],
                "tags": visual_post_data.get('tags', []),
                "period_color": self._get_period_color(visual_post_data['period']),
                "image_style": visual_post_data['image_style'],
                "post_format": visual_post_data.get('post_format', 'post'),
                "file_path": ai_image_data.get('image_path'),
                "file_url": f"/static/generated/{os.path.basename(ai_image_data.get('image_path', ''))}",
                "background_image": {
                    "id": "ai_generated",
                    "photographer": "DALL-E AI",
                    "pexels_url": "https://openai.com/dall-e-3"
                },
                "ai_generated": True,
                "ai_image_data": ai_image_data,
                "created_at": datetime.datetime.now().isoformat(),
                "dimensions": {
                    "width": 1024,
                    "height": 1024
                }
            }
            
            # Load existing visual posts storage
            storage_file = os.path.join(os.path.dirname(__file__), "../../static/visual_posts_storage.json")
            storage_data = {"posts": [], "by_period": {}}
            
            if os.path.exists(storage_file):
                with open(storage_file, 'r') as f:
                    storage_data = json.load(f)
            
            # Add new post to storage
            storage_data["posts"].append(visual_post)
            storage_data["by_period"][post_id] = visual_post
            
            # Save storage
            os.makedirs(os.path.dirname(storage_file), exist_ok=True)
            with open(storage_file, 'w') as f:
                json.dump(storage_data, f, indent=2)
            
            return {
                "success": True,
                "post": visual_post,
                "message": "Visual post created from AI image"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_period_color(self, period: str) -> str:
        """Get color for period"""
        period_colors = {
            "Image": "#DAA520",
            "Veränderung": "#2196F3",
            "Energie": "#F44336",
            "Kreativität": "#FFD700",
            "Erfolg": "#4CAF50",
            "Entspannung": "#9C27B0",
            "Umsicht": "#FF9800"
        }
        return period_colors.get(period, "#000000")