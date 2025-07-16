from crewai import Agent, Task, Crew
from crewai.llm import LLM
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import hashlib
from app.agents.crews.base_crew import BaseCrew
from app.services.knowledge_base_manager import knowledge_base_manager
from app.core.storage import StorageFactory
import logging
import asyncio

logger = logging.getLogger(__name__)

class AffirmationsAgent(BaseCrew):
    def __init__(self, openai_api_key: str):
        logger.info("[AFFIRMATIONS_AGENT] Initializing...")
        super().__init__()
        self.openai_api_key = openai_api_key
        
        # Use shared embeddings and vector store
        self.embeddings = knowledge_base_manager.get_embeddings()
        self.vector_store = knowledge_base_manager.get_vector_store()
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize storage adapter
        self.storage = StorageFactory.get_adapter()
        self.collection = "affirmations"
        
        # Create the affirmations agent from YAML config
        try:
            self.affirmations_agent = self.create_agent("affirmations_agent", llm=self.llm)
            logger.info("[AFFIRMATIONS_AGENT] Agent created successfully")
        except Exception as e:
            logger.error(f"[AFFIRMATIONS_AGENT] Error creating agent: {e}")
            raise
    
    async def _run_async(self, coro):
        """Helper to await async coroutines"""
        return await coro
    
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
    
    def _map_period_to_number(self, period_name: str) -> int:
        """Map period name to number (1-7)"""
        period_mapping = {
            "Image": 1,
            "Veränderung": 2,
            "Energie": 3,
            "Kreativität": 4,
            "Erfolg": 5,
            "Entspannung": 6,
            "Umsicht": 7
        }
        return period_mapping.get(period_name, 1)
    
    async def generate_affirmations(self, period_name: str, period_info: Dict[str, Any], count: int = 5) -> Dict[str, Any]:
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
            period_number = self._map_period_to_number(period_name)
            
            # Check for existing affirmations
            existing_affirmations = await self._run_async(
                self.storage.list(
                    self.collection,
                    filters={"period": period_number, "theme": period_name},
                    limit=count
                )
            )
            
            if existing_affirmations and len(existing_affirmations) >= count:
                return {
                    "success": True,
                    "affirmations": existing_affirmations[:count],
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
            
            # Save new affirmations to storage
            saved_affirmations = []
            for affirmation in affirmations_data["affirmations"]:
                # Prepare data for storage
                storage_data = {
                    "theme": period_name,
                    "period": period_number,
                    "affirmation": affirmation["text"],
                    "language": "de",
                    "metadata": {
                        "focus": affirmation.get("focus", f"{period_name} Stärkung"),
                        "period_color": period_color,
                        "period_info": period_info,
                        "generated_at": datetime.now().isoformat()
                    }
                }
                
                # Save to storage
                affirmation_id = await self._run_async(
                    self.storage.save(self.collection, storage_data)
                )
                
                # Add to result list
                saved_affirmation = storage_data.copy()
                saved_affirmation["id"] = affirmation_id
                saved_affirmation["created_at"] = storage_data["metadata"]["generated_at"]
                saved_affirmation["period_name"] = period_name
                saved_affirmation["period_color"] = period_color
                saved_affirmation["text"] = storage_data["affirmation"]
                saved_affirmations.append(saved_affirmation)
            
            return {
                "success": True,
                "affirmations": saved_affirmations,
                "period_name": period_name,
                "period_color": period_color,
                "period_info": period_info,
                "source": "generated",
                "message": f"{len(saved_affirmations)} neue Affirmationen für {period_name} generiert"
            }
            
        except Exception as e:
            logger.error(f"[AFFIRMATIONS_AGENT] Error generating affirmations: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Generieren der Affirmationen"
            }
    
    async def get_affirmations_by_period(self, period_name: str = None) -> Dict[str, Any]:
        """Get all affirmations, optionally filtered by 7 Cycles period"""
        try:
            filters = None
            if period_name:
                period_number = self._map_period_to_number(period_name)
                filters = {"period": period_number}
            
            affirmations = await self._run_async(
                self.storage.list(
                    self.collection,
                    filters=filters,
                    order_by="created_at",
                    order_desc=True
                )
            )
            
            logger.info(f"[AFFIRMATIONS_AGENT] Retrieved {len(affirmations) if isinstance(affirmations, list) else 'unknown'} affirmations")
            logger.debug(f"[AFFIRMATIONS_AGENT] Affirmations type: {type(affirmations)}")
            if affirmations and isinstance(affirmations, list) and len(affirmations) > 0:
                logger.debug(f"[AFFIRMATIONS_AGENT] First affirmation type: {type(affirmations[0])}")
            
            # Transform storage format to expected format
            formatted_affirmations = []
            for aff in affirmations:
                # Handle case where aff might not be a dict
                if not isinstance(aff, dict):
                    logger.warning(f"[AFFIRMATIONS_AGENT] Unexpected affirmation format: {type(aff)} - {aff}")
                    continue
                    
                formatted = {
                    "id": aff.get("id"),
                    "text": aff.get("affirmation"),
                    "theme": aff.get("theme"),
                    "period_name": aff.get("theme"),
                    "period": aff.get("period"),
                    "created_at": aff.get("created_at"),
                    "language": aff.get("language", "de")
                }
                
                # Add metadata fields if present
                if "metadata" in aff and isinstance(aff["metadata"], dict):
                    formatted["focus"] = aff["metadata"].get("focus")
                    formatted["period_color"] = aff["metadata"].get("period_color")
                    formatted["period_info"] = aff["metadata"].get("period_info")
                
                formatted_affirmations.append(formatted)
            
            return {
                "success": True,
                "affirmations": formatted_affirmations,
                "count": len(formatted_affirmations),
                "period_name": period_name
            }
            
        except Exception as e:
            logger.error(f"[AFFIRMATIONS_AGENT] Error getting affirmations: {e}")
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
                    "keywords": ["Ich bin", "Mein wahres Selbst", "Meine Ausstrahlung", "Meine Identität"],
                    "number": 1
                },
                "Veränderung": {
                    "description": "Transformation, Wandel und Anpassung",
                    "color": "#2196F3",
                    "focus": "Mut zur Veränderung, Flexibilität, Wachstum",
                    "keywords": ["Ich verändere", "Ich wachse", "Neue Wege", "Transformation"],
                    "number": 2
                },
                "Energie": {
                    "description": "Vitalität, Schwung und dynamische Kraft",
                    "color": "#F44336",
                    "focus": "Lebenskraft, Motivation, Ausdauer",
                    "keywords": ["Meine Energie", "Ich bin kraftvoll", "Vitalität", "Schwung"],
                    "number": 3
                },
                "Kreativität": {
                    "description": "Innovation, Inspiration und schöpferischer Ausdruck",
                    "color": "#FFD700",
                    "focus": "Kreative Entfaltung, Inspiration, Innovation",
                    "keywords": ["Ich erschaffe", "Meine Kreativität", "Innovation", "Inspiration"],
                    "number": 4
                },
                "Erfolg": {
                    "description": "Zielerreichung, Leistung und Manifestation",
                    "color": "#CC0066",
                    "focus": "Ziele erreichen, Erfolg manifestieren, Leistung",
                    "keywords": ["Ich erreiche", "Mein Erfolg", "Ziele verwirklichen", "Erfolgreiche Umsetzung"],
                    "number": 5
                },
                "Entspannung": {
                    "description": "Ruhe, Regeneration und innere Balance",
                    "color": "#4CAF50",
                    "focus": "Gelassenheit, Erholung, innere Ruhe",
                    "keywords": ["Ich entspanne", "Innere Ruhe", "Balance", "Gelassenheit"],
                    "number": 6
                },
                "Umsicht": {
                    "description": "Weisheit, Besonnenheit und durchdachte Planung",
                    "color": "#9C27B0",
                    "focus": "Weisheit, kluge Entscheidungen, strategisches Denken",
                    "keywords": ["Ich entscheide weise", "Meine Weisheit", "Besonnenheit", "Klare Sicht"],
                    "number": 7
                }
            }
        }
    
    # Backward compatibility methods
    async def _load_generated_affirmations(self) -> Dict[str, Any]:
        """Legacy method - now uses storage adapter"""
        affirmations = await self._run_async(
            self.storage.list(self.collection)
        )
        
        # Convert to legacy format
        by_period = {}
        for aff in affirmations:
            period_hash = self._generate_affirmation_hash(
                aff.get("theme", ""),
                aff.get("metadata", {}).get("period_info", {})
            )
            if period_hash not in by_period:
                by_period[period_hash] = []
            by_period[period_hash].append(aff)
        
        return {"affirmations": affirmations, "by_period": by_period}
    
    def _save_generated_affirmations(self):
        """Legacy method - no longer needed with storage adapter"""
        pass  # Storage adapter handles persistence automatically