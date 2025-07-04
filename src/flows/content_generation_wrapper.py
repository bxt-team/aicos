from crewai import Crew, Task
from src.agents.researcher import ResearcherAgent
from src.agents.writer import WriterAgent
from src.agents.image_creator import ImageCreatorAgent
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
                    Analyze the knowledge files in the knowledge_files directory to identify 
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