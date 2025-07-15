import json
import logging
import re
import os
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI

from app.agents.crews.base_crew import BaseCrew
from app.tools.mobile_analytics.play_store_api_tool import PlayStoreAPITool
from app.tools.mobile_analytics.keyword_ranking_tool import KeywordRankingTool
from app.tools.mobile_analytics.review_extractor_tool import ReviewExtractorTool
from app.models.mobile_analytics.play_store_analysis import PlayStoreAnalysis

logger = logging.getLogger(__name__)


class PlayStoreAnalystAgent(BaseCrew):
    """Agent for analyzing Android Play Store listings for ASO performance."""
    
    def __init__(self):
        super().__init__()
        self.memory = {}  # Store baseline performance data
        
    def health_check(self) -> Dict[str, Any]:
        """Check if the agent is ready to work."""
        return {
            "agent": "PlayStoreAnalystAgent",
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "capabilities": [
                "play_store_scraping",
                "keyword_analysis",
                "review_sentiment",
                "competitor_analysis",
                "visual_quality_assessment"
            ]
        }
    
    def create_agents(self) -> List[Agent]:
        """Create specialized agents for Play Store analysis."""
        
        llm = ChatOpenAI(model="gpt-4", temperature=0.1)
        
        # Listing Analyzer Agent
        listing_analyzer = Agent(
            role="Play Store Listing Analyst",
            goal="Analyze Play Store listings for keyword effectiveness, visual quality, and metadata optimization",
            backstory="""You are an expert in Android App Store Optimization (ASO) with years of experience 
            analyzing successful apps on Google Play. You understand how Google's search algorithm works and can 
            identify opportunities for improvement in app listings.""",
            tools=[PlayStoreAPITool(), KeywordRankingTool()],
            llm=llm,
            verbose=True
        )
        
        # Review Analyst Agent
        review_analyst = Agent(
            role="Play Store Review Analyst",
            goal="Analyze user reviews to identify sentiment, pain points, and feature requests",
            backstory="""You specialize in analyzing Play Store reviews to extract actionable insights. 
            You can identify patterns in user feedback and prioritize issues based on their impact.""",
            tools=[ReviewExtractorTool()],
            llm=llm,
            verbose=True
        )
        
        # Optimization Strategist Agent
        optimization_strategist = Agent(
            role="Play Store ASO Strategist",
            goal="Create data-driven optimization strategies for Play Store listings",
            backstory="""You are a strategic thinker who combines ASO best practices with data analysis 
            to create actionable optimization plans. You understand Play Store ranking factors and can 
            prioritize improvements based on potential impact.""",
            tools=[],
            llm=llm,
            verbose=True
        )
        
        return [listing_analyzer, review_analyst, optimization_strategist]
    
    def create_tasks(self, app_info: Dict[str, Any]) -> List[Task]:
        """Create tasks for comprehensive Play Store analysis."""
        
        agents = self.create_agents()
        listing_analyzer = agents[0]
        review_analyst = agents[1]
        optimization_strategist = agents[2]
        
        # Task 1: Scrape and analyze listing
        scrape_task = Task(
            description=f"""
            Analyze the Play Store listing for the app:
            {json.dumps(app_info, indent=2)}
            
            Extract and analyze:
            1. App title, subtitle, and description
            2. Keywords used in metadata
            3. Visual assets quality (icon, screenshots, feature graphic)
            4. Category and competitors
            5. Download count and ratings
            6. Update frequency and developer responsiveness
            
            Provide a comprehensive analysis of the listing's strengths and weaknesses.
            """,
            agent=listing_analyzer,
            expected_output="Detailed analysis of Play Store listing elements"
        )
        
        # Task 2: Analyze reviews
        review_task = Task(
            description=f"""
            Extract and analyze user reviews for the app using the app information:
            {json.dumps(app_info, indent=2)}
            
            Use the Review Extractor and Analyzer tool to:
            1. Fetch reviews for the app
            2. Analyze overall sentiment distribution
            3. Identify most common complaints and pain points
            4. Find most praised features
            5. Extract feature requests from users
            6. Look for version-specific issues
            7. Find competitor mentions
            
            Focus on actionable insights that can improve the app and its listing.
            """,
            agent=review_analyst,
            expected_output="Comprehensive review analysis with sentiment and insights"
        )
        
        # Task 3: Create optimization strategy
        optimization_task = Task(
            description=f"""
            Based on the listing analysis and review insights, create a comprehensive 
            Play Store optimization strategy:
            
            1. Keyword optimization recommendations
            2. Metadata improvements (title, short description, full description)
            3. Visual asset recommendations
            4. Review response strategies
            5. Competitive positioning
            6. Localization opportunities
            
            Prioritize recommendations by expected impact and implementation difficulty.
            """,
            agent=optimization_strategist,
            expected_output="Actionable Play Store optimization strategy with prioritized recommendations"
        )
        
        return [scrape_task, review_task, optimization_task]
    
    async def analyze_listing(self, app_info: Dict[str, Any]) -> PlayStoreAnalysis:
        """Analyze a Play Store listing comprehensively."""
        try:
            logger.info(f"Starting Play Store analysis for: {app_info}")
            
            # Create and run the crew
            agents = self.create_agents()
            tasks = self.create_tasks(app_info)
            
            crew = Crew(
                agents=agents,
                tasks=tasks,
                verbose=True
            )
            
            result = crew.kickoff()
            
            # Track costs for this analysis
            cost_info = self.track_crew_costs(
                crew_result=result,
                agent_name="PlayStoreAnalystAgent",
                model="gpt-4",
                task_description=f"Play Store analysis for {app_info.get('package_name', 'unknown app')}"
            )
            
            # Parse and structure the results
            analysis = self._parse_crew_results(result, app_info)
            
            # Add cost information to analysis
            if cost_info:
                analysis.cost_estimate = cost_info.get("cost_estimate", {})
                logger.info(f"Analysis cost: ${cost_info['cost_estimate']['estimated_cost']:.4f}")
            
            # Save the analysis to storage
            self._save_analysis(analysis)
            
            logger.info("Play Store analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in Play Store analysis: {e}")
            raise
    
    def _parse_crew_results(self, crew_result: Any, app_info: Dict[str, Any]) -> PlayStoreAnalysis:
        """Parse crew results into structured PlayStoreAnalysis model."""
        
        # Extract results from crew output
        results_text = str(crew_result)
        
        # Extract package name from URL if not provided directly
        package_name = app_info.get("package_name")
        if not package_name and app_info.get("url"):
            # Extract from Play Store URL pattern: ...id=com.example.app
            match = re.search(r'id=([a-zA-Z0-9._]+)', app_info.get("url", ""))
            if match:
                package_name = match.group(1)
        
        # Ensure we have a valid package name
        if not package_name:
            package_name = "unknown.package"
        
        # Create structured analysis
        # Note: In a real implementation, this would parse the actual crew output
        # For now, we'll create a sample structure
        
        analysis = PlayStoreAnalysis(
            app_id=package_name,  # Use package_name as app_id for Play Store
            app_name=app_info.get("app_name", "Unknown App"),
            package_name=package_name,
            developer=app_info.get("developer", "Unknown Developer"),
            category=app_info.get("category", "Unknown"),
            rating=4.2,
            total_reviews=15000,
            downloads="100,000+",
            last_updated=datetime.now().isoformat(),
            
            # Keyword Analysis
            keyword_analysis={
                "primary_keywords": ["keyword1", "keyword2", "keyword3"],
                "keyword_density": {
                    "title": 0.3,
                    "short_description": 0.25,
                    "description": 0.15
                },
                "competitor_keywords": ["competitor1", "competitor2"],
                "suggested_keywords": ["suggestion1", "suggestion2", "suggestion3"],
                "keyword_opportunities": [
                    {
                        "keyword": "new_keyword",
                        "search_volume": "high",
                        "competition": "medium",
                        "relevance": 0.85
                    }
                ]
            },
            
            # Review Sentiment
            review_sentiment={
                "overall_sentiment": 0.72,
                "sentiment_label": "Positive",
                "positive_percentage": 72,
                "neutral_percentage": 18,
                "negative_percentage": 10,
                "pain_points": [
                    {
                        "issue": "App crashes",
                        "frequency": 45,
                        "severity": "High",
                        "percentage_of_negative": 35
                    }
                ],
                "positive_highlights": [
                    {
                        "aspect": "User interface",
                        "mentions": 120,
                        "percentage_of_positive": 25
                    }
                ],
                "feature_requests": [
                    {
                        "feature": "Dark mode",
                        "mentions": 80,
                        "priority": "High"
                    }
                ]
            },
            
            # Visual Analysis
            visual_analysis={
                "icon_quality": {
                    "score": 8.5,
                    "recommendations": ["Consider updating icon design for better visibility"]
                },
                "screenshots": {
                    "count": 6,
                    "quality_score": 7.8,
                    "recommendations": ["Add more screenshots showing key features"]
                },
                "feature_graphic": {
                    "present": True,
                    "quality_score": 8.0,
                    "recommendations": []
                },
                "promo_video": {
                    "present": False,
                    "recommendations": ["Add a promotional video to increase conversions"]
                }
            },
            
            # Recommendations
            recommendations=[
                {
                    "category": "Keywords",
                    "recommendation": "Add 'new_keyword' to your title for better visibility",
                    "priority": "high",
                    "expected_impact": "15-20% increase in organic traffic",
                    "implementation_difficulty": "easy"
                },
                {
                    "category": "Reviews",
                    "recommendation": "Address app crash issues mentioned in 35% of negative reviews",
                    "priority": "critical",
                    "expected_impact": "Improve rating from 4.2 to 4.5+",
                    "implementation_difficulty": "medium"
                },
                {
                    "category": "Visuals",
                    "recommendation": "Add a promotional video showcasing key features",
                    "priority": "medium",
                    "expected_impact": "10-15% increase in conversion rate",
                    "implementation_difficulty": "medium"
                }
            ],
            
            # Competitor Analysis
            competitor_analysis={
                "top_competitors": ["com.competitor1", "com.competitor2"],
                "competitive_advantages": ["Better UI", "More features"],
                "competitive_weaknesses": ["Higher price", "Less frequent updates"],
                "market_position": "3rd in category"
            },
            
            analysis_timestamp=datetime.now().isoformat()
        )
        
        return analysis
    
    def get_historical_performance(self, app_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get historical performance data for an app."""
        
        # In a real implementation, this would fetch from a database
        # For now, return sample data
        
        if app_id not in self.memory:
            return None
        
        return self.memory.get(app_id, {}).get("historical_data", [])
    
    def compare_apps(self, app_ids: List[str]) -> Dict[str, Any]:
        """Compare multiple apps for competitive analysis."""
        
        comparison = {
            "comparison_date": datetime.now().isoformat(),
            "apps_compared": len(app_ids),
            "metrics": {
                "ratings": {},
                "downloads": {},
                "keywords": {},
                "update_frequency": {}
            }
        }
        
        # In a real implementation, this would fetch and compare data
        # For now, return the structure
        
        return comparison
    
    def _save_analysis(self, analysis: PlayStoreAnalysis) -> str:
        """Save analysis to storage and return the analysis ID."""
        analysis_id = str(uuid.uuid4())
        storage_dir = "storage/mobile_analytics/play_store"
        os.makedirs(storage_dir, exist_ok=True)
        
        # Add analysis ID to the data
        analysis_data = analysis.dict()
        analysis_data["analysis_id"] = analysis_id
        
        # Save to file
        file_path = os.path.join(storage_dir, f"{analysis_id}.json")
        with open(file_path, "w") as f:
            json.dump(analysis_data, f, indent=2)
        
        logger.info(f"Saved Play Store analysis to {file_path}")
        return analysis_id
    
    def get_all_analyses(self) -> List[Dict[str, Any]]:
        """Get all saved Play Store analyses."""
        storage_dir = "storage/mobile_analytics/play_store"
        if not os.path.exists(storage_dir):
            return []
        
        analyses = []
        for filename in os.listdir(storage_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(storage_dir, filename)
                try:
                    with open(file_path, "r") as f:
                        analysis_data = json.load(f)
                        # Add summary info for list view
                        analyses.append({
                            "analysis_id": analysis_data.get("analysis_id"),
                            "app_name": analysis_data.get("app_name"),
                            "package_name": analysis_data.get("package_name"),
                            "rating": analysis_data.get("rating"),
                            "analysis_timestamp": analysis_data.get("analysis_timestamp"),
                            "recommendation_count": len(analysis_data.get("recommendations", []))
                        })
                except Exception as e:
                    logger.error(f"Error reading analysis file {filename}: {e}")
        
        # Sort by timestamp, newest first
        analyses.sort(key=lambda x: x.get("analysis_timestamp", ""), reverse=True)
        return analyses
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific Play Store analysis by ID."""
        file_path = f"storage/mobile_analytics/play_store/{analysis_id}.json"
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading analysis {analysis_id}: {e}")
            return None
    
    def delete_analysis(self, analysis_id: str) -> bool:
        """Delete a Play Store analysis by ID."""
        file_path = f"storage/mobile_analytics/play_store/{analysis_id}.json"
        
        if not os.path.exists(file_path):
            logger.warning(f"Analysis {analysis_id} not found for deletion")
            return False
        
        try:
            os.remove(file_path)
            logger.info(f"Deleted Play Store analysis: {analysis_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting analysis {analysis_id}: {e}")
            return False