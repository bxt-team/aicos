from crewai import Agent, Task, Crew
from crewai.llm import LLM
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import json
from typing import List, Dict, Any
from datetime import datetime
import hashlib
from app.agents.crews.base_crew import BaseCrew

class WriteHashtagResearchAgent(BaseCrew):
    def __init__(self, openai_api_key: str):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vector_store = None
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Storage for generated content
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/write_hashtag_storage.json")
        self.generated_content = self._load_generated_content()
        
        # Initialize knowledge base
        self._load_knowledge_base()
        
        # Create the agent
        self.write_hashtag_agent = self._create_write_hashtag_agent()
    
    def _load_knowledge_base(self):
        """Load and process the PDF knowledge base for 7 Cycles"""
        try:
            pdf_path = os.path.join(os.path.dirname(__file__), "../../knowledge/20250607_7Cycles of Life_Ebook.pdf")
            
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            
            texts = text_splitter.split_documents(documents)
            
            # Create vector store
            self.vector_store = FAISS.from_documents(texts, self.embeddings)
            
            print(f"Successfully loaded {len(texts)} document sections for Write and Hashtag Research")
            
        except Exception as e:
            print(f"Error loading knowledge base: {e}")
            self.vector_store = None
    
    def _load_generated_content(self) -> Dict[str, Any]:
        """Load previously generated content"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading content storage: {e}")
        
        return {"posts": [], "by_affirmation": {}}
    
    def _save_generated_content(self):
        """Save generated content to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.generated_content, f, indent=2)
        except Exception as e:
            print(f"Error saving content: {e}")
    
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
    
    def generate_instagram_post(self, affirmation: str, period_name: str, style: str = "inspirational") -> Dict[str, Any]:
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
            
            # Check for existing content
            content_hash = hashlib.md5(f"{affirmation}_{period_name}_{style}".encode()).hexdigest()
            existing = self.generated_content.get("by_affirmation", {}).get(content_hash)
            
            if existing:
                return {
                    "success": True,
                    "post": existing,
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
            
            # Store the generated content
            self.generated_content["posts"].append(post_data)
            self.generated_content["by_affirmation"][content_hash] = post_data
            self._save_generated_content()
            
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
    
    def get_generated_posts(self, period_name: str = None) -> Dict[str, Any]:
        """Get all generated posts, optionally filtered by period"""
        try:
            if period_name:
                filtered_posts = [
                    post for post in self.generated_content.get("posts", [])
                    if post.get("period_name") == period_name
                ]
            else:
                filtered_posts = self.generated_content.get("posts", [])
            
            return {
                "success": True,
                "posts": filtered_posts,
                "count": len(filtered_posts),
                "period_name": period_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }