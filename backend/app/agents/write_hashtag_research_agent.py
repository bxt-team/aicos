from crewai import Agent, Task, Crew
from crewai.llm import LLM
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import uuid
from app.agents.crews.base_crew import BaseCrew
from app.services.knowledge_base_manager import knowledge_base_manager
from app.services.supabase_client import SupabaseClient
from app.core.storage import StorageFactory
import asyncio
import logging

logger = logging.getLogger(__name__)

class WriteHashtagResearchAgent(BaseCrew):
    def __init__(self, openai_api_key: str):
        # Get storage adapter from factory for multi-tenant support
        storage_adapter = StorageFactory.get_adapter()
        super().__init__(storage_adapter=storage_adapter)
        
        self.openai_api_key = openai_api_key
        # Use shared embeddings and vector store
        self.embeddings = knowledge_base_manager.get_embeddings()
        self.vector_store = knowledge_base_manager.get_vector_store()
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Collection name for hashtag research
        self.collection = "instagram_posts"
        
        # Initialize Supabase client for backward compatibility
        self.supabase = SupabaseClient()
        
        # Create the agent
        self.write_hashtag_agent = self._create_write_hashtag_agent()
    
    async def _save_to_database(self, post_data: Dict[str, Any]) -> Optional[str]:
        """Save Instagram post to multi-tenant storage"""
        try:
            # Prepare data for storage
            storage_data = {
                "content": post_data.get("post_text", ""),
                "hashtags": post_data.get("hashtags", []),
                "post_type": "feed",  # default to feed post
                "status": "draft",
                "call_to_action": post_data.get("call_to_action", ""),
                "engagement_strategies": post_data.get("engagement_strategies", []),
                "optimal_posting_time": post_data.get("optimal_posting_time", ""),
                "period_name": post_data.get("period_name", ""),
                "period_color": post_data.get("period_color", ""),
                "affirmation": post_data.get("affirmation", ""),
                "style": post_data.get("style", ""),
                "content_hash": post_data.get("id", "")
            }
            
            # Save to multi-tenant storage
            if self.validate_context():
                post_id = await self.save_result(self.collection, storage_data)
            else:
                post_id = await self.storage_adapter.save(self.collection, storage_data)
            
            return post_id
            
        except Exception as e:
            logger.error(f"Error saving to storage: {e}")
            return None
    
    async def _get_from_database(self, content_hash: str = None) -> List[Dict[str, Any]]:
        """Get Instagram posts from multi-tenant storage"""
        try:
            # Build filters
            filters = {}
            if content_hash:
                filters["content_hash"] = content_hash
            
            # Get from multi-tenant storage
            if self.validate_context():
                posts = await self.list_results(
                    self.collection,
                    filters=filters,
                    order_by="created_at",
                    order_desc=True
                )
            else:
                posts = await self.storage_adapter.list(
                    self.collection,
                    filters=filters,
                    order_by="created_at",
                    order_desc=True
                )
            
            # Transform storage format to expected format
            formatted_posts = []
            for item in posts:
                post = {
                    "id": item.get("content_hash", item.get("id")),
                    "post_text": item.get("content", ""),
                    "hashtags": item.get("hashtags", []),
                    "call_to_action": item.get("call_to_action", ""),
                    "engagement_strategies": item.get("engagement_strategies", []),
                    "optimal_posting_time": item.get("optimal_posting_time", ""),
                    "period_name": item.get("period_name", ""),
                    "period_color": item.get("period_color", ""),
                    "affirmation": item.get("affirmation", ""),
                    "style": item.get("style", ""),
                    "created_at": item.get("created_at", ""),
                    "db_id": item.get("id")
                }
                posts.append(post)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            return []
    
    def _create_write_hashtag_agent(self) -> Agent:
        """Create the Write and Hashtag Research agent"""
        return Agent(
            role="Instagram Post & Hashtag TextWriter",
            goal="Create engaging Instagram posts with affirmations for 7 Cycles periods, including relevant hashtags and call-to-actions to grow follower base",
            backstory="""
            You are a skilled Instagram content creator and hashtag research expert specializing in the 7 Cycles system. 
            You have deep understanding of:
            - Personal development and the unique energy of each of the 7 periods
            - Instagram content creation best practices
            - Hashtag research and optimization for maximum reach
            - Creating compelling call-to-actions that drive engagement
            - Building authentic connections with spiritual and personal growth communities
            
            Your expertise includes:
            - Crafting posts that resonate with each period's specific themes
            - Research trending and relevant hashtags for personal development content
            - Creating authentic call-to-actions that encourage meaningful engagement
            - Understanding Instagram algorithm preferences for spiritual/wellness content
            - Balancing inspirational content with community building
            """,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm
        )
    
    def _get_period_context(self, period_name: str) -> str:
        """Get relevant context for a specific 7 Cycles period"""
        if not self.vector_store:
            return "Knowledge base not available"
        
        try:
            # Period-specific search queries
            period_queries = {
                "Image": "image selbstbild identität wahrnehmung ausstrahlung selbstvertrauen authentizität",
                "Veränderung": "veränderung transformation wandel anpassung neubeginn flexibilität wachstum",
                "Energie": "energie vitalität schwung dynamik kraft motivation ausdauer lebenskraft",
                "Kreativität": "kreativität innovation inspiration schöpfung künstlerisch kreativ entfaltung",
                "Erfolg": "erfolg zielerreichung leistung manifestation erfolgreich ziele erreichen",
                "Entspannung": "entspannung ruhe regeneration balance frieden gelassenheit erholung",
                "Umsicht": "umsicht weisheit besonnenheit planung entscheidungen weise strategisch"
            }
            
            query = period_queries.get(period_name, "7 cycles lebenszyklen energie kreativität erfolg")
            
            # Retrieve relevant documents
            docs = self.vector_store.similarity_search(query, k=3)
            
            # Combine context
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
            
        except Exception as e:
            print(f"Error retrieving period context: {e}")
            return "Error retrieving context"
    
    def _get_period_info(self, period_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific 7 Cycles period"""
        periods_info = {
            "Image": {
                "description": "Selbstbild, Identität und persönliche Ausstrahlung",
                "color": "#DAA520",
                "focus": "Selbstvertrauen, Authentizität, Selbstliebe",
                "keywords": ["selbstbild", "identität", "authentizität", "selbstvertrauen", "ausstrahlung"],
                "hashtags": ["#selbstbild", "#identität", "#authentizität", "#selbstvertrauen", "#persönlichkeitsentwicklung"]
            },
            "Veränderung": {
                "description": "Transformation, Wandel und Anpassung",
                "color": "#2196F3",
                "focus": "Mut zur Veränderung, Flexibilität, Wachstum",
                "keywords": ["veränderung", "transformation", "wandel", "neubeginn", "wachstum"],
                "hashtags": ["#veränderung", "#transformation", "#wandel", "#neubeginn", "#wachstum"]
            },
            "Energie": {
                "description": "Vitalität, Schwung und dynamische Kraft",
                "color": "#F44336",
                "focus": "Lebenskraft, Motivation, Ausdauer",
                "keywords": ["energie", "vitalität", "kraft", "motivation", "lebenskraft"],
                "hashtags": ["#energie", "#vitalität", "#kraft", "#motivation", "#lebenskraft"]
            },
            "Kreativität": {
                "description": "Innovation, Inspiration und schöpferischer Ausdruck",
                "color": "#FFD700",
                "focus": "Kreative Entfaltung, Inspiration, Innovation",
                "keywords": ["kreativität", "innovation", "inspiration", "schöpfung", "künstlerisch"],
                "hashtags": ["#kreativität", "#innovation", "#inspiration", "#schöpfung", "#künstlerisch"]
            },
            "Erfolg": {
                "description": "Zielerreichung, Leistung und Manifestation",
                "color": "#CC0066",
                "focus": "Ziele erreichen, Erfolg manifestieren, Leistung",
                "keywords": ["erfolg", "ziele", "manifestation", "leistung", "zielerreichung"],
                "hashtags": ["#erfolg", "#ziele", "#manifestation", "#leistung", "#zielerreichung"]
            },
            "Entspannung": {
                "description": "Ruhe, Regeneration und innere Balance",
                "color": "#4CAF50",
                "focus": "Gelassenheit, Erholung, innere Ruhe",
                "keywords": ["entspannung", "ruhe", "balance", "gelassenheit", "erholung"],
                "hashtags": ["#entspannung", "#ruhe", "#balance", "#gelassenheit", "#erholung"]
            },
            "Umsicht": {
                "description": "Weisheit, Besonnenheit und durchdachte Planung",
                "color": "#9C27B0",
                "focus": "Weisheit, kluge Entscheidungen, strategisches Denken",
                "keywords": ["umsicht", "weisheit", "besonnenheit", "planung", "entscheidungen"],
                "hashtags": ["#umsicht", "#weisheit", "#besonnenheit", "#planung", "#weiseentscheidungen"]
            }
        }
        
        return periods_info.get(period_name, {})
    
    async def generate_instagram_post(self, affirmation: str, period_name: str, style: str = "inspirational") -> Dict[str, Any]:
        """Generate an Instagram post with affirmation, hashtags, and call-to-action"""
        try:
            # Validate period name
            valid_periods = ["Image", "Veränderung", "Energie", "Kreativität", "Erfolg", "Entspannung", "Umsicht"]
            if period_name not in valid_periods:
                return {
                    "success": False,
                    "error": f"Invalid period: {period_name}. Available periods: {valid_periods}",
                    "message": "Invalid 7 Cycles period"
                }
            
            # Get period information and context
            period_info = self._get_period_info(period_name)
            context = self._get_period_context(period_name)
            
            # Check for existing content in database
            content_hash = hashlib.md5(f"{affirmation}_{period_name}_{style}".encode()).hexdigest()
            existing_posts = await self._get_from_database(content_hash)
            
            if existing_posts:
                return {
                    "success": True,
                    "post": existing_posts[0],
                    "source": "existing",
                    "message": f"Existing Instagram post for {period_name} retrieved"
                }
            
            # Create task for content generation
            task = Task(
                description=f"""
                Create an engaging Instagram post for the 7 Cycles period "{period_name}" with the following affirmation:
                
                Affirmation: "{affirmation}"
                
                Period Information:
                - Name: {period_name}
                - Color: {period_info.get('color', '#000000')}
                - Focus: {period_info.get('focus', '')}
                - Description: {period_info.get('description', '')}
                - Keywords: {', '.join(period_info.get('keywords', []))}
                
                Context from 7 Cycles knowledge base:
                {context}
                
                Style: {style}
                
                Create a complete Instagram post that includes:
                
                1. POST TEXT (150-200 words):
                   - Start with an engaging hook related to the period
                   - Incorporate the affirmation naturally into the text
                   - Provide context about the {period_name} period from the 7 Cycles system
                   - Make it relatable and inspiring
                   - End with a compelling call-to-action
                
                2. HASHTAGS (25-30 hashtags):
                   - Mix of trending personal development hashtags
                   - 7 Cycles specific hashtags
                   - Period-specific hashtags for {period_name}
                   - Community building hashtags
                   - Engagement-focused hashtags
                   
                3. CALL-TO-ACTION:
                   - Encourage meaningful engagement (comments, shares, saves)
                   - Ask thought-provoking questions
                   - Invite followers to share their experiences
                   - Promote community interaction
                
                4. ENGAGEMENT STRATEGIES:
                   - Suggest optimal posting times
                   - Recommend story follow-up content
                   - Provide tips for community building
                
                Format the response as JSON:
                {{
                    "post_text": "Complete Instagram post text with natural affirmation integration",
                    "hashtags": ["#hashtag1", "#hashtag2", ...],
                    "call_to_action": "Specific call-to-action text",
                    "engagement_strategies": ["strategy1", "strategy2", ...],
                    "optimal_posting_time": "Recommended posting time",
                    "period_name": "{period_name}",
                    "period_color": "{period_info.get('color', '#000000')}",
                    "affirmation": "{affirmation}",
                    "style": "{style}"
                }}
                """,
                expected_output="JSON formatted Instagram post with text, hashtags, call-to-action, and engagement strategies",
                agent=self.write_hashtag_agent
            )
            
            # Create and execute crew
            crew = Crew(
                agents=[self.write_hashtag_agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                post_data = json.loads(str(result))
            except json.JSONDecodeError:
                # If JSON parsing fails, create a structured response from the text
                result_str = str(result)
                
                # Extract key components using simple text parsing
                post_data = {
                    "post_text": self._extract_post_text(result_str, affirmation, period_name),
                    "hashtags": self._extract_hashtags(result_str, period_info),
                    "call_to_action": self._extract_call_to_action(result_str),
                    "engagement_strategies": self._get_default_engagement_strategies(period_name),
                    "optimal_posting_time": "7:00-9:00 AM oder 6:00-8:00 PM",
                    "period_name": period_name,
                    "period_color": period_info.get('color', '#000000'),
                    "affirmation": affirmation,
                    "style": style
                }
            
            # Add metadata
            post_data["created_at"] = datetime.now().isoformat()
            post_data["id"] = content_hash
            
            # Save to database
            db_id = await self._save_to_database(post_data)
            if db_id:
                post_data["db_id"] = db_id
                logger.info(f"Instagram post saved to database with ID: {db_id}")
            else:
                logger.warning("Failed to save Instagram post to database")
            
            return {
                "success": True,
                "post": post_data,
                "source": "generated",
                "message": f"Instagram post for {period_name} successfully generated"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error generating Instagram post"
            }
    
    def _extract_post_text(self, result_str: str, affirmation: str, period_name: str) -> str:
        """Extract or create post text from result"""
        # Try to find post text in the result
        lines = result_str.split('\n')
        post_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('"') and len(line) > 20:
                post_lines.append(line)
        
        if post_lines:
            return ' '.join(post_lines[:3])  # Take first few meaningful lines
        
        # Fallback: create a simple post text
        period_descriptions = {
            "Image": "Dein Selbstbild ist der Grundstein für alles, was du im Leben erreichst.",
            "Veränderung": "Veränderung ist nicht nur unvermeidlich, sondern auch der Schlüssel zu deinem Wachstum.",
            "Energie": "Deine Energie ist deine wertvollste Ressource – nutze sie bewusst.",
            "Kreativität": "Kreativität ist die Sprache deiner Seele – lass sie frei fließen.",
            "Erfolg": "Erfolg ist nicht nur ein Ziel, sondern eine Reise voller Lernen und Wachstum.",
            "Entspannung": "In der Ruhe liegt die Kraft – finde deine innere Balance.",
            "Umsicht": "Weise Entscheidungen entstehen aus Besonnenheit und klarer Sicht."
        }
        
        base_text = period_descriptions.get(period_name, f"Die {period_name}-Periode ist eine kraftvolle Zeit für dein persönliches Wachstum.")
        
        return f"{base_text}\n\n{affirmation}\n\nWie lebst du diese Energie in deinem Alltag? Teile deine Erfahrungen in den Kommentaren! 💫"
    
    def _extract_hashtags(self, result_str: str, period_info: Dict[str, Any]) -> List[str]:
        """Extract or create hashtags from result"""
        import re
        
        # Try to extract hashtags from result
        hashtags = re.findall(r'#\w+', result_str)
        
        if len(hashtags) >= 20:
            return hashtags[:30]  # Limit to 30 hashtags
        
        # Create default hashtags
        base_hashtags = [
            "#7cycles", "#lebenszyklen", "#persönlichkeitsentwicklung", "#affirmationen",
            "#achtsamkeit", "#bewusstsein", "#spiritualität", "#wachstum", "#transformation",
            "#selbstliebe", "#mentalhealth", "#wellness", "#mindfulness", "#inspiration",
            "#motivation", "#positivevibes", "#selfcare", "#innerpeace", "#consciousness",
            "#lifecoach", "#personaldevelopment", "#growth", "#mindset", "#wellbeing",
            "#spirituality", "#meditation", "#selfawareness", "#empowerment", "#healing"
        ]
        
        # Add period-specific hashtags
        period_hashtags = period_info.get('hashtags', [])
        
        # Combine and deduplicate
        all_hashtags = list(set(base_hashtags + period_hashtags))
        
        return all_hashtags[:30]
    
    def _extract_call_to_action(self, result_str: str) -> str:
        """Extract or create call-to-action from result"""
        # Look for questions or engagement prompts
        lines = result_str.split('\n')
        for line in lines:
            if '?' in line and len(line) > 10:
                return line.strip()
        
        # Fallback call-to-action
        return "Welche Erfahrungen hast du mit dieser Energie gemacht? Teile sie in den Kommentaren! 💫"
    
    def _get_default_engagement_strategies(self, period_name: str) -> List[str]:
        """Get default engagement strategies for a period"""
        return [
            "Stelle eine Frage, die zur Selbstreflexion anregt",
            "Teile persönliche Erfahrungen in den Stories",
            "Verwende relevante Hashtags für maximale Reichweite",
            "Antworte schnell auf Kommentare für bessere Engagement-Rate",
            "Poste zur optimalen Zeit für deine Zielgruppe",
            f"Erstelle Follow-up Content über {period_name} in Stories",
            "Ermutige User Generated Content mit einem Hashtag",
            "Teile den Post in relevanten Wellness-Communities"
        ]
    
    async def get_generated_posts(self, period_name: str = None) -> Dict[str, Any]:
        """Get all generated posts, optionally filtered by period"""
        try:
            # Get all posts from database
            posts = await self._get_from_database()
            
            # Filter by period if specified
            if period_name:
                filtered_posts = [
                    post for post in posts
                    if post.get("period_name") == period_name
                ]
            else:
                filtered_posts = posts
            
            return {
                "success": True,
                "posts": filtered_posts,
                "count": len(filtered_posts),
                "period_name": period_name
            }
            
        except Exception as e:
            logger.error(f"Error getting posts: {e}")
            return {
                "success": False,
                "error": str(e),
                "posts": []
            }