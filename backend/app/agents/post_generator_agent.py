"""Agent for generating Threads posts based on strategy and 7 Cycles content."""

import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import random

from crewai import Agent, Task, Crew
from langchain_community.llms import OpenAI
from langchain.tools import Tool

from .crews.base_crew import BaseCrew
from .affirmations_agent import AffirmationsAgent
from .qa_agent import QAAgent
from ..services.supabase_client import SupabaseClient, Activity

logger = logging.getLogger(__name__)


class PostGeneratorAgent(BaseCrew):
    """Agent that generates engaging Threads posts combining various 7 Cycles content."""
    
    def __init__(self, openai_api_key: str, supabase_client: Optional[SupabaseClient] = None):
        """Initialize the Post Generator Agent."""
        super().__init__()
        
        # Initialize LLM
        self.llm = OpenAI(
            model="gpt-4o-mini",
            openai_api_key=openai_api_key,
            temperature=0.8
        )
        
        # Initialize supporting agents
        self.affirmations_agent = AffirmationsAgent(openai_api_key)
        self.qa_agent = QAAgent(openai_api_key)
        self.supabase = supabase_client or SupabaseClient()
        
        # Storage for posts
        self.storage_dir = os.path.join(os.path.dirname(__file__), "../../static/threads_posts")
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Create agent
        self.agent = self.create_agent("threads_generator", llm=self.llm)
        
        # Create content tools
        self.affirmation_tool = Tool(
            name="get_affirmations",
            description="Get affirmations for a specific period",
            func=self._get_affirmations
        )
        
        self.activity_tool = Tool(
            name="get_activities",
            description="Get activities for a specific period or theme",
            func=self._get_activities
        )
        
        self.knowledge_tool = Tool(
            name="get_knowledge",
            description="Get 7 Cycles knowledge on a specific topic",
            func=self._get_knowledge
        )
        
        # Add tools to agent
        if hasattr(self.agent, 'tools'):
            self.agent.tools.extend([self.affirmation_tool, self.activity_tool, self.knowledge_tool])
        else:
            self.agent.tools = [self.affirmation_tool, self.activity_tool, self.knowledge_tool]
    
    def _get_affirmations(self, period: str) -> str:
        """Get affirmations for a specific period."""
        try:
            # Map period names
            period_map = {
                "1": "IMAGE", "IMAGE": "IMAGE",
                "2": "VERÄNDERUNG", "VERÄNDERUNG": "VERÄNDERUNG", "CHANGE": "VERÄNDERUNG",
                "3": "ENERGIE", "ENERGIE": "ENERGIE", "ENERGY": "ENERGIE",
                "4": "KREATIVITÄT", "KREATIVITÄT": "KREATIVITÄT", "CREATIVITY": "KREATIVITÄT",
                "5": "ERFOLG", "ERFOLG": "ERFOLG", "SUCCESS": "ERFOLG",
                "6": "ENTSPANNUNG", "ENTSPANNUNG": "ENTSPANNUNG", "RELAXATION": "ENTSPANNUNG",
                "7": "UMSICHT", "UMSICHT": "UMSICHT", "PRUDENCE": "UMSICHT"
            }
            
            period_name = period_map.get(period.upper(), "IMAGE")
            affirmations = self.affirmations_agent.get_affirmations_by_period(period_name)
            
            if affirmations:
                return json.dumps([a["affirmation"] for a in affirmations[:3]], ensure_ascii=False)
            return "[]"
        except Exception as e:
            logger.error(f"Error getting affirmations: {str(e)}")
            return "[]"
    
    async def _get_activities(self, period_or_theme: str) -> str:
        """Get activities for a specific period or theme."""
        try:
            # Check if it's a period number
            if period_or_theme.isdigit():
                activities = await self.supabase.get_activities(period=int(period_or_theme))
            else:
                # Search by tag
                activities = await self.supabase.get_activities(tags=[period_or_theme.lower()])
            
            if activities:
                return json.dumps([{
                    "title": a.title,
                    "description": a.description,
                    "period": a.period
                } for a in activities[:3]], ensure_ascii=False)
            
            # Return mock activities if no real ones found
            return json.dumps([{
                "title": "Morgenmeditation",
                "description": "Beginne den Tag mit einer 10-minütigen Meditation",
                "period": 1
            }], ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error getting activities: {str(e)}")
            return "[]"
    
    def _get_knowledge(self, topic: str) -> str:
        """Get 7 Cycles knowledge on a specific topic."""
        try:
            # Use QA agent to get knowledge
            response = self.qa_agent.answer_question(topic)
            if response and "answer" in response:
                return response["answer"][:500]  # Limit length for posts
            return "7 Cycles wisdom teaches us about the natural rhythm of life."
        except Exception as e:
            logger.error(f"Error getting knowledge: {str(e)}")
            return "7 Cycles wisdom teaches us about the natural rhythm of life."
    
    async def generate_posts(
        self,
        count: int = 5,
        strategy: Optional[Dict[str, Any]] = None,
        period: Optional[int] = None,
        theme: Optional[str] = None,
        include_affirmations: bool = True,
        include_activities: bool = True
    ) -> Dict[str, Any]:
        """Generate multiple Threads posts based on parameters."""
        try:
            # Get current period if not specified
            if period is None:
                period = self._get_current_period()
            
            # Get affirmations if requested
            affirmations = []
            if include_affirmations:
                affirmations = self._get_affirmations(str(period))
            
            # Get activities if requested
            activities = []
            if include_activities:
                activities = await self._get_activities(str(period))
            
            # Get knowledge context
            knowledge_context = self._get_knowledge(f"Period {period} wisdom")
            
            # Create generation task
            task = self.create_task(
                "threads_post_generation",
                self.agent,
                count=count,
                strategy=json.dumps(strategy, indent=2) if strategy else "Use default 7 Cycles content strategy",
                period=period,
                theme=theme or "General 7 Cycles wisdom",
                include_affirmations=include_affirmations,
                include_activities=include_activities,
                affirmations=affirmations,
                activities=activities,
                knowledge_context=knowledge_context,
                tools=[self.affirmation_tool, self.activity_tool, self.knowledge_tool]
            )
            
            # Create crew and execute
            crew = self.create_crew(
                "threads_generation_crew",
                agents=[self.agent],
                tasks=[task]
            )
            
            result = crew.kickoff()
            
            # Parse and structure posts
            posts = self._parse_posts_result(result, period)
            
            # Save posts
            self._save_posts(posts)
            
            # Store in Supabase
            await self._store_posts_in_db(posts)
            
            return {
                "success": True,
                "posts": posts,
                "count": len(posts),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating posts: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "posts": []
            }
    
    def _get_current_period(self) -> int:
        """Calculate current period based on date."""
        # Simple calculation - in reality this would be based on user's cycle
        day_of_year = datetime.now().timetuple().tm_yday
        return ((day_of_year - 1) % 49 // 7) + 1
    
    def _parse_posts_result(self, result: Any, period: int) -> List[Dict[str, Any]]:
        """Parse the crew result into structured posts."""
        posts = []
        
        try:
            # Generate sample posts if parsing fails
            default_posts = self._generate_default_posts(period)
            
            if hasattr(result, 'output'):
                # Try to parse JSON from output
                try:
                    content = result.output
                    if isinstance(content, str):
                        # Extract JSON if embedded in text
                        import re
                        json_match = re.search(r'\[.*\]', content, re.DOTALL)
                        if json_match:
                            posts_data = json.loads(json_match.group())
                            for post_data in posts_data:
                                posts.append(self._format_post(post_data, period))
                        else:
                            posts = default_posts
                    elif isinstance(content, list):
                        for post_data in content:
                            posts.append(self._format_post(post_data, period))
                except:
                    posts = default_posts
            else:
                posts = default_posts
                
        except Exception as e:
            logger.error(f"Error parsing posts: {str(e)}")
            posts = self._generate_default_posts(period)
        
        return posts
    
    def _format_post(self, post_data: Dict[str, Any], period: int) -> Dict[str, Any]:
        """Format a single post with all required fields."""
        return {
            "content": post_data.get("content", ""),
            "hashtags": post_data.get("hashtags", self._get_default_hashtags(period)),
            "period": post_data.get("period", period),
            "visual_prompt": post_data.get("visual_prompt", f"Minimalist design for period {period}"),
            "post_type": post_data.get("post_type", "wisdom"),
            "call_to_action": post_data.get("call_to_action", "Was ist deine Erfahrung? Teile sie mit uns! 💫"),
            "created_at": datetime.now().isoformat()
        }
    
    def _generate_default_posts(self, period: int) -> List[Dict[str, Any]]:
        """Generate default posts as fallback."""
        period_names = {
            1: "IMAGE", 2: "VERÄNDERUNG", 3: "ENERGIE",
            4: "KREATIVITÄT", 5: "ERFOLG", 6: "ENTSPANNUNG", 7: "UMSICHT"
        }
        
        period_name = period_names.get(period, "IMAGE")
        
        return [
            {
                "content": f"🌟 Periode {period}: {period_name}\n\nJede Phase unseres Lebens hat ihre eigene Energie und Weisheit. In der {period_name}-Phase geht es darum, diese Kraft bewusst zu nutzen.\n\nWelche Energie spürst du gerade in deinem Leben?",
                "hashtags": ["#7Cycles", f"#{period_name}", "#Lebensrhythmus", "#Spiritualität", "#Transformation"],
                "period": period,
                "visual_prompt": f"Minimalist spiritual design representing {period_name} energy",
                "post_type": "educational",
                "call_to_action": "Teile deine Gedanken in den Kommentaren! 💬"
            },
            {
                "content": f"✨ Tagesaffirmation für {period_name}:\n\n'Ich bin im Einklang mit meinem natürlichen Rhythmus und nutze die Kraft dieser Phase für mein Wachstum.'\n\nWiederhole diese Affirmation heute dreimal und spüre die Veränderung.",
                "hashtags": ["#Affirmation", f"#{period_name}", "#7Zyklen", "#Selbstliebe", "#TäglichePraxis"],
                "period": period,
                "visual_prompt": f"Calming nature scene with affirmation text overlay",
                "post_type": "affirmation",
                "call_to_action": "Speichere diesen Post für deine tägliche Praxis! 🔖"
            },
            {
                "content": f"🎯 Aktivität für heute:\n\nNimm dir 10 Minuten Zeit für eine {period_name}-Meditation. Setze dich ruhig hin, atme tief und visualisiere die Energie dieser Phase in deinem Leben.\n\nBereit für diese kraftvolle Übung?",
                "hashtags": ["#Meditation", "#7CyclesAktivität", f"#{period_name}", "#Achtsamkeit", "#DailyPractice"],
                "period": period,
                "visual_prompt": f"Person meditating with {period_name} energy visualization",
                "post_type": "activity",
                "call_to_action": "Probiere es aus und berichte von deiner Erfahrung! 🧘‍♀️"
            }
        ]
    
    def _get_default_hashtags(self, period: int) -> List[str]:
        """Get default hashtags for a period."""
        period_hashtags = {
            1: ["#IMAGE", "#Selbstbild", "#Identität"],
            2: ["#VERÄNDERUNG", "#Transformation", "#Wandel"],
            3: ["#ENERGIE", "#Vitalität", "#Kraft"],
            4: ["#KREATIVITÄT", "#Inspiration", "#Schöpfung"],
            5: ["#ERFOLG", "#Manifestation", "#Ziele"],
            6: ["#ENTSPANNUNG", "#Ruhe", "#Balance"],
            7: ["#UMSICHT", "#Weisheit", "#Planung"]
        }
        
        base_hashtags = ["#7Cycles", "#7Zyklen", "#Lebensrhythmus"]
        return base_hashtags + period_hashtags.get(period, ["#Spiritualität"])
    
    def _save_posts(self, posts: List[Dict[str, Any]]):
        """Save posts to storage."""
        filename = f"posts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
        
        # Also save as latest
        latest_path = os.path.join(self.storage_dir, "latest_posts.json")
        with open(latest_path, 'w') as f:
            json.dump(posts, f, indent=2, ensure_ascii=False)
    
    async def _store_posts_in_db(self, posts: List[Dict[str, Any]]):
        """Store generated posts in Supabase."""
        try:
            for post in posts:
                await self.supabase.create_threads_post({
                    "content": post["content"],
                    "tags": post["hashtags"],
                    "period": post["period"],
                    "visual_prompt": post.get("visual_prompt"),
                    "status": "draft"
                })
        except Exception as e:
            logger.error(f"Error storing posts in database: {str(e)}")
    
    def get_latest_posts(self) -> Optional[List[Dict[str, Any]]]:
        """Retrieve the latest generated posts."""
        latest_path = os.path.join(self.storage_dir, "latest_posts.json")
        
        if os.path.exists(latest_path):
            with open(latest_path, 'r') as f:
                return json.load(f)
        
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check agent health status."""
        return {
            "status": "healthy",
            "agent": "PostGeneratorAgent",
            "storage_available": os.path.exists(self.storage_dir),
            "latest_posts": self.get_latest_posts() is not None,
            "supporting_agents": {
                "affirmations": hasattr(self, 'affirmations_agent'),
                "qa": hasattr(self, 'qa_agent'),
                "supabase": self.supabase.client is not None
            }
        }