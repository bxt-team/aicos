import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import statistics
from collections import defaultdict


@dataclass
class ImageFeedback:
    image_path: str
    feedback_id: str
    rating: int  # 1-5 scale
    comments: str
    generation_params: Dict[str, Any]
    timestamp: str
    user_id: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class FeedbackCollector:
    def __init__(self, feedback_file: str = "static/image_feedback.json"):
        self.feedback_file = feedback_file
        self.feedback_data = self._load_feedback()
    
    def _load_feedback(self) -> Dict[str, Any]:
        """Load existing feedback data or create new structure."""
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                pass
        
        return {
            "feedback_entries": [],
            "image_ratings": {},
            "prompt_performance": {},
            "style_preferences": {},
            "optimization_metrics": {}
        }
    
    def _save_feedback(self) -> None:
        """Save feedback data to file."""
        os.makedirs(os.path.dirname(self.feedback_file) if os.path.dirname(self.feedback_file) else '.', exist_ok=True)
        with open(self.feedback_file, 'w') as f:
            json.dump(self.feedback_data, f, indent=2)
    
    def add_feedback(self, image_path: str, rating: int, comments: str = "", 
                    generation_params: Dict[str, Any] = None, user_id: str = None,
                    tags: List[str] = None) -> str:
        """Add feedback for a generated image."""
        feedback_id = hashlib.md5(f"{image_path}_{datetime.now().isoformat()}".encode()).hexdigest()
        
        feedback = ImageFeedback(
            image_path=image_path,
            feedback_id=feedback_id,
            rating=rating,
            comments=comments,
            generation_params=generation_params or {},
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            tags=tags or []
        )
        
        self.feedback_data["feedback_entries"].append(feedback.to_dict())
        self.feedback_data["image_ratings"][image_path] = rating
        
        # Update style preferences
        if generation_params and "style" in generation_params:
            style = generation_params["style"]
            if style not in self.feedback_data["style_preferences"]:
                self.feedback_data["style_preferences"][style] = {"ratings": [], "count": 0}
            
            self.feedback_data["style_preferences"][style]["ratings"].append(rating)
            self.feedback_data["style_preferences"][style]["count"] += 1
        
        # Update prompt performance
        if generation_params and "prompt" in generation_params:
            prompt_hash = hashlib.md5(generation_params["prompt"].encode()).hexdigest()
            if prompt_hash not in self.feedback_data["prompt_performance"]:
                self.feedback_data["prompt_performance"][prompt_hash] = {
                    "prompt": generation_params["prompt"],
                    "ratings": [],
                    "count": 0
                }
            
            self.feedback_data["prompt_performance"][prompt_hash]["ratings"].append(rating)
            self.feedback_data["prompt_performance"][prompt_hash]["count"] += 1
        
        self._save_feedback()
        return feedback_id
    
    def get_feedback_for_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """Get feedback for a specific image."""
        for entry in self.feedback_data["feedback_entries"]:
            if entry["image_path"] == image_path:
                return entry
        return None
    
    def get_all_feedback(self) -> List[Dict[str, Any]]:
        """Get all feedback entries."""
        return self.feedback_data["feedback_entries"]


class FeedbackAnalyzer:
    def __init__(self, feedback_collector: FeedbackCollector):
        self.collector = feedback_collector
    
    def analyze_style_preferences(self) -> Dict[str, Any]:
        """Analyze which styles perform best."""
        style_analysis = {}
        
        for style, data in self.collector.feedback_data["style_preferences"].items():
            if data["ratings"]:
                style_analysis[style] = {
                    "average_rating": statistics.mean(data["ratings"]),
                    "count": data["count"],
                    "rating_distribution": {
                        "1": data["ratings"].count(1),
                        "2": data["ratings"].count(2),
                        "3": data["ratings"].count(3),
                        "4": data["ratings"].count(4),
                        "5": data["ratings"].count(5)
                    }
                }
        
        # Sort by average rating
        sorted_styles = sorted(style_analysis.items(), key=lambda x: x[1]["average_rating"], reverse=True)
        
        return {
            "style_rankings": sorted_styles,
            "best_performing_style": sorted_styles[0][0] if sorted_styles else None,
            "style_analysis": style_analysis
        }
    
    def analyze_prompt_performance(self) -> Dict[str, Any]:
        """Analyze which prompts generate better images."""
        prompt_analysis = {}
        
        for prompt_hash, data in self.collector.feedback_data["prompt_performance"].items():
            if data["ratings"]:
                prompt_analysis[prompt_hash] = {
                    "prompt": data["prompt"],
                    "average_rating": statistics.mean(data["ratings"]),
                    "count": data["count"],
                    "rating_distribution": {
                        "1": data["ratings"].count(1),
                        "2": data["ratings"].count(2),
                        "3": data["ratings"].count(3),
                        "4": data["ratings"].count(4),
                        "5": data["ratings"].count(5)
                    }
                }
        
        # Sort by average rating
        sorted_prompts = sorted(prompt_analysis.items(), key=lambda x: x[1]["average_rating"], reverse=True)
        
        return {
            "prompt_rankings": sorted_prompts,
            "best_performing_prompts": sorted_prompts[:5],  # Top 5
            "prompt_analysis": prompt_analysis
        }
    
    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Generate recommendations for improving image generation."""
        style_analysis = self.analyze_style_preferences()
        prompt_analysis = self.analyze_prompt_performance()
        
        recommendations = {
            "preferred_styles": [],
            "avoid_styles": [],
            "prompt_patterns": [],
            "overall_metrics": {}
        }
        
        # Style recommendations
        if style_analysis["style_rankings"]:
            # Best performing styles (rating >= 4.0)
            good_styles = [s for s, data in style_analysis["style_rankings"] if data["average_rating"] >= 4.0]
            recommendations["preferred_styles"] = good_styles
            
            # Poorly performing styles (rating < 3.0)
            poor_styles = [s for s, data in style_analysis["style_rankings"] if data["average_rating"] < 3.0]
            recommendations["avoid_styles"] = poor_styles
        
        # Prompt patterns
        if prompt_analysis["best_performing_prompts"]:
            top_prompts = prompt_analysis["best_performing_prompts"]
            recommendations["prompt_patterns"] = [
                {
                    "prompt": prompt_data["prompt"],
                    "rating": prompt_data["average_rating"],
                    "usage_count": prompt_data["count"]
                }
                for _, prompt_data in top_prompts
            ]
        
        # Overall metrics
        all_ratings = []
        for entry in self.collector.feedback_data["feedback_entries"]:
            all_ratings.append(entry["rating"])
        
        if all_ratings:
            recommendations["overall_metrics"] = {
                "average_rating": statistics.mean(all_ratings),
                "total_feedback_count": len(all_ratings),
                "rating_distribution": {
                    "1": all_ratings.count(1),
                    "2": all_ratings.count(2),
                    "3": all_ratings.count(3),
                    "4": all_ratings.count(4),
                    "5": all_ratings.count(5)
                }
            }
        
        return recommendations
    
    def get_recent_feedback_trends(self, days: int = 7) -> Dict[str, Any]:
        """Analyze feedback trends over recent days."""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_feedback = []
        
        for entry in self.collector.feedback_data["feedback_entries"]:
            entry_date = datetime.fromisoformat(entry["timestamp"])
            if entry_date >= cutoff_date:
                recent_feedback.append(entry)
        
        if not recent_feedback:
            return {"message": f"No feedback found in the last {days} days"}
        
        ratings = [entry["rating"] for entry in recent_feedback]
        
        return {
            "period_days": days,
            "total_feedback": len(recent_feedback),
            "average_rating": statistics.mean(ratings),
            "rating_trend": {
                "1": ratings.count(1),
                "2": ratings.count(2),
                "3": ratings.count(3),
                "4": ratings.count(4),
                "5": ratings.count(5)
            },
            "recent_feedback": recent_feedback
        }


class PromptOptimizer:
    def __init__(self, feedback_analyzer: FeedbackAnalyzer):
        self.analyzer = feedback_analyzer
    
    def optimize_prompt(self, base_prompt: str, style: str = None) -> str:
        """Optimize a prompt based on feedback analysis."""
        recommendations = self.analyzer.get_optimization_recommendations()
        
        optimized_prompt = base_prompt
        
        # Apply style preferences
        if style and style in recommendations["avoid_styles"]:
            # Suggest alternative style
            if recommendations["preferred_styles"]:
                suggested_style = recommendations["preferred_styles"][0]
                optimized_prompt = f"{base_prompt} in {suggested_style} style"
        
        # Apply successful prompt patterns
        if recommendations["prompt_patterns"]:
            top_prompt = recommendations["prompt_patterns"][0]["prompt"]
            
            # Extract common keywords from successful prompts
            common_keywords = self._extract_common_keywords(
                [p["prompt"] for p in recommendations["prompt_patterns"]]
            )
            
            # Add high-performing keywords if not present
            for keyword in common_keywords[:3]:  # Add top 3 keywords
                if keyword.lower() not in optimized_prompt.lower():
                    optimized_prompt += f", {keyword}"
        
        return optimized_prompt
    
    def _extract_common_keywords(self, prompts: List[str]) -> List[str]:
        """Extract common keywords from successful prompts."""
        # Simple keyword extraction - count word frequency
        word_counts = defaultdict(int)
        
        for prompt in prompts:
            words = prompt.lower().split()
            for word in words:
                # Filter out common stop words
                if word not in ['a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']:
                    word_counts[word] += 1
        
        # Return words sorted by frequency
        return sorted(word_counts.keys(), key=lambda x: word_counts[x], reverse=True)
    
    def get_generation_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for next image generation."""
        style_analysis = self.analyzer.analyze_style_preferences()
        
        recommendations = {
            "recommended_style": None,
            "style_confidence": 0.0,
            "prompt_suggestions": [],
            "parameters": {}
        }
        
        # Style recommendation
        if style_analysis["best_performing_style"]:
            best_style = style_analysis["best_performing_style"]
            style_data = style_analysis["style_analysis"][best_style]
            
            recommendations["recommended_style"] = best_style
            recommendations["style_confidence"] = style_data["average_rating"] / 5.0
        
        # Parameter recommendations
        recommendations["parameters"] = {
            "quality": "hd",  # Always use high quality for better feedback
            "size": "1024x1024",  # Standard size for consistent comparison
            "style": recommendations["recommended_style"]
        }
        
        return recommendations