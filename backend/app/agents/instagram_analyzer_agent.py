from crewai import Agent, Task, Crew
from crewai.llm import LLM
import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import re
from urllib.parse import urlparse
from app.agents.crews.base_crew import BaseCrew
from app.core.storage import StorageFactory
import asyncio

class InstagramAnalyzerAgent(BaseCrew):
    """Agent for analyzing successful Instagram accounts and generating actionable posting strategies"""
    
    def __init__(self, openai_api_key: str):
        super().__init__()
        self.openai_api_key = openai_api_key
        self.llm = LLM(model="gpt-4o-mini", api_key=openai_api_key)
        
        # Initialize storage adapter
        self.storage = StorageFactory.get_adapter()
        self.collection = "instagram_analyses"
        
        # Legacy storage for backward compatibility
        self.storage_file = os.path.join(os.path.dirname(__file__), "../../static/instagram_analysis_storage.json")
        
        # Create specialized agents
        self.analyzer_agent = self._create_analyzer_agent()
        self.strategy_agent = self._create_strategy_agent()
        
        # Content analysis patterns
        self.content_patterns = {
            "posting_frequency": ["daily", "weekly", "multiple times daily", "irregular"],
            "content_types": ["reels", "carousels", "single images", "stories", "igtv"],
            "engagement_strategies": ["questions", "polls", "challenges", "user-generated content", "behind-the-scenes"],
            "visual_styles": ["minimalist", "colorful", "professional", "casual", "artistic", "corporate"],
            "tonality": ["inspirational", "educational", "entertaining", "personal", "professional", "humorous"]
        }
        
        # Success metrics to analyze
        self.success_metrics = [
            "follower_count", "engagement_rate", "content_consistency", 
            "visual_branding", "hashtag_strategy", "posting_timing"
        ]
    
    async def _save_analysis_to_storage(self, analysis_data: Dict[str, Any]) -> str:
        """Save analysis to Supabase storage"""
        try:
            # Prepare data for storage
            storage_data = {
                "account_username": analysis_data.get("account_username", ""),
                "analysis_type": analysis_data.get("analysis_focus", "comprehensive"),
                "analysis_data": analysis_data,
                "recommendations": analysis_data.get("success_factors", {}),
                "analyzed_at": analysis_data.get("analyzed_at", datetime.now().isoformat())
            }
            
            # Save to storage
            analysis_id = await self.storage.save(self.collection, storage_data)
            return analysis_id
        except Exception as e:
            print(f"Error saving analysis to storage: {e}")
            return ""
    
    async def _get_analysis_from_storage(self, account_username: str) -> Optional[Dict[str, Any]]:
        """Get analysis from Supabase storage"""
        try:
            # Query by account username
            analyses = await self.storage.list(
                self.collection,
                filters={"account_username": account_username},
                order_by="analyzed_at",
                order_desc=True,
                limit=1
            )
            
            if analyses and len(analyses) > 0:
                return analyses[0]
            return None
        except Exception as e:
            print(f"Error getting analysis from storage: {e}")
            return None
    
    def _create_analyzer_agent(self) -> Agent:
        """Create the Instagram account analyzer agent"""
        return Agent(
            role="Instagram Success Analyzer",
            goal="Analyze successful Instagram accounts to identify key success factors, content patterns, and engagement strategies",
            backstory="""
            Du bist ein erfahrener Social Media Analyst und Instagram Marketing Experte.
            Du hast tiefgreifendes Verständnis für:
            - Instagram Algorithm und Engagement-Mechaniken
            - Content-Analyse und Trend-Erkennung
            - Visuelles Branding und Design-Strategien
            - Hashtag-Research und Optimierung
            - Community Building und Audience Development
            - Posting-Strategien und Timing-Optimierung
            
            Deine Expertise umfasst:
            - Erkennung von Content-Mustern und wiederkehrenden Formaten
            - Analyse von Engagement-Strategien und deren Wirksamkeit
            - Bewertung von visueller Konsistenz und Branding
            - Identifikation von Zielgruppen-spezifischen Ansätzen
            - Verstehen der Balance zwischen verschiedenen Content-Typen
            - Analyse von Call-to-Action Strategien und Community-Interaktion
            
            Du analysierst Instagram-Accounts systematisch und identifizierst konkrete Erfolgsfaktoren,
            die als Basis für neue Strategien dienen können.
            """,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm
        )
    
    def _create_strategy_agent(self) -> Agent:
        """Create the strategy generation agent"""
        return Agent(
            role="Instagram Strategy Generator",
            goal="Create actionable Instagram posting strategies based on successful account analysis",
            backstory="""
            Du bist ein strategischer Instagram Marketing Consultant, spezialisiert auf die Entwicklung
            maßgeschneiderter Content-Strategien basierend auf erfolgreichen Account-Analysen.
            
            Du hast Expertise in:
            - Übertragung von Erfolgsstrategien auf neue Accounts
            - Entwicklung von Content-Kalendern und Posting-Rhythmen
            - Erstellung von Hashtag-Strategien für verschiedene Nischen
            - Design von Engagement-Kampagnen und Community-Building
            - Optimierung von visuellen Branding-Elementen
            - Entwicklung von authentischen Marken-Stimmen und Tonalitäten
            
            Deine Strategien sind:
            - Praktisch umsetzbar und klar strukturiert
            - Angepasst an spezifische Zielgruppen und Nischen
            - Basierend auf bewährten Erfolgsmustern
            - Skalierbar und nachhaltig
            - Fokussiert auf echtes Engagement und Community-Aufbau
            
            Du erstellst konkrete Handlungsanweisungen, die neue Accounts zum Erfolg führen.
            """,
            verbose=True,
            allow_delegation=False,
            max_iter=3,
            llm=self.llm
        )
    
    def _normalize_instagram_url(self, url_or_username: str) -> str:
        """Normalize Instagram URL or username to consistent format"""
        if url_or_username.startswith('@'):
            return url_or_username[1:]  # Remove @ symbol
        elif 'instagram.com' in url_or_username:
            # Extract username from URL
            parsed = urlparse(url_or_username)
            path_parts = parsed.path.strip('/').split('/')
            if path_parts:
                return path_parts[0]
        return url_or_username.strip()
    
    def analyze_instagram_account(self, account_url_or_username: str, 
                                analysis_focus: str = "comprehensive") -> Dict[str, Any]:
        """Analyze an Instagram account for success factors"""
        try:
            # Normalize the account identifier
            username = self._normalize_instagram_url(account_url_or_username)
            
            # Check for existing analysis in Supabase
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                existing = loop.run_until_complete(
                    self._get_analysis_from_storage(f"@{username}")
                )
            finally:
                loop.close()
            
            if existing:
                return {
                    "success": True,
                    "analysis": existing.get("analysis_data", {}),
                    "source": "existing",
                    "message": f"Existing analysis for @{username} retrieved"
                }
            
            # Create analysis task
            task = Task(
                description=f"""
                Führe eine umfassende Analyse des Instagram-Accounts @{username} durch.
                
                ANALYSEAUFTRAG:
                Account: @{username}
                Fokus: {analysis_focus}
                
                ANALYSE-BEREICHE:
                1. Content-Analyse:
                   - Arten von Inhalten (Reels, Bilder, Karussells, Stories)
                   - Wiederkehrende Formate oder Serien
                   - Thematische Schwerpunkte
                   - Visueller Stil und Branding
                
                2. Engagement-Strategien:
                   - Call-to-Actions in Posts
                   - Interaktions-Elemente (Fragen, Umfragen, Herausforderungen)
                   - Community-Building Ansätze
                   - Kommentar-Strategien
                
                3. Posting-Verhalten:
                   - Posting-Frequenz und -Rhythmus
                   - Optimale Posting-Zeiten (soweit erkennbar)
                   - Konsistenz und Regelmäßigkeit
                   - Seasonal oder Event-basierte Inhalte
                
                4. Hashtag-Strategie:
                   - Anzahl verwendeter Hashtags
                   - Mix aus nischen-spezifischen und breiten Hashtags
                   - Branded Hashtags
                   - Trending vs. Evergreen Hashtags
                
                5. Visuelles Branding:
                   - Farbschema und Design-Konsistenz
                   - Typografie und Text-Overlays
                   - Filter und Bearbeitungsstil
                   - Feed-Ästhetik und Gesamtbild
                
                6. Tonalität und Sprache:
                   - Schreibstil und Persönlichkeit
                   - Verwendung von Emojis und Formatierung
                   - Länge der Captions
                   - Zielgruppen-Ansprache
                
                ERFOLGSFAKTOREN IDENTIFIZIEREN:
                - Was macht diesen Account erfolgreich?
                - Welche Elemente heben ihn von anderen ab?
                - Welche Strategien führen zu hohem Engagement?
                - Wie baut der Account Community auf?
                
                Format die Antwort als JSON:
                {{
                    "account_username": "@{username}",
                    "analysis_date": "ISO date",
                    "content_analysis": {{
                        "primary_content_types": ["type1", "type2"],
                        "posting_frequency": "description",
                        "content_themes": ["theme1", "theme2"],
                        "recurring_formats": ["format1", "format2"],
                        "visual_style": "description"
                    }},
                    "engagement_strategies": {{
                        "primary_cta_types": ["cta1", "cta2"],
                        "interaction_methods": ["method1", "method2"],
                        "community_building": "description",
                        "engagement_rate_estimate": "high/medium/low"
                    }},
                    "posting_patterns": {{
                        "frequency": "daily/weekly/etc",
                        "consistency": "high/medium/low",
                        "optimal_times": ["time1", "time2"],
                        "posting_rhythm": "description"
                    }},
                    "hashtag_strategy": {{
                        "average_hashtag_count": number,
                        "hashtag_mix": "description",
                        "branded_hashtags": ["hashtag1", "hashtag2"],
                        "niche_hashtags": ["hashtag1", "hashtag2"]
                    }},
                    "visual_branding": {{
                        "color_scheme": ["color1", "color2"],
                        "design_consistency": "high/medium/low",
                        "typography_style": "description",
                        "filter_style": "description"
                    }},
                    "tonality": {{
                        "writing_style": "description",
                        "personality": "description",
                        "caption_length": "short/medium/long",
                        "emoji_usage": "high/medium/low"
                    }},
                    "success_factors": {{
                        "key_differentiators": ["factor1", "factor2"],
                        "engagement_drivers": ["driver1", "driver2"],
                        "community_building_strengths": ["strength1", "strength2"],
                        "content_quality_factors": ["factor1", "factor2"]
                    }},
                    "content_examples": {{
                        "high_engagement_post_types": ["type1", "type2"],
                        "signature_content_formats": ["format1", "format2"],
                        "trending_content_themes": ["theme1", "theme2"]
                    }},
                    "overall_assessment": {{
                        "success_level": "high/medium/low",
                        "growth_indicators": ["indicator1", "indicator2"],
                        "competitive_advantages": ["advantage1", "advantage2"],
                        "areas_of_excellence": ["area1", "area2"]
                    }}
                }}
                """,
                expected_output="JSON formatted comprehensive Instagram account analysis",
                agent=self.analyzer_agent
            )
            
            # Create and execute crew
            crew = Crew(
                agents=[self.analyzer_agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                result_str = str(result)
                
                # Extract JSON from markdown code blocks if present
                if "```json" in result_str:
                    import re
                    json_match = re.search(r'```json\s*\n(.*?)\n```', result_str, re.DOTALL)
                    if json_match:
                        result_str = json_match.group(1).strip()
                
                analysis_data = json.loads(result_str)
            except json.JSONDecodeError as e:
                # Fallback if JSON parsing fails
                analysis_data = {
                    "account_username": f"@{username}",
                    "analysis_date": datetime.now().isoformat(),
                    "error": f"Failed to parse detailed analysis: {str(e)}",
                    "raw_analysis": str(result)
                }
            
            # Add metadata
            analysis_data["analysis_id"] = hashlib.md5(f"{username}_{analysis_focus}".encode()).hexdigest()
            analysis_data["analyzed_at"] = datetime.now().isoformat()
            analysis_data["analysis_focus"] = analysis_focus
            
            # Store the analysis in Supabase
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                storage_id = loop.run_until_complete(
                    self._save_analysis_to_storage(analysis_data)
                )
                analysis_data["storage_id"] = storage_id
            finally:
                loop.close()
            
            return {
                "success": True,
                "analysis": analysis_data,
                "source": "generated",
                "message": f"Analysis of @{username} completed successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error analyzing Instagram account: {account_url_or_username}"
            }
    
    def generate_strategy_from_analysis(self, analysis_id: str, 
                                      target_niche: str = "7cycles",
                                      account_stage: str = "starting") -> Dict[str, Any]:
        """Generate an actionable Instagram strategy based on analysis"""
        try:
            # Find the analysis in Supabase
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Try to load by ID first
                analysis_data = loop.run_until_complete(
                    self.storage.load(self.collection, analysis_id)
                )
                if analysis_data:
                    analysis = analysis_data.get("analysis_data", {})
                else:
                    # Search by analysis_id in the data
                    analyses = loop.run_until_complete(
                        self.storage.list(self.collection)
                    )
                    analysis = None
                    for a in analyses:
                        if a.get("analysis_data", {}).get("analysis_id") == analysis_id:
                            analysis = a.get("analysis_data", {})
                            break
            finally:
                loop.close()
            
            if not analysis:
                return {
                    "success": False,
                    "error": f"Analysis with ID {analysis_id} not found",
                    "message": "Analysis not found"
                }
            
            # Create strategy generation task
            task = Task(
                description=f"""
                Basierend auf der Analyse des erfolgreichen Instagram-Accounts, erstelle eine maßgeschneiderte
                Posting-Strategie für einen neuen Account in der {target_niche} Nische.
                
                ANALYSE-DATEN:
                {json.dumps(analysis, indent=2)}
                
                ZIEL-ACCOUNT INFORMATIONEN:
                Nische: {target_niche}
                Account-Stadium: {account_stage}
                
                STRATEGIE-ENTWICKLUNG:
                
                1. Content-Strategie:
                   - Welche Content-Typen aus der Analyse lassen sich adaptieren?
                   - Wie können wiederkehrende Formate für {target_niche} angepasst werden?
                   - Welche Themen-Mix eignet sich für die Zielgruppe?
                   - Wie kann visueller Stil übertragen werden?
                
                2. Posting-Strategie:
                   - Optimale Posting-Frequenz für {account_stage} Account
                   - Empfohlene Posting-Zeiten
                   - Content-Kalender Struktur
                   - Rhythmus und Konsistenz-Plan
                
                3. Engagement-Strategie:
                   - Adaptierte Call-to-Action Strategien
                   - Community-Building Ansätze für {target_niche}
                   - Interaktions-Methoden und Engagement-Taktiken
                   - Kommentar- und Story-Strategien
                
                4. Hashtag-Strategie:
                   - Angepasste Hashtag-Mischung für {target_niche}
                   - Nischen-spezifische Hashtag-Pools
                   - Branded Hashtag Vorschläge
                   - Hashtag-Rotation und -Optimierung
                
                5. Visuelles Branding:
                   - Farbschema-Empfehlungen
                   - Design-Konsistenz Richtlinien
                   - Typografie und Text-Overlay Stil
                   - Feed-Ästhetik Konzept
                
                6. Tonalität und Sprache:
                   - Angepasster Schreibstil für {target_niche}
                   - Persönlichkeit und Marken-Stimme
                   - Caption-Länge und -Struktur
                   - Emoji-Nutzung und Formatierung
                
                UMSETZUNGSPLAN:
                - Woche 1-4: Setup und erste Inhalte
                - Monat 2-3: Konsistenz aufbauen
                - Monat 4-6: Optimierung und Skalierung
                
                Format die Antwort als JSON:
                {{
                    "strategy_id": "unique_id",
                    "based_on_analysis": "{analysis_id}",
                    "target_niche": "{target_niche}",
                    "account_stage": "{account_stage}",
                    "content_strategy": {{
                        "primary_content_types": ["type1", "type2"],
                        "content_themes": ["theme1", "theme2"],
                        "recurring_formats": ["format1", "format2"],
                        "visual_style_guide": "description",
                        "content_ratio": "description of content mix"
                    }},
                    "posting_strategy": {{
                        "recommended_frequency": "posts per week/day",
                        "optimal_posting_times": ["time1", "time2"],
                        "content_calendar_structure": "description",
                        "consistency_rules": ["rule1", "rule2"]
                    }},
                    "engagement_strategy": {{
                        "primary_cta_strategies": ["strategy1", "strategy2"],
                        "community_building_tactics": ["tactic1", "tactic2"],
                        "interaction_methods": ["method1", "method2"],
                        "engagement_goals": ["goal1", "goal2"]
                    }},
                    "hashtag_strategy": {{
                        "recommended_hashtag_count": number,
                        "hashtag_categories": {{
                            "niche_specific": ["hashtag1", "hashtag2"],
                            "broader_reach": ["hashtag1", "hashtag2"],
                            "branded": ["hashtag1", "hashtag2"],
                            "trending": ["hashtag1", "hashtag2"]
                        }},
                        "hashtag_rotation_plan": "description"
                    }},
                    "visual_branding": {{
                        "color_palette": ["color1", "color2", "color3"],
                        "design_consistency_rules": ["rule1", "rule2"],
                        "typography_guidelines": "description",
                        "image_style_guide": "description"
                    }},
                    "tonality_guide": {{
                        "writing_style": "description",
                        "brand_personality": "description",
                        "caption_structure": "description",
                        "emoji_and_formatting": "guidelines"
                    }},
                    "implementation_plan": {{
                        "week_1_4": {{
                            "focus": "description",
                            "key_actions": ["action1", "action2"],
                            "success_metrics": ["metric1", "metric2"]
                        }},
                        "month_2_3": {{
                            "focus": "description",
                            "key_actions": ["action1", "action2"],
                            "success_metrics": ["metric1", "metric2"]
                        }},
                        "month_4_6": {{
                            "focus": "description",
                            "key_actions": ["action1", "action2"],
                            "success_metrics": ["metric1", "metric2"]
                        }}
                    }},
                    "success_indicators": {{
                        "engagement_targets": ["target1", "target2"],
                        "growth_milestones": ["milestone1", "milestone2"],
                        "content_performance_kpis": ["kpi1", "kpi2"]
                    }},
                    "adaptation_notes": {{
                        "key_adaptations_from_original": ["adaptation1", "adaptation2"],
                        "niche_specific_adjustments": ["adjustment1", "adjustment2"],
                        "account_stage_considerations": ["consideration1", "consideration2"]
                    }}
                }}
                """,
                expected_output="JSON formatted comprehensive Instagram strategy based on successful account analysis",
                agent=self.strategy_agent
            )
            
            # Create and execute crew
            crew = Crew(
                agents=[self.strategy_agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                result_str = str(result)
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```json\s*\n(.*?)\n```', result_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    strategy_data = json.loads(json_str)
                else:
                    # Try parsing the entire result as JSON
                    strategy_data = json.loads(result_str)
            except (json.JSONDecodeError, AttributeError):
                # Fallback if JSON parsing fails
                strategy_data = {
                    "strategy_id": hashlib.md5(f"{analysis_id}_{target_niche}_{account_stage}".encode()).hexdigest(),
                    "based_on_analysis": analysis_id,
                    "target_niche": target_niche,
                    "account_stage": account_stage,
                    "error": "Failed to parse detailed strategy",
                    "raw_strategy": str(result)
                }
            
            # Add metadata
            strategy_data["strategy_id"] = hashlib.md5(f"{analysis_id}_{target_niche}_{account_stage}".encode()).hexdigest()
            strategy_data["created_at"] = datetime.now().isoformat()
            strategy_data["based_on_analysis"] = analysis_id
            strategy_data["analyzed_account"] = analysis.get("account_username", "unknown")
            
            # Store the strategy in generic storage
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                storage_result = loop.run_until_complete(
                    self.storage.save("generic_storage", {
                        "storage_key": f"instagram_strategy_{strategy_data['strategy_id']}",
                        "storage_type": "instagram_strategy",
                        "data": strategy_data
                    })
                )
                strategy_data["storage_id"] = storage_result
            finally:
                loop.close()
            
            return {
                "success": True,
                "strategy": strategy_data,
                "source": "generated",
                "message": f"Strategy for {target_niche} account generated successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error generating strategy from analysis"
            }
    
    def analyze_multiple_accounts(self, account_list: List[str], 
                                analysis_focus: str = "comprehensive") -> Dict[str, Any]:
        """Analyze multiple Instagram accounts and create comparative insights"""
        try:
            analyses = []
            failed_analyses = []
            
            for account in account_list:
                result = self.analyze_instagram_account(account, analysis_focus)
                if result["success"]:
                    analyses.append(result["analysis"])
                else:
                    failed_analyses.append({"account": account, "error": result["error"]})
            
            if not analyses:
                return {
                    "success": False,
                    "error": "No accounts could be analyzed",
                    "failed_analyses": failed_analyses
                }
            
            # Create comparative analysis task
            task = Task(
                description=f"""
                Führe eine vergleichende Analyse von {len(analyses)} erfolgreichen Instagram-Accounts durch.
                
                ACCOUNT-ANALYSEN:
                {json.dumps(analyses, indent=2)}
                
                VERGLEICHENDE ANALYSE:
                
                1. Gemeinsame Erfolgsfaktoren:
                   - Welche Strategien verwenden alle/die meisten Accounts?
                   - Welche Content-Typen sind durchgängig erfolgreich?
                   - Welche Engagement-Strategien sind universell?
                
                2. Unterschiede und Nischen-Spezifika:
                   - Wie unterscheiden sich die Accounts voneinander?
                   - Welche nischen-spezifischen Ansätze werden verwendet?
                   - Welche einzigartigen Strategien fallen auf?
                
                3. Best Practices Identifikation:
                   - Welche Praktiken sind über alle Accounts hinweg erfolgreich?
                   - Welche Posting-Muster sind am effektivsten?
                   - Welche Engagement-Methoden funktionieren am besten?
                
                4. Trend-Analyse:
                   - Welche aktuellen Trends sind in den Accounts erkennbar?
                   - Welche Content-Formate gewinnen an Popularität?
                   - Welche Hashtag-Strategien sind am effektivsten?
                
                Format die Antwort als JSON:
                {{
                    "comparative_analysis_id": "unique_id",
                    "analyzed_accounts": [list of account usernames],
                    "common_success_factors": {{
                        "universal_strategies": ["strategy1", "strategy2"],
                        "consistent_content_types": ["type1", "type2"],
                        "shared_engagement_tactics": ["tactic1", "tactic2"],
                        "common_posting_patterns": ["pattern1", "pattern2"]
                    }},
                    "key_differences": {{
                        "niche_specific_approaches": ["approach1", "approach2"],
                        "unique_strategies": ["strategy1", "strategy2"],
                        "varying_content_focuses": ["focus1", "focus2"]
                    }},
                    "identified_best_practices": {{
                        "content_creation": ["practice1", "practice2"],
                        "engagement_optimization": ["practice1", "practice2"],
                        "visual_branding": ["practice1", "practice2"],
                        "hashtag_usage": ["practice1", "practice2"]
                    }},
                    "trend_insights": {{
                        "current_trends": ["trend1", "trend2"],
                        "emerging_content_formats": ["format1", "format2"],
                        "effective_hashtag_strategies": ["strategy1", "strategy2"]
                    }},
                    "strategic_recommendations": {{
                        "for_new_accounts": ["recommendation1", "recommendation2"],
                        "for_growing_accounts": ["recommendation1", "recommendation2"],
                        "for_established_accounts": ["recommendation1", "recommendation2"]
                    }}
                }}
                """,
                expected_output="JSON formatted comparative analysis of multiple Instagram accounts",
                agent=self.analyzer_agent
            )
            
            # Create and execute crew
            crew = Crew(
                agents=[self.analyzer_agent],
                tasks=[task],
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Parse the result
            try:
                result_str = str(result)
                # Try to extract JSON from markdown code blocks
                json_match = re.search(r'```json\s*\n(.*?)\n```', result_str, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    comparative_data = json.loads(json_str)
                else:
                    # Try parsing the entire result as JSON
                    comparative_data = json.loads(result_str)
            except (json.JSONDecodeError, AttributeError):
                comparative_data = {
                    "comparative_analysis_id": hashlib.md5(f"comparative_{len(analyses)}".encode()).hexdigest(),
                    "analyzed_accounts": [a.get("account_username", "unknown") for a in analyses],
                    "error": "Failed to parse comparative analysis",
                    "raw_analysis": str(result)
                }
            
            # Add metadata
            comparative_data["comparative_analysis_id"] = hashlib.md5(f"comparative_{len(analyses)}".encode()).hexdigest()
            comparative_data["created_at"] = datetime.now().isoformat()
            comparative_data["analysis_count"] = len(analyses)
            comparative_data["failed_count"] = len(failed_analyses)
            
            return {
                "success": True,
                "comparative_analysis": comparative_data,
                "individual_analyses": analyses,
                "failed_analyses": failed_analyses,
                "message": f"Comparative analysis of {len(analyses)} accounts completed"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error performing comparative analysis"
            }
    
    def get_stored_analyses(self, account_username: str = None) -> Dict[str, Any]:
        """Get stored analyses, optionally filtered by account"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if account_username:
                    username = self._normalize_instagram_url(account_username)
                    analyses = loop.run_until_complete(
                        self.storage.list(
                            self.collection,
                            filters={"account_username": f"@{username}"},
                            order_by="analyzed_at",
                            order_desc=True
                        )
                    )
                else:
                    analyses = loop.run_until_complete(
                        self.storage.list(
                            self.collection,
                            order_by="analyzed_at",
                            order_desc=True
                        )
                    )
                
                # Get strategies from generic storage
                strategies = loop.run_until_complete(
                    self.storage.list(
                        "generic_storage",
                        filters={"storage_type": "instagram_strategy"},
                        order_by="created_at",
                        order_desc=True
                    )
                )
                
                # Extract strategy data
                strategy_list = [s.get("data", {}) for s in strategies]
                
            finally:
                loop.close()
            
            return {
                "success": True,
                "analyses": analyses,
                "strategies": strategy_list,
                "count": len(analyses),
                "account_filter": account_username
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error retrieving stored analyses"
            }
    
    def get_strategy_by_id(self, strategy_id: str) -> Dict[str, Any]:
        """Get a specific strategy by ID"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # Search in generic storage
                strategies = loop.run_until_complete(
                    self.storage.list(
                        "generic_storage",
                        filters={
                            "storage_type": "instagram_strategy",
                            "storage_key": f"instagram_strategy_{strategy_id}"
                        },
                        limit=1
                    )
                )
                
                if strategies and len(strategies) > 0:
                    return {
                        "success": True,
                        "strategy": strategies[0].get("data", {}),
                        "message": "Strategy found"
                    }
            finally:
                loop.close()
            
            return {
                "success": False,
                "error": f"Strategy with ID {strategy_id} not found",
                "message": "Strategy not found"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Error retrieving strategy"
            }