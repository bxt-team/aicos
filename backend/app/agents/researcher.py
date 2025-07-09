from crewai import Agent
from crewai_tools import DirectoryReadTool, FileReadTool
from textwrap import dedent

class ResearcherAgent:
    def __init__(self):
        self.directory_tool = DirectoryReadTool(directory='knowledge/')
        self.file_read_tool = FileReadTool()
    
    def create_agent(self):
        return Agent(
            role="Content Researcher",
            goal="Extract and analyze relevant information from knowledge files to identify affirmation themes for the 7 periods of the 7 Cycles app",
            backstory=dedent("""
                You are an expert researcher specializing in the 7 Cycles system. You have 
                deep knowledge of the 7 periods: Image (#DAA520), Change (#2196F3), Energy (#F44336), 
                Creativity (#FFD700), Success (#CC0066), Relaxation (#4CAF50), and Prudence (#9C27B0). 
                You analyze knowledge files to extract key themes and concepts for each period 
                to create personalized affirmations that align with each period's unique energy.
            """),
            tools=[self.directory_tool, self.file_read_tool],
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def get_tasks(self):
        return [
            {
                "description": dedent("""
                    Analyze the knowledge files in the knowledge directory to extract key themes and concepts for each of the 7 periods 
                    of the 7 Cycles system. Use the DirectoryReadTool to explore the directory and FileReadTool to read individual files.
                    
                    Focus on:
                    1. Use DirectoryReadTool to list all files in the knowledge directory
                    2. Read the introduction files (01_introduction_en.txt through 06_lifecyle_en.txt) for context
                    3. Extract core themes from each period's knowledge file (07_image_en.txt through 13_prudence_en.txt)
                    4. Identify the unique characteristics and energy of each period
                    5. Find key concepts that would make powerful affirmations for each period
                    6. Understand the emotional and spiritual aspects of each period
                    7. Analyze the holistic development approach of the 7 Cycles system
                    
                    Your research should result in a comprehensive analysis that includes:
                    - Core themes for each of the 7 periods
                    - Unique characteristics of each period's energy
                    - Key concepts suitable for affirmation generation
                    - Emotional and spiritual development aspects
                    - Color associations for each period
                """),
                "expected_output": dedent("""
                    A detailed research report containing:
                    - Core themes and concepts for each of the 7 periods:
                      * Image (#DAA520): Recognition, professional development, self-presentation
                      * Change (#2196F3): Transformation, flexibility, growth
                      * Energy (#F44336): Dynamic power, strength, achievement
                      * Creativity (#FFD700): Innovation, artistic expression, openness
                      * Success (#CC0066): Holistic achievement, fulfillment, authentic living
                      * Relaxation (#4CAF50): Well-being, balance, harmony
                      * Prudence (#9C27B0): Conscious action, reflection, strategic planning
                    - Key affirmation themes for each period
                    - Emotional and spiritual development aspects
                    - Unique characteristics of each period's energy
                    - Color symbolism and associations for each period
                """),
                "agent": "researcher"
            }
        ]