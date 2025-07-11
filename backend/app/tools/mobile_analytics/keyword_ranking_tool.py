import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from crewai.tools import BaseTool
import requests

logger = logging.getLogger(__name__)


class KeywordRankingTool(BaseTool):
    name: str = "Keyword Ranking Analyzer"
    description: str = "Analyzes keyword rankings and suggests optimizations for App Store listings"
    
    def _run(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze keyword effectiveness and rankings.
        
        Args:
            app_data: Dictionary containing app title, subtitle, description, etc.
            
        Returns:
            Dictionary containing keyword analysis and suggestions
        """
        try:
            # Extract text content for analysis
            title = app_data.get("title", "")
            subtitle = app_data.get("subtitle", "")
            description = app_data.get("description", "")
            category = app_data.get("category", "")
            
            # Perform keyword analysis
            analysis = {
                "title_analysis": self._analyze_title(title),
                "subtitle_analysis": self._analyze_subtitle(subtitle),
                "description_analysis": self._analyze_description(description),
                "keyword_density": self._calculate_keyword_density(title, subtitle, description),
                "category_keywords": self._get_category_keywords(category),
                "suggested_keywords": self._suggest_keywords(app_data),
                "competitor_keywords": self._analyze_competitor_keywords(category),
                "optimization_score": self._calculate_optimization_score(app_data)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing keywords: {e}")
            return {"error": str(e)}
    
    def _analyze_title(self, title: str) -> Dict[str, Any]:
        """Analyze app title for keyword optimization."""
        words = title.split()
        
        return {
            "length": len(title),
            "word_count": len(words),
            "character_usage": f"{len(title)}/30",  # App Store limit
            "contains_brand": self._detect_brand(title),
            "keyword_placement": self._analyze_keyword_placement(title),
            "recommendations": self._get_title_recommendations(title)
        }
    
    def _analyze_subtitle(self, subtitle: str) -> Dict[str, Any]:
        """Analyze app subtitle for keyword optimization."""
        if not subtitle:
            return {
                "present": False,
                "recommendation": "Add a subtitle to improve keyword coverage and conversion"
            }
        
        return {
            "present": True,
            "length": len(subtitle),
            "character_usage": f"{len(subtitle)}/30",
            "keyword_relevance": self._calculate_relevance_score(subtitle),
            "action_oriented": self._is_action_oriented(subtitle),
            "recommendations": self._get_subtitle_recommendations(subtitle)
        }
    
    def _analyze_description(self, description: str) -> Dict[str, Any]:
        """Analyze app description for keyword usage."""
        if not description:
            return {"error": "No description provided"}
        
        paragraphs = description.split('\n\n')
        first_paragraph = paragraphs[0] if paragraphs else ""
        
        return {
            "total_length": len(description),
            "paragraph_count": len(paragraphs),
            "first_paragraph_impact": self._analyze_first_paragraph(first_paragraph),
            "keyword_distribution": self._analyze_keyword_distribution(description),
            "readability_score": self._calculate_readability(description),
            "call_to_action": self._detect_cta(description),
            "feature_highlighting": self._analyze_feature_highlighting(description)
        }
    
    def _calculate_keyword_density(self, title: str, subtitle: str, description: str) -> Dict[str, float]:
        """Calculate keyword density across all text fields."""
        combined_text = f"{title} {subtitle} {description}".lower()
        words = combined_text.split()
        word_count = len(words)
        
        if word_count == 0:
            return {}
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            # Skip common words
            if len(word) < 3 or word in self._get_stop_words():
                continue
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Calculate density percentages
        keyword_density = {}
        for word, count in sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]:
            keyword_density[word] = round((count / word_count) * 100, 2)
        
        return keyword_density
    
    def _suggest_keywords(self, app_data: Dict[str, Any]) -> List[str]:
        """Suggest keywords based on app category and content."""
        category = app_data.get("category", "")
        title = app_data.get("title", "")
        
        # Base suggestions on category
        category_keywords = self._get_category_keywords(category)
        
        # Filter out already used keywords
        existing_keywords = set(title.lower().split())
        
        suggestions = [kw for kw in category_keywords if kw.lower() not in existing_keywords]
        
        return suggestions[:10]  # Top 10 suggestions
    
    def _get_category_keywords(self, category: str) -> List[str]:
        """Get relevant keywords for app category."""
        # In a real implementation, this would query a keyword database
        category_keyword_map = {
            "Games": ["fun", "play", "game", "puzzle", "adventure", "multiplayer", "casual", "arcade"],
            "Productivity": ["organize", "task", "manage", "workflow", "efficient", "planner", "schedule"],
            "Social Networking": ["connect", "chat", "share", "friends", "message", "community", "social"],
            "Photo & Video": ["edit", "photo", "video", "camera", "filter", "create", "share", "collage"],
            "Health & Fitness": ["workout", "fitness", "health", "track", "exercise", "diet", "wellness"],
            "Education": ["learn", "study", "course", "tutorial", "skill", "practice", "education"],
            "Finance": ["budget", "money", "invest", "finance", "track", "expense", "save", "banking"],
            "Entertainment": ["watch", "stream", "music", "video", "show", "movie", "listen", "discover"]
        }
        
        return category_keyword_map.get(category, ["app", "mobile", "tool", "utility"])
    
    def _analyze_competitor_keywords(self, category: str) -> Dict[str, Any]:
        """Analyze keywords used by top competitors in category."""
        # In a real implementation, this would analyze actual competitor data
        return {
            "top_competitor_keywords": self._get_category_keywords(category)[:5],
            "unique_opportunity_keywords": ["innovative", "fast", "simple", "powerful"],
            "saturated_keywords": ["best", "top", "free"]
        }
    
    def _calculate_optimization_score(self, app_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall keyword optimization score."""
        score = 100
        issues = []
        
        # Check title optimization
        title_length = len(app_data.get("title", ""))
        if title_length < 15:
            score -= 10
            issues.append("Title too short - not using available characters")
        elif title_length > 30:
            score -= 15
            issues.append("Title exceeds character limit")
        
        # Check subtitle presence
        if not app_data.get("subtitle"):
            score -= 20
            issues.append("No subtitle provided")
        
        # Check description length
        desc_length = len(app_data.get("description", ""))
        if desc_length < 500:
            score -= 15
            issues.append("Description too short - add more detail")
        
        return {
            "score": max(0, score),
            "grade": self._score_to_grade(score),
            "issues": issues,
            "strengths": self._identify_strengths(app_data)
        }
    
    def _score_to_grade(self, score: int) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _identify_strengths(self, app_data: Dict[str, Any]) -> List[str]:
        """Identify optimization strengths."""
        strengths = []
        
        if app_data.get("subtitle"):
            strengths.append("Subtitle is present")
        
        if len(app_data.get("description", "")) > 1000:
            strengths.append("Comprehensive description")
        
        if app_data.get("rating_average", 0) > 4.0:
            strengths.append("High user ratings")
        
        return strengths
    
    def _get_stop_words(self) -> set:
        """Get common stop words to exclude from analysis."""
        return {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "up", "about", "into", "through", "during",
            "before", "after", "above", "below", "between", "under", "again",
            "further", "then", "once", "is", "are", "was", "were", "been", "be",
            "have", "has", "had", "do", "does", "did", "will", "would", "should",
            "could", "may", "might", "must", "can", "this", "that", "these", "those"
        }
    
    def _detect_brand(self, title: str) -> bool:
        """Detect if title contains brand name."""
        # Simple heuristic - first word is often the brand
        return len(title.split()) > 1
    
    def _analyze_keyword_placement(self, title: str) -> str:
        """Analyze keyword placement in title."""
        words = title.split()
        if len(words) < 2:
            return "Too short for analysis"
        
        # Keywords at the beginning have more weight
        return "Good" if len(words[0]) > 3 else "Consider leading with stronger keyword"
    
    def _get_title_recommendations(self, title: str) -> List[str]:
        """Get recommendations for title optimization."""
        recommendations = []
        
        if len(title) < 20:
            recommendations.append("Consider adding descriptive keywords")
        
        if not any(c.isupper() for c in title):
            recommendations.append("Use proper capitalization")
        
        return recommendations
    
    def _calculate_relevance_score(self, text: str) -> float:
        """Calculate keyword relevance score."""
        # Simplified scoring
        return min(100, len(text.split()) * 10)
    
    def _is_action_oriented(self, subtitle: str) -> bool:
        """Check if subtitle contains action-oriented language."""
        action_words = {"create", "build", "manage", "track", "discover", "explore", "find", "get", "make"}
        return any(word in subtitle.lower() for word in action_words)
    
    def _get_subtitle_recommendations(self, subtitle: str) -> List[str]:
        """Get subtitle optimization recommendations."""
        recommendations = []
        
        if len(subtitle) < 20:
            recommendations.append("Use more of the available character limit")
        
        if not self._is_action_oriented(subtitle):
            recommendations.append("Consider adding action-oriented language")
        
        return recommendations
    
    def _analyze_first_paragraph(self, paragraph: str) -> Dict[str, Any]:
        """Analyze the impact of the first paragraph."""
        return {
            "length": len(paragraph),
            "hook_quality": "Good" if len(paragraph) > 50 else "Needs stronger opening",
            "contains_value_prop": self._detect_value_proposition(paragraph)
        }
    
    def _detect_value_proposition(self, text: str) -> bool:
        """Detect if text contains value proposition."""
        value_words = {"best", "unique", "only", "first", "fastest", "easiest", "powerful"}
        return any(word in text.lower() for word in value_words)
    
    def _analyze_keyword_distribution(self, description: str) -> str:
        """Analyze how keywords are distributed in description."""
        paragraphs = description.split('\n')
        if len(paragraphs) < 3:
            return "Limited content for distribution analysis"
        
        # Check if keywords appear throughout
        return "Well distributed" if len(set(paragraphs)) > len(paragraphs) * 0.7 else "Consider better distribution"
    
    def _calculate_readability(self, text: str) -> str:
        """Calculate text readability score."""
        # Simplified readability check
        avg_sentence_length = len(text.split('.')) / max(1, text.count('.'))
        
        if avg_sentence_length < 15:
            return "Excellent"
        elif avg_sentence_length < 25:
            return "Good"
        else:
            return "Consider shorter sentences"
    
    def _detect_cta(self, description: str) -> bool:
        """Detect call-to-action in description."""
        cta_phrases = ["download now", "try today", "get started", "join now", "install today"]
        return any(phrase in description.lower() for phrase in cta_phrases)
    
    def _analyze_feature_highlighting(self, description: str) -> Dict[str, Any]:
        """Analyze how features are highlighted."""
        bullet_points = description.count('•') + description.count('✓') + description.count('-')
        
        return {
            "uses_bullet_points": bullet_points > 0,
            "bullet_count": bullet_points,
            "recommendation": "Good structure" if bullet_points > 3 else "Consider using bullet points for features"
        }