from crewai import Crew, Flow, Task
from crewai.flow.flow import listen, start
from app.agents.researcher import ResearcherAgent
from app.agents.writer import WriterAgent
from app.agents.image_creator import ImageCreatorAgent
from textwrap import dedent
import json
import os
from typing import Dict, Any

class ContentGenerationFlow(Flow):
    def __init__(self):
        super().__init__()
        self.researcher_agent = ResearcherAgent()
        self.writer_agent = WriterAgent()
        self.image_creator_agent = ImageCreatorAgent()
        
        self.researcher = self.researcher_agent.create_agent()
        self.writer = self.writer_agent.create_agent()
        self.image_creator = self.image_creator_agent.create_agent()
    
    @start()
    def research_content_topics(self) -> Dict[str, Any]:
        """First flow: Research content topics from knowledge files"""
        research_task = Task(
            description=dedent("""
                Analyze the knowledge files in the knowledge directory to identify 
                the most compelling topics for Instagram content. Focus on:
                
                1. Extract key themes and concepts from affirmations and wellness content
                2. Identify emotional triggers and motivational elements
                3. Find trending wellness and self-improvement topics
                4. Suggest 3-5 post ideas with strong engagement potential
                5. Provide context and background for each suggested topic
                
                Your research should result in a comprehensive analysis that includes:
                - Topic relevance and engagement potential
                - Target audience appeal
                - Emotional resonance factors
                - Suggested content angles
            """),
            expected_output=dedent("""
                A detailed research report containing:
                - List of 3-5 high-potential Instagram post topics
                - Analysis of why each topic would perform well
                - Target audience insights for each topic
                - Emotional and motivational hooks identified
                - Trending aspects of wellness/self-improvement content
                - Specific content angles and approaches for each topic
            """),
            agent=self.researcher,
            output_file="research_output.md"
        )
        
        crew = Crew(
            agents=[self.researcher],
            tasks=[research_task],
            verbose=True
        )
        
        result = crew.kickoff()
        return {"research_results": result, "topics_identified": True}
    
    @listen("research_content_topics")
    def create_written_content(self, research_output: Dict[str, Any]) -> Dict[str, Any]:
        """Second flow: Create written content based on research"""
        writing_task = Task(
            description=dedent(f"""
                Based on the research findings: {research_output['research_results']}
                
                Create engaging Instagram content including:
                
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
            expected_output=dedent("""
                Complete Instagram content package including:
                - 3-5 ready-to-post captions with hooks, body, and CTAs
                - Strategic hashtag suggestions for each post
                - Visual content recommendations (colors, style, imagery)
                - Post timing and engagement strategy suggestions
                - Content variations for different audience segments
                - Engagement optimization tips for each post
            """),
            agent=self.writer,
            output_file="written_content.md"
        )
        
        crew = Crew(
            agents=[self.writer],
            tasks=[writing_task],
            verbose=True
        )
        
        result = crew.kickoff()
        return {
            "written_content": result,
            "research_results": research_output["research_results"],
            "content_created": True
        }
    
    @listen("create_written_content")
    def generate_visual_concepts(self, content_output: Dict[str, Any]) -> Dict[str, Any]:
        """Third flow: Generate visual concepts and image prompts"""
        visual_task = Task(
            description=dedent(f"""
                Create detailed image generation prompts and visual concepts for Instagram posts 
                based on the written content: {content_output['written_content']}
                
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
            expected_output=dedent("""
                Complete visual content package including:
                - 3-5 detailed DALL-E prompts for image generation
                - Color palette and style guidelines for each image
                - Typography and text overlay specifications
                - Alternative visual concepts for testing
                - Instagram optimization guidelines
                - Visual consistency recommendations across posts
                - Engagement-focused design elements
            """),
            agent=self.image_creator,
            output_file="visual_concepts.md"
        )
        
        crew = Crew(
            agents=[self.image_creator],
            tasks=[visual_task],
            verbose=True
        )
        
        result = crew.kickoff()
        return {
            "visual_concepts": result,
            "written_content": content_output["written_content"],
            "research_results": content_output["research_results"],
            "flow_completed": True
        }
    
    def run_complete_flow(self) -> Dict[str, Any]:
        """Run the complete content generation flow"""
        try:
            final_result = self.kickoff()
            return {
                "success": True,
                "data": final_result,
                "message": "Content generation flow completed successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Content generation flow failed"
            }