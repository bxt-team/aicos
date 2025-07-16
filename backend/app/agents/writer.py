from crewai import Agent
from textwrap import dedent
from app.core.storage import StorageFactory
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import re

class WriterAgent:
    def __init__(self):
        # Initialize storage adapter
        self.storage = StorageFactory.get_adapter()
        self.collection = "content_items"
    
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
    
    async def save_generated_content(self, content_type: str, content: str, period: int, theme: str, metadata: Dict[str, Any] = None) -> str:
        """Save generated content to Supabase"""
        try:
            data = {
                "content_type": content_type,
                "title": f"{theme} - Period {period}",
                "content": content,
                "period": period,
                "theme": theme,
                "status": "draft",
                "metadata": metadata or {}
            }
            
            # Add generation timestamp to metadata
            data["metadata"]["generated_at"] = datetime.now().isoformat()
            data["metadata"]["generator"] = "WriterAgent"
            
            # Save to storage
            content_id = await self.storage.save(self.collection, data)
            return content_id
        except Exception as e:
            print(f"Error saving generated content: {e}")
            return ""
    
    def parse_affirmations_from_result(self, crew_result) -> Dict[str, List[Dict[str, Any]]]:
        """Parse affirmations from crew result and save to storage"""
        try:
            result_text = str(crew_result)
            affirmations_by_period = {}
            
            # Define periods with their numbers
            period_mapping = {
                "Image": 1,
                "Change": 2,
                "Energy": 3,
                "Creativity": 4,
                "Success": 5,
                "Relaxation": 6,
                "Prudence": 7
            }
            
            # Parse affirmations for each period
            for period_name, period_num in period_mapping.items():
                affirmations = []
                
                # Look for affirmations in the result text
                # This is a simple parser - adjust based on actual output format
                pattern = rf"{period_name}.*?(?=(?:{'|'.join(period_mapping.keys())})|$)"
                match = re.search(pattern, result_text, re.IGNORECASE | re.DOTALL)
                
                if match:
                    period_text = match.group(0)
                    
                    # Extract affirmations (lines that look like affirmations)
                    lines = period_text.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Simple heuristic: affirmations often start with "I am", "I have", "My", etc.
                        if line and any(line.startswith(prefix) for prefix in ["I am", "I have", "I can", "I will", "My", "I embrace", "I create"]):
                            affirmations.append({
                                "text": line,
                                "period": period_num,
                                "theme": period_name
                            })
                
                if affirmations:
                    affirmations_by_period[period_name] = affirmations
                    
                    # Save each affirmation to storage
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        for aff in affirmations:
                            loop.run_until_complete(
                                self.save_generated_content(
                                    "affirmation",
                                    aff["text"],
                                    period_num,
                                    period_name,
                                    {"source": "writer_agent", "batch_generation": True}
                                )
                            )
                    finally:
                        loop.close()
            
            return affirmations_by_period
        except Exception as e:
            print(f"Error parsing affirmations: {e}")
            return {}
    
    async def get_recent_content(self, content_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recently generated content from storage"""
        try:
            filters = {}
            if content_type:
                filters["content_type"] = content_type
            
            content = await self.storage.list(
                self.collection,
                filters=filters,
                order_by="created_at",
                order_desc=True,
                limit=limit
            )
            return content
        except Exception as e:
            print(f"Error retrieving content: {e}")
            return []