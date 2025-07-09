from crewai import Agent, Task, Crew
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
from app.agents.crews.base_crew import BaseCrew

class AffirmationsAgent(BaseCrew):
    def __init__(self, openai_api_key: str):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.vector_store = None
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Storage for generated affirmations
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../../static/affirmations_storage.json")
        self.generated_affirmations = self._load_generated_affirmations()
        
        # Initialize knowledge base
        self._load_knowledge_base()
        
        # Create the affirmations agent from YAML config
        self.affirmations_agent = self.create_agent("affirmations_agent", llm=self.llm)
    
    def _load_knowledge_base(self):
        """Load and process the PDF knowledge base"""
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
    
    def _get_period_context(self, period_name: str, period_info: Dict[str, Any]) -> str:
        """Get relevant context for a specific 7 Cycles period"""
        if not self.vector_store:
            return "Wissensdatenbank nicht verfügbar"
        
        try:
            # Create search query based on 7 Cycles period
            period_queries = {
                "Image": "image selbstbild identität wahrnehmung ausstrahlung selbstvertrauen authentizität",
                "Veränderung": "veränderung transformation wandel anpassung neubeginn flexibilität wachstum",
                "Energie": "energie vitalität schwung dynamik kraft motivation ausdauer lebenskraft",
                "Kreativität": "kreativität innovation inspiration schöpfung künstlerisch kreativ entfaltung",
                "Erfolg": "erfolg zielerreichung leistung manifestation erfolgreich ziele erreichen",
                "Entspannung": "entspannung ruhe regeneration balance frieden gelassenheit erholung",
                "Umsicht": "umsicht weisheit besonnenheit planung entscheidungen weise strategisch"
            }
            
            # Get specific query for the period or use general 7 cycles query
            query = period_queries.get(period_name, "7 cycles lebenszyklen energie kreativität erfolg")
            
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
    
    def generate_affirmations(self, period_name: str, period_info: Dict[str, Any], count: int = 5) -> Dict[str, Any]:
        """Generate affirmations for a specific 7 Cycles period"""
        try:
            # Define the 7 Cycles periods with their colors
            cycles_periods = {
                "Image": "#DAA520",
                "Veränderung": "#2196F3", 
                "Energie": "#F44336",
                "Kreativität": "#FFD700",
                "Erfolg": "#CC0066",
                "Entspannung": "#4CAF50",
                "Umsicht": "#9C27B0"
            }
            
            # Validate period name
            if period_name not in cycles_periods:
                return {
                    "success": False,
                    "error": f"Ungültige Periode: {period_name}. Verfügbare Perioden: {list(cycles_periods.keys())}",
                    "message": "Ungültige 7 Cycles Periode"
                }
            
            period_color = cycles_periods[period_name]
            
            # Check for existing affirmations
            period_hash = self._generate_affirmation_hash(period_name, period_info)
            existing = self._check_existing_affirmations(period_hash)
            
            if existing:
                return {
                    "success": True,
                    "affirmations": existing,
                    "period_name": period_name,
                    "period_color": period_color,
                    "period_info": period_info,
                    "source": "existing",
                    "message": f"Bestehende Affirmationen für {period_name} abgerufen"
                }
            
            # Get relevant context
            context = self._get_period_context(period_name, period_info)
            
            # Create task from YAML config
            task = self.create_task(
                "generate_affirmations_task",
                self.affirmations_agent,
                count=count,
                period_name=period_name,
                period_color=period_color,
                period_info=json.dumps(period_info, indent=2),
                context=context
            )
            
            # Create and execute crew
            crew = self.create_crew(
                "affirmations_crew",
                agents=[self.affirmations_agent],
                tasks=[task]
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                affirmations_data = json.loads(str(result))
            except json.JSONDecodeError:
                # If JSON parsing fails, extract affirmations from text using regex
                import re
                result_str = str(result)
                
                # Try to extract affirmations from the text using regex
                affirmations_list = []
                
                # Look for "text": "..." patterns to extract actual affirmation text
                text_pattern = r'"text":\s*"([^"]+)"'
                text_matches = re.findall(text_pattern, result_str)
                
                # Look for theme and focus patterns
                theme_pattern = r'"theme":\s*"([^"]+)"'
                focus_pattern = r'"focus":\s*"([^"]+)"'
                
                theme_matches = re.findall(theme_pattern, result_str)
                focus_matches = re.findall(focus_pattern, result_str)
                
                # Create affirmations from extracted text
                for i, text in enumerate(text_matches):
                    if text and len(text) > 10:  # Only keep meaningful affirmations
                        theme = theme_matches[i] if i < len(theme_matches) else period_name
                        focus = focus_matches[i] if i < len(focus_matches) else f"{period_name} Stärkung"
                        
                        affirmations_list.append({
                            "text": text,
                            "theme": theme,
                            "focus": focus,
                            "period_color": period_color
                        })
                
                # If regex extraction failed, try simple line-by-line parsing
                if not affirmations_list:
                    lines = result_str.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Look for German affirmations (likely to start with "Ich")
                        if line and (line.startswith('Ich ') or line.startswith('Mein ') or line.startswith('Meine ')):
                            # Clean up the line
                            clean_line = line.strip('",.')
                            if clean_line and len(clean_line) > 10:
                                affirmations_list.append({
                                    "text": clean_line,
                                    "theme": period_name,
                                    "focus": f"{period_name} Stärkung",
                                    "period_color": period_color
                                })
                
                # If we still couldn't extract proper affirmations, create fallback ones
                if not affirmations_list:
                    period_affirmations = {
                        "Image": "Ich bin stolz auf mein wahres Selbst und strahle Selbstvertrauen aus.",
                        "Veränderung": "Ich begrüße Veränderungen als Chance für mein Wachstum.",
                        "Energie": "Ich bin voller Energie und Lebenskraft.",
                        "Kreativität": "Meine Kreativität fließt frei und inspiriert mich täglich.",
                        "Erfolg": "Ich erreiche meine Ziele mit Entschlossenheit und Freude.",
                        "Entspannung": "Ich finde innere Ruhe und Gelassenheit in jedem Moment.",
                        "Umsicht": "Ich treffe weise Entscheidungen mit Bedacht und Klarheit."
                    }
                    
                    base_affirmation = period_affirmations.get(period_name, f"Ich bin voller {period_name} und Energie.")
                    
                    affirmations_list = [
                        {
                            "text": base_affirmation,
                            "theme": period_name,
                            "focus": f"{period_name} Stärkung",
                            "period_color": period_color
                        }
                    ]
                
                affirmations_data = {
                    "affirmations": affirmations_list[:count]
                }
            
            # Add metadata
            for affirmation in affirmations_data["affirmations"]:
                affirmation["created_at"] = datetime.now().isoformat()
                affirmation["period_name"] = period_name
                affirmation["period_color"] = period_color
                affirmation["period_info"] = period_info
                affirmation["id"] = hashlib.md5(f"{affirmation['text']}_{period_hash}".encode()).hexdigest()
                # Ensure period_color is set
                if "period_color" not in affirmation:
                    affirmation["period_color"] = period_color
            
            # Store the affirmations
            self.generated_affirmations["affirmations"].extend(affirmations_data["affirmations"])
            self.generated_affirmations["by_period"][period_hash] = affirmations_data["affirmations"]
            self._save_generated_affirmations()
            
            return {
                "success": True,
                "affirmations": affirmations_data["affirmations"],
                "period_name": period_name,
                "period_color": period_color,
                "period_info": period_info,
                "source": "generated",
                "message": f"{len(affirmations_data['affirmations'])} neue Affirmationen für {period_name} generiert"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Generieren der Affirmationen"
            }
    
    def get_affirmations_by_period(self, period_name: str = None) -> Dict[str, Any]:
        """Get all affirmations, optionally filtered by 7 Cycles period"""
        try:
            if period_name:
                filtered_affirmations = [
                    aff for aff in self.generated_affirmations.get("affirmations", [])
                    if aff.get("period_name") == period_name or aff.get("period_type") == period_name
                ]
            else:
                filtered_affirmations = self.generated_affirmations.get("affirmations", [])
            
            return {
                "success": True,
                "affirmations": filtered_affirmations,
                "count": len(filtered_affirmations),
                "period_name": period_name
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_available_periods(self) -> Dict[str, Any]:
        """Get information about the 7 Cycles periods"""
        return {
            "success": True,
            "period_types": {
                "Image": {
                    "description": "Selbstbild, Identität und persönliche Ausstrahlung",
                    "color": "#DAA520",
                    "focus": "Selbstvertrauen, Authentizität, Selbstliebe",
                    "keywords": ["Ich bin", "Mein wahres Selbst", "Meine Ausstrahlung", "Meine Identität"]
                },
                "Veränderung": {
                    "description": "Transformation, Wandel und Anpassung",
                    "color": "#2196F3",
                    "focus": "Mut zur Veränderung, Flexibilität, Wachstum",
                    "keywords": ["Ich verändere", "Ich wachse", "Neue Wege", "Transformation"]
                },
                "Energie": {
                    "description": "Vitalität, Schwung und dynamische Kraft",
                    "color": "#F44336",
                    "focus": "Lebenskraft, Motivation, Ausdauer",
                    "keywords": ["Meine Energie", "Ich bin kraftvoll", "Vitalität", "Schwung"]
                },
                "Kreativität": {
                    "description": "Innovation, Inspiration und schöpferischer Ausdruck",
                    "color": "#FFD700",
                    "focus": "Kreative Entfaltung, Inspiration, Innovation",
                    "keywords": ["Ich erschaffe", "Meine Kreativität", "Innovation", "Inspiration"]
                },
                "Erfolg": {
                    "description": "Zielerreichung, Leistung und Manifestation",
                    "color": "#CC0066",
                    "focus": "Ziele erreichen, Erfolg manifestieren, Leistung",
                    "keywords": ["Ich erreiche", "Mein Erfolg", "Ziele verwirklichen", "Erfolgreiche Umsetzung"]
                },
                "Entspannung": {
                    "description": "Ruhe, Regeneration und innere Balance",
                    "color": "#4CAF50",
                    "focus": "Gelassenheit, Erholung, innere Ruhe",
                    "keywords": ["Ich entspanne", "Innere Ruhe", "Balance", "Gelassenheit"]
                },
                "Umsicht": {
                    "description": "Weisheit, Besonnenheit und durchdachte Planung",
                    "color": "#9C27B0",
                    "focus": "Weisheit, kluge Entscheidungen, strategisches Denken",
                    "keywords": ["Ich entscheide weise", "Meine Weisheit", "Besonnenheit", "Klare Sicht"]
                }
            }
        }