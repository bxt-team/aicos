from crewai import Agent, Task, Crew
from crewai.agent import Agent
from crewai.llm import LLM
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import json
from typing import List, Dict, Any
from datetime import datetime, timedelta
import hashlib

class AffirmationsAgent:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vector_store = None
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Storage for generated affirmations
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/affirmations_storage.json")
        self.generated_affirmations = self._load_generated_affirmations()
        
        # Initialize knowledge base
        self._load_knowledge_base()
        
        # Create the affirmations agent
        self.affirmations_agent = Agent(
            role="7 Lebenszyklen Affirmationen-Ersteller",
            goal="Erstelle personalisierte Affirmationen basierend auf dem 7 Lebenszyklen-Konzept, um Menschen bei der Fokussierung auf verschiedene Lebensperioden zu helfen",
            backstory="""Du bist ein erfahrener Affirmationen-Ersteller mit tiefem Verständnis der 7 Lebenszyklen-Philosophie. 
            Du erstellst kraftvolle, personalisierte Affirmationen, die Menschen helfen, sich mit den natürlichen Rhythmen des Lebens 
            in Einklang zu bringen. Deine Affirmationen sind darauf ausgelegt, Fokus, Energie und Erfolg während spezifischer 
            Lebensperioden und Zyklen zu verstärken. Du verstehst, wie man Affirmationen kreiert, die mit den einzigartigen 
            Eigenschaften jedes Zyklus resonieren. WICHTIG: Erstelle alle Affirmationen auf Deutsch!""",
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )
    
    def _load_knowledge_base(self):
        """Load and process the PDF knowledge base"""
        try:
            pdf_path = os.path.join(os.path.dirname(__file__), "../../knowledge_files/20250607_7Cycles of Life_Ebook.pdf")
            
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
            
            print(f"Erfolgreich {len(texts)} Dokumentenabschnitte für Affirmationen geladen")
            
        except Exception as e:
            print(f"Fehler beim Laden der Wissensdatenbank für Affirmationen: {e}")
            self.vector_store = None
    
    def _load_generated_affirmations(self) -> Dict[str, Any]:
        """Load previously generated affirmations"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading affirmations storage: {e}")
        
        return {"affirmations": [], "by_period": {}}
    
    def _save_generated_affirmations(self):
        """Save generated affirmations to storage"""
        try:
            os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
            with open(self.storage_file, 'w') as f:
                json.dump(self.generated_affirmations, f, indent=2)
        except Exception as e:
            print(f"Error saving affirmations: {e}")
    
    def _get_period_context(self, period_type: str, period_info: Dict[str, Any]) -> str:
        """Get relevant context for a specific period"""
        if not self.vector_store:
            return "Wissensdatenbank nicht verfügbar"
        
        try:
            # Create search query based on period type
            queries = {
                "tag": f"day cycle daily rhythm tages {period_info.get('phase', '')}",
                "woche": f"week cycle weekly rhythm wochen {period_info.get('phase', '')}",
                "monat": f"month cycle monthly rhythm monat {period_info.get('phase', '')}",
                "jahr": f"year cycle yearly rhythm jahr {period_info.get('phase', '')}",
                "leben": f"life cycle life phase leben {period_info.get('stage', '')}",
                "allgemein": "7 cycles of life energy creativity success lebenszyklen"
            }
            
            query = queries.get(period_type, queries["allgemein"])
            
            # Retrieve relevant documents
            docs = self.vector_store.similarity_search(query, k=3)
            
            # Combine context
            context = "\n\n".join([doc.page_content for doc in docs])
            return context
            
        except Exception as e:
            print(f"Fehler beim Abrufen des Perioden-Kontexts: {e}")
            return "Fehler beim Abrufen des Kontexts"
    
    def _generate_affirmation_hash(self, period_type: str, period_info: Dict[str, Any]) -> str:
        """Generate a hash for the period to check for duplicates"""
        period_key = f"{period_type}_{json.dumps(period_info, sort_keys=True)}"
        return hashlib.md5(period_key.encode()).hexdigest()
    
    def _check_existing_affirmations(self, period_hash: str) -> List[Dict[str, Any]]:
        """Check if affirmations already exist for this period"""
        return self.generated_affirmations.get("by_period", {}).get(period_hash, [])
    
    def generate_affirmations(self, period_type: str, period_info: Dict[str, Any], count: int = 5) -> Dict[str, Any]:
        """Generate affirmations for a specific period"""
        try:
            # Check for existing affirmations
            period_hash = self._generate_affirmation_hash(period_type, period_info)
            existing = self._check_existing_affirmations(period_hash)
            
            if existing:
                return {
                    "success": True,
                    "affirmations": existing,
                    "period_type": period_type,
                    "period_info": period_info,
                    "source": "existing",
                    "message": "Bestehende Affirmationen für diese Periode abgerufen"
                }
            
            # Get relevant context
            context = self._get_period_context(period_type, period_info)
            
            # Create task
            task = Task(
                description=f"""
                Erstelle {count} kraftvolle Affirmationen für die {period_type}-Periode basierend auf dem 7 Lebenszyklen-Wissen.
                
                Perioden-Typ: {period_type}
                Perioden-Information: {json.dumps(period_info, indent=2)}
                
                Kontext aus der Wissensdatenbank:
                {context}
                
                Anweisungen:
                - Erstelle Affirmationen, die mit den natürlichen Rhythmen dieser spezifischen Periode übereinstimmen
                - Jede Affirmation sollte positiv, in der Gegenwartsform und persönlich stärkend sein
                - Fokussiere auf die einzigartigen Eigenschaften und Möglichkeiten dieser Periode
                - Integriere Themen wie Energie, Kreativität, Erfolg und Einklang mit natürlichen Zyklen
                - Mache sie praktisch und im Alltag anwendbar
                - Jede Affirmation sollte 10-20 Wörter lang sein
                - Stelle Vielfalt in den Fokusbereich sicher (Energie, Kreativität, Erfolg, Beziehungen, Wachstum)
                - WICHTIG: Alle Affirmationen müssen auf Deutsch sein!
                
                Formatiere als JSON:
                {{
                    "affirmations": [
                        {{
                            "text": "Affirmationstext",
                            "theme": "energie/kreativitaet/erfolg/beziehungen/wachstum",
                            "focus": "Kurze Beschreibung des Fokus dieser Affirmation"
                        }}
                    ]
                }}
                """,
                expected_output="JSON formatierte Liste von Affirmationen mit Themen und Fokusbereichen",
                agent=self.affirmations_agent
            )
            
            # Execute task
            crew = Crew(
                agents=[self.affirmations_agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                affirmations_data = json.loads(str(result))
            except json.JSONDecodeError:
                # If JSON parsing fails, create simple structure
                affirmations_data = {
                    "affirmations": [
                        {
                            "text": line.strip(),
                            "theme": "allgemein",
                            "focus": "tägliche Stärkung"
                        }
                        for line in str(result).split('\n') 
                        if line.strip() and not line.strip().startswith('{') and not line.strip().startswith('}')
                    ][:count]
                }
            
            # Add metadata
            for affirmation in affirmations_data["affirmations"]:
                affirmation["created_at"] = datetime.now().isoformat()
                affirmation["period_type"] = period_type
                affirmation["period_info"] = period_info
                affirmation["id"] = hashlib.md5(f"{affirmation['text']}_{period_hash}".encode()).hexdigest()
            
            # Store the affirmations
            self.generated_affirmations["affirmations"].extend(affirmations_data["affirmations"])
            self.generated_affirmations["by_period"][period_hash] = affirmations_data["affirmations"]
            self._save_generated_affirmations()
            
            return {
                "success": True,
                "affirmations": affirmations_data["affirmations"],
                "period_type": period_type,
                "period_info": period_info,
                "source": "generated",
                "message": f"{len(affirmations_data['affirmations'])} neue Affirmationen generiert"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Generieren der Affirmationen"
            }
    
    def get_affirmations_by_period(self, period_type: str = None) -> Dict[str, Any]:
        """Get all affirmations, optionally filtered by period type"""
        try:
            if period_type:
                filtered_affirmations = [
                    aff for aff in self.generated_affirmations.get("affirmations", [])
                    if aff.get("period_type") == period_type
                ]
            else:
                filtered_affirmations = self.generated_affirmations.get("affirmations", [])
            
            return {
                "success": True,
                "affirmations": filtered_affirmations,
                "count": len(filtered_affirmations),
                "period_type": period_type
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_periods(self) -> Dict[str, Any]:
        """Get information about available period types"""
        return {
            "success": True,
            "period_types": {
                "tag": {
                    "description": "Tageszyklus-Affirmationen",
                    "phases": ["morgen", "nachmittag", "abend", "nacht"]
                },
                "woche": {
                    "description": "Wochenzyklus-Affirmationen",
                    "phases": ["planung", "aktion", "vollendung", "reflexion"]
                },
                "monat": {
                    "description": "Monatszyklus-Affirmationen",
                    "phases": ["neumond", "zunehmend", "vollmond", "abnehmend"]
                },
                "jahr": {
                    "description": "Jahreszyklus-Affirmationen",
                    "phases": ["fruehling", "sommer", "herbst", "winter"]
                },
                "leben": {
                    "description": "Lebensphasen-Affirmationen",
                    "stages": ["kindheit", "jugend", "erwachsenenalter", "reife", "weisheit"]
                }
            }
        }