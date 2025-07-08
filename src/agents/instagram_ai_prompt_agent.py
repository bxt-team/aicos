from crewai import Agent, Task, Crew
from crewai.llm import LLM
import os
import json
from typing import Dict, Any, List
from datetime import datetime
import hashlib
from src.crews.base_crew import BaseCrew
from src.tools.image_generator import ImageGenerator
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

class InstagramAIPromptAgent(BaseCrew):
    """Agent for creating AI image prompts from complete Instagram post data"""
    
    def __init__(self, openai_api_key: str):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize image generator
        self.image_generator = ImageGenerator(openai_api_key)
        
        # Storage for generated prompts and images
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/ai_prompt_storage.json")
        self.generated_content = self._load_generated_content()
        
        # Initialize knowledge base and vector store
        self.knowledge_base = self._initialize_knowledge_base()
        
        # Create the prompt generation agent
        self.prompt_agent = self._create_prompt_agent()
        
        # 7 Cycles period colors and themes
        self.period_info = {
            "Image": {
                "color": "#DAA520",
                "themes": ["self-image", "identity", "authenticity", "confidence", "recognition", "professional appearance"],
                "visual_elements": ["mirrors", "golden light", "professional settings", "clear reflections", "polished surfaces"]
            },
            "Veränderung": {
                "color": "#2196F3", 
                "themes": ["transformation", "change", "growth", "adaptability", "flow", "evolution"],
                "visual_elements": ["flowing water", "butterflies", "seasonal changes", "metamorphosis", "bridges", "pathways"]
            },
            "Energie": {
                "color": "#F44336",
                "themes": ["vitality", "power", "strength", "dynamic action", "passion", "life force"],
                "visual_elements": ["fire", "lightning", "sunrise", "athletic movements", "vibrant energy", "dynamic poses"]
            },
            "Kreativität": {
                "color": "#FFD700",
                "themes": ["innovation", "inspiration", "artistic expression", "imagination", "creativity", "originality"],
                "visual_elements": ["paint brushes", "artistic tools", "colorful palettes", "creative chaos", "light bulbs", "artistic studios"]
            },
            "Erfolg": {
                "color": "#CC0066",
                "themes": ["achievement", "fulfillment", "manifestation", "goals", "success", "accomplishment"],
                "visual_elements": ["peaks", "trophies", "celebrations", "achievements", "upward arrows", "victory poses"]
            },
            "Entspannung": {
                "color": "#4CAF50",
                "themes": ["peace", "balance", "harmony", "rest", "tranquility", "inner calm"],
                "visual_elements": ["nature", "zen gardens", "peaceful water", "soft lighting", "meditation poses", "serene landscapes"]
            },
            "Umsicht": {
                "color": "#9C27B0",
                "themes": ["wisdom", "reflection", "strategic thinking", "mindfulness", "careful planning", "deep insight"],
                "visual_elements": ["wise figures", "thoughtful poses", "libraries", "contemplative settings", "chess pieces", "ancient symbols"]
            }
        }
    
    def _initialize_knowledge_base(self) -> FAISS:
        """Initialize the 7 Cycles knowledge base with vector embeddings"""
        try:
            # Path to the 7 Cycles ebook
            ebook_path = os.path.join(os.path.dirname(__file__), "../../knowledge_files/20250607_7Cycles of Life_Ebook.pdf")
            
            if not os.path.exists(ebook_path):
                print(f"Warning: 7 Cycles ebook not found at {ebook_path}")
                return None
            
            # Load and split the PDF
            loader = PyPDFLoader(ebook_path)
            documents = loader.load()
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            chunks = text_splitter.split_documents(documents)
            
            # Create embeddings and vector store
            embeddings = OpenAIEmbeddings(openai_api_key=self.openai_api_key)
            vector_store = FAISS.from_documents(chunks, embeddings)
            
            print(f"Successfully loaded 7 Cycles knowledge base with {len(chunks)} chunks")
            return vector_store
            
        except Exception as e:
            print(f"Error initializing knowledge base: {e}")
            return None
    
    def _get_period_context(self, period_name: str, period_info: Dict[str, Any]) -> str:
        """Get relevant context for a specific 7 Cycles period from the knowledge base"""
        if not self.knowledge_base:
            return ""
        
        try:
            # Create queries for different aspects of the period
            period_queries = {
                "Image": "image selbstbild identität wahrnehmung ausstrahlung selbstvertrauen authentizität",
                "Veränderung": "veränderung transformation wandel anpassung neubeginn flexibilität wachstum",
                "Energie": "energie kraft vitalität power stärke lebendigkeit dynamik",
                "Kreativität": "kreativität inspiration innovation künstlerisch schöpferisch imagination",
                "Erfolg": "erfolg achievement manifestation ziele erreichen erfüllung",
                "Entspannung": "entspannung ruhe balance harmony frieden gelassenheit",
                "Umsicht": "umsicht wisdom weisheit reflektion strategisch achtsamkeit"
            }
            
            query = period_queries.get(period_name, f"{period_name.lower()} 7 cycles")
            
            # Search for relevant context
            docs = self.knowledge_base.similarity_search(query, k=3)
            context = "\n\n".join([doc.page_content for doc in docs])
            
            return context[:800] if context else ""  # Limit context length
            
        except Exception as e:
            print(f"Error getting period context: {e}")
            return ""
    
    def _load_generated_content(self) -> Dict[str, Any]:
        """Load previously generated content"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading content storage: {e}")
        return {"prompts": [], "images": [], "by_instagram_post": {}}
    
    def _save_generated_content(self):
        """Save generated content to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.generated_content, f, indent=2)
        except Exception as e:
            print(f"Error saving content: {e}")
    
    def _create_prompt_agent(self) -> Agent:
        """Create the AI prompt generation agent"""
        return Agent(
            role="7 Cycles Instagram AI Bild-Prompt Meister",
            goal="Analysiere vollständige Instagram-Posts und erstelle spirituell-informierte DALL-E Prompts auf DEUTSCH die die Essenz des Post-Inhalts, Hashtags und tiefe 7 Cycles Periodenwisheit erfassen, verstärkt durch die offizielle Wissensbasis",
            backstory="""
            Du bist ein Experte für AI-Prompt-Engineering, spezialisiert auf das 7 Cycles System und Instagram-Content-Erstellung.
            Du hast exklusiven Zugang zur vollständigen 7 Cycles of Life Ebook-Wissensbasis und tiefes Verständnis von:
            
            KERN-EXPERTISE:
            - Erweiterte Analyse von Instagram-Post-Text, Hashtags und Call-to-Actions zur Extraktion visueller Themen
            - Tiefes Wissen über die authentische Energie, Weisheit und visuelle Darstellung jeder 7 Cycles Periode
            - Integration spiritueller Konzepte aus dem 7 Cycles Ebook in moderne visuelle Geschichten
            - DALL-E Prompt-Optimierung zur Erstellung spirituell resonanter und ästhetisch ansprechender Bilder
            - Umwandlung komplexer spiritueller Konzepte in überzeugende, zugängliche visuelle Metaphern
            
            ERWEITERTE FÄHIGKEITEN MIT WISSENSBASIS:
            - Zugang zu authentischer 7 Cycles Weisheit für jede Periode aus dem offiziellen Ebook
            - Verständnis wie sich die Themen jeder Periode in visuelle Darstellungen übersetzen
            - Wissen über spirituelle Symbolik und Metaphern angemessen für jeden Zyklus
            - Fähigkeit Prompts zu erstellen die die Tiefe der 7 Cycles Philosophie ehren und dabei Instagram-freundlich bleiben
            - Integration traditioneller spiritueller Elemente mit modernen ästhetischen Präferenzen
            
            SPEZIALISIERTE FÄHIGKEITEN:
            - Extraktion wichtiger visueller Themen aus Hashtag-Sammlungen informiert durch Periodenwissen
            - Verstehen des emotionalen und spirituellen Tons von Instagram-Posts im 7 Cycles Kontext
            - Erstellen von Prompts die authentische spirituelle/persönliche Entwicklungsthemen mit visueller Attraktivität balancieren
            - Natürliche Integration periodenspezifischer Farben, Symbole und Elemente basierend auf Ebook-Weisheit
            - Sicherstellung dass generierte Bilder Affirmations-Text-Overlays unterstützen während sie spirituelle Tiefe vermitteln
            - Optimierung von Tags und visuellen Elementen basierend auf authentischen 7 Cycles Lehren
            
            WICHTIG: Alle DALL-E Prompts MÜSSEN auf DEUTSCH geschrieben werden!
            
            Dein einzigartiger Wert kommt aus der Verbindung moderner AI-Bildgenerierung mit uralter spiritueller Weisheit,
            um visuell atemberaubende Inhalte zu erstellen die echte persönliche Transformation und Wachstum unterstützen.
            """,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm
        )
    
    def generate_ai_image_from_instagram_post(self, instagram_post_data: Dict[str, Any], 
                                            post_format: str = "post", image_style: str = "inspirational") -> Dict[str, Any]:
        """Generate an AI image based on complete Instagram post data"""
        try:
            # Extract data from Instagram post
            post_text = instagram_post_data.get("instagram_post_text", "")
            hashtags = instagram_post_data.get("instagram_hashtags", "")
            call_to_action = instagram_post_data.get("instagram_cta", "")
            period_name = instagram_post_data.get("period", "")
            affirmation = instagram_post_data.get("text", "")
            instagram_style = instagram_post_data.get("instagram_style", "inspirational")
            
            # Get period information
            period_info = self.period_info.get(period_name, {})
            
            # Get knowledge-based context for the period
            knowledge_context = self._get_period_context(period_name, period_info)
            
            # Check for existing content
            content_hash = hashlib.md5(f"{post_text}_{hashtags}_{period_name}_{image_style}".encode()).hexdigest()
            existing = self.generated_content.get("by_instagram_post", {}).get(content_hash)
            
            if existing:
                return {
                    "success": True,
                    "image": existing,
                    "source": "existing",
                    "message": f"Existing AI image for Instagram post retrieved"
                }
            
            # Extract and clean hashtags (remove # symbols)
            cleaned_hashtags = hashtags.replace('#', '') if hashtags else ""
            
            # Create task for AI prompt generation
            task = Task(
                description=f"""
                Analysiere diesen vollständigen Instagram-Post und erstelle einen detaillierten DALL-E Prompt zur Generierung eines Hintergrundbildes:

                INSTAGRAM POST INHALT:
                Post Text: "{post_text}"
                Hashtags: "{cleaned_hashtags}"
                Call-to-Action: "{call_to_action}"
                Kern-Affirmation: "{affirmation}"
                Instagram Style: "{instagram_style}"
                
                7 CYCLES PERIOD INFORMATION:
                Period: {period_name}
                Period Farbe: {period_info.get('color', '#000000')}
                Period Themen: {', '.join(period_info.get('themes', []))}
                Visuelle Elemente: {', '.join(period_info.get('visual_elements', []))}
                
                WISSENSBASIS AUS 7 CYCLES EBOOK:
                {knowledge_context}
                
                POST FORMAT: {post_format} ({"Instagram Post 4:5 Verhältnis" if post_format == "post" else "Instagram Story 9:16 Verhältnis"})
                IMAGE STYLE: {image_style}
                
                ANFORDERUNGEN:
                1. Analysiere den vollständigen Instagram-Inhalt um die Gesamtbotschaft und Energie zu verstehen
                2. Extrahiere visuelle Themen aus der Hashtag-Sammlung (ohne # Symbole)
                3. Integriere Erkenntnisse aus der 7 Cycles Wissensbasis für authentische periodenspezifische Bilder
                4. Integriere die periodenspezifische Farbe ({period_info.get('color', '#000000')}) natürlich
                5. Erstelle einen Prompt der ein für Textüberlagerung geeignetes Hintergrundbild erzeugt
                6. Stelle sicher, dass das Bild das spirituelle/persönliche Entwicklungsthema mit 7 Cycles Weisheit unterstützt
                7. Mache es Instagram-tauglich und ästhetisch ansprechend
                8. Nutze den Wissenskontext für tiefere, bedeutungsvollere visuelle Metaphern
                
                Erstelle einen detaillierten DALL-E Prompt (max 400 Zeichen) auf DEUTSCH der folgendes erfasst:
                - Die Essenz des Instagram-Post-Inhalts verstärkt durch 7 Cycles Weisheit
                - Hauptthemen aus den Hashtags informiert durch Periodenwissen
                - Die Energie und Farbschema der Periode verwurzelt in authentischem Verständnis
                - Visuelle Elemente die die Affirmation mit spiritueller Tiefe unterstützen
                - Professionelle, inspirierende Ästhetik geeignet für soziale Medien
                
                Der DALL-E Prompt MUSS auf DEUTSCH geschrieben werden!
                
                Formatiere die Antwort als JSON:
                {{
                    "dalle_prompt": "Detaillierter DALL-E Prompt hier AUF DEUTSCH",
                    "visual_themes": ["thema1", "thema2", "thema3"],
                    "color_palette": ["{period_info.get('color', '#000000')}", "complementary_color1", "complementary_color2"],
                    "image_description": "Kurze Beschreibung des erwarteten Bildergebnisses",
                    "period_name": "{period_name}",
                    "instagram_analysis": "Kurze Analyse was diesen Prompt basierend auf dem Instagram-Inhalt ausmacht",
                    "knowledge_integration": "Wie 7 Cycles Wissen verwendet wurde um das visuelle Konzept zu verstärken",
                    "spiritual_elements": ["element1", "element2", "element3"],
                    "enhanced_tags": ["optimierte Tag-Vorschläge basierend auf Periodenwissen ohne # Symbole"]
                }}
                """,
                expected_output="JSON formatted DALL-E prompt with analysis and visual specifications",
                agent=self.prompt_agent
            )
            
            # Create and execute crew
            crew = Crew(
                agents=[self.prompt_agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                prompt_data = json.loads(str(result))
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails - using German prompt
                prompt_data = {
                    "dalle_prompt": self._create_fallback_prompt(period_name, affirmation, period_info),
                    "visual_themes": period_info.get('themes', [])[:3],
                    "color_palette": [period_info.get('color', '#000000'), "#FFFFFF", "#F5F5F5"],
                    "image_description": f"AI generated image for {period_name} period with {affirmation}",
                    "period_name": period_name,
                    "instagram_analysis": "Fallback prompt generated due to parsing error"
                }
            
            # Generate the actual image using DALL-E
            dalle_prompt = prompt_data.get("dalle_prompt", "")
            image_result = self.image_generator.generate_image(
                prompt=dalle_prompt,
                size="1024x1024",  # DALL-E 3 standard size
                style=image_style
            )
            
            if not image_result.get("success"):
                return {
                    "success": False,
                    "error": image_result.get("error", "Failed to generate image"),
                    "message": "Error generating AI image"
                }
            
            # Add metadata
            prompt_data["created_at"] = datetime.now().isoformat()
            prompt_data["id"] = content_hash
            prompt_data["image_url"] = image_result.get("image_url")
            prompt_data["image_path"] = image_result.get("image_path")
            prompt_data["post_format"] = post_format
            prompt_data["image_style"] = image_style
            prompt_data["instagram_post_data"] = instagram_post_data
            
            # Store the generated content
            self.generated_content["images"].append(prompt_data)
            self.generated_content["by_instagram_post"][content_hash] = prompt_data
            self._save_generated_content()
            
            return {
                "success": True,
                "image": prompt_data,
                "source": "generated",
                "message": f"AI image for {period_name} Instagram post successfully generated"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error generating AI image from Instagram post"
            }
    
    def _create_fallback_prompt(self, period_name: str, affirmation: str, period_info: Dict[str, Any]) -> str:
        """Create a fallback prompt if the main generation fails"""
        color = period_info.get('color', '#000000')
        themes = ', '.join(period_info.get('themes', [])[:2])
        visual_elements = ', '.join(period_info.get('visual_elements', [])[:2])
        
        return f"Ein wunderschöner, inspirierender {period_name.lower()}-thematischer Hintergrund mit {visual_elements}, {themes}, sanftes Licht, friedliche Atmosphäre, geeignet für Affirmations-Text-Overlay, {color} Farbschema, professioneller Fotografie-Stil, spirituelle und erhebende Stimmung"
    
    def optimize_tags_with_knowledge(self, original_tags: List[str], period_name: str, instagram_content: Dict[str, Any]) -> List[str]:
        """Optimize tags using 7 Cycles knowledge base"""
        if not self.knowledge_base:
            return original_tags
        
        try:
            # Get period-specific context
            period_info = self.period_info.get(period_name, {})
            knowledge_context = self._get_period_context(period_name, period_info)
            
            # Create enhanced tag suggestions based on knowledge
            enhanced_tags = []
            
            # Add period-specific visual elements
            visual_elements = period_info.get('visual_elements', [])
            enhanced_tags.extend(visual_elements[:3])
            
            # Add period themes
            themes = period_info.get('themes', [])
            enhanced_tags.extend(themes[:2])
            
            # Combine with original tags and remove duplicates
            all_tags = list(set(original_tags + enhanced_tags))
            
            # Limit to most relevant tags
            return all_tags[:8]
            
        except Exception as e:
            print(f"Error optimizing tags with knowledge: {e}")
            return original_tags
    
    def get_enhanced_context_summary(self, period_name: str) -> Dict[str, Any]:
        """Get enhanced context summary for a period including knowledge insights"""
        period_info = self.period_info.get(period_name, {})
        knowledge_context = self._get_period_context(period_name, period_info)
        
        return {
            "period_name": period_name,
            "color": period_info.get('color', '#000000'),
            "themes": period_info.get('themes', []),
            "visual_elements": period_info.get('visual_elements', []),
            "knowledge_context": knowledge_context[:500] if knowledge_context else "",
            "has_knowledge": bool(knowledge_context),
            "knowledge_chunks": len(knowledge_context.split('\n\n')) if knowledge_context else 0
        }
    
    def get_generated_images(self, period_name: str = None) -> Dict[str, Any]:
        """Get all generated AI images, optionally filtered by period"""
        try:
            if period_name:
                filtered_images = [
                    img for img in self.generated_content.get("images", [])
                    if img.get("period_name") == period_name
                ]
            else:
                filtered_images = self.generated_content.get("images", [])
            
            return {
                "success": True,
                "images": filtered_images,
                "count": len(filtered_images),
                "period_name": period_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }