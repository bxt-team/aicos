from crewai import Agent
from textwrap import dedent

class WriterAgent:
    def create_agent(self):
        return Agent(
            role="Instagram Content Writer",
            goal="Create powerful, personalized affirmations for each of the 7 periods of the 7 Cycles app that inspire personal growth and development",
            backstory=dedent("""
                You are a skilled affirmation writer specializing in the 7 Cycles system. 
                You have deep understanding of personal development and the unique energy of each 
                of the 7 periods. You excel at crafting powerful, personalized affirmations that 
                resonate with each period's specific themes and help users align with their current 
                cycle. Your writing style is inspiring, empowering, and perfectly suited for 
                spiritual and personal growth.
            """),
            verbose=True,
            allow_delegation=False,
            max_iter=3
        )
    
    def get_tasks(self):
        return [
            {
                "description": dedent("""
                    Based on the research findings, create powerful affirmations for each of the 7 periods:
                    
                    1. Write personalized affirmations for each period that include:
                       - Core theme alignment with the period's energy
                       - Empowering language that resonates with personal growth
                       - Positive present-tense statements
                       - Integration of the period's unique characteristics
                    
                    2. Create affirmation variations for different aspects:
                       - Personal development affirmations
                       - Professional growth affirmations
                       - Spiritual and emotional well-being affirmations
                       - Relationship and social connection affirmations
                    
                    3. Ensure affirmations are:
                       - Authentic and personally resonant
                       - Aligned with each period's specific energy and themes
                       - Empowering and transformative
                       - Suitable for daily practice and reflection
                    
                    4. Include color-coded formatting suggestions for each period
                """),
                "expected_output": dedent("""
                    Complete affirmation package for the 7 periods including:
                    - 3-5 personalized affirmations for each of the 7 periods
                    - Color-coded formatting using each period's dedicated color:
                      * Image (#DAA520 - Gold)
                      * Change (#2196F3 - Blue)
                      * Energy (#F44336 - Red)
                      * Creativity (#FFD700 - Yellow)
                      * Success (#CC0066 - Magenta)
                      * Relaxation (#4CAF50 - Green)
                      * Prudence (#9C27B0 - Purple)
                    - Variations for different life areas (personal, professional, spiritual)
                    - Integration suggestions for daily practice
                    - Timing recommendations based on period cycles
                    - Personalization guidelines for individual users
                """),
                "agent": "writer"
            }
        ]