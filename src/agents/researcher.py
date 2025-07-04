from crewai import Agent
from crewai_tools import FileReadTool
from textwrap import dedent

class ResearcherAgent:
    def __init__(self):
        self.file_read_tool = FileReadTool()
    
    def create_agent(self):
        return Agent(
            role="Content Researcher",
            goal="Extract and analyze relevant information from knowledge files to identify trending topics and themes for Instagram content",
            backstory=dedent("""
                You are an expert content researcher with a keen eye for identifying 
                compelling topics that resonate with audiences. You specialize in analyzing 
                knowledge bases to find the most engaging and relevant content themes for 
                social media, particularly Instagram. Your research forms the foundation 
                for creating viral and meaningful content.
            """),
            tools=[self.file_read_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def get_tasks(self):
        return [
            {
                "description": dedent("""
                    Analyze the knowledge files in the knowledge_files directory to identify 
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
                "expected_output": dedent("""
                    A detailed research report containing:
                    - List of 3-5 high-potential Instagram post topics
                    - Analysis of why each topic would perform well
                    - Target audience insights for each topic
                    - Emotional and motivational hooks identified
                    - Trending aspects of wellness/self-improvement content
                    - Specific content angles and approaches for each topic
                """),
                "agent": "researcher"
            }
        ]