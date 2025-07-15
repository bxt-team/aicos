import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from collections import Counter
import re
from crewai.tools import BaseTool
from textblob import TextBlob

logger = logging.getLogger(__name__)


class SentimentAnalysisTool(BaseTool):
    name: str = "Review Sentiment Analyzer"
    description: str = "Analyzes user reviews for sentiment, themes, and insights"
    
    def _run(self, reviews: Any) -> Dict[str, Any]:
        """
        Analyze reviews for sentiment and extract insights.
        
        Args:
            reviews: List of review dictionaries with 'text', 'rating', 'date' fields
                    OR a dict/string that needs to be processed first
            
        Returns:
            Dictionary containing sentiment analysis and insights
        """
        try:
            # Handle different input types
            if isinstance(reviews, str):
                return {"error": "String input not supported. Please provide a list of reviews or use ReviewExtractorTool."}
            
            if isinstance(reviews, dict):
                # Check if it's a single review
                if "text" in reviews and "rating" in reviews:
                    reviews = [reviews]
                else:
                    return {"error": "Invalid input format. Expected list of reviews but got dict. Use ReviewExtractorTool for app data."}
            
            if not isinstance(reviews, list):
                return {"error": f"Invalid input type: {type(reviews)}. Expected list of reviews."}
            
            if not reviews:
                return {"error": "No reviews provided for analysis"}
            
            # Validate review format
            valid_reviews = []
            for review in reviews:
                if isinstance(review, dict) and "text" in review:
                    valid_reviews.append(review)
            
            if not valid_reviews:
                return {"error": "No valid reviews found. Each review must be a dict with at least a 'text' field."}
            
            reviews = valid_reviews
            
            # Perform comprehensive analysis
            analysis = {
                "total_reviews_analyzed": len(reviews),
                "sentiment_summary": self._analyze_overall_sentiment(reviews),
                "rating_distribution": self._analyze_rating_distribution(reviews),
                "sentiment_by_rating": self._analyze_sentiment_by_rating(reviews),
                "common_themes": self._extract_common_themes(reviews),
                "feature_sentiment": self._analyze_feature_sentiment(reviews),
                "temporal_analysis": self._analyze_temporal_trends(reviews),
                "user_pain_points": self._identify_pain_points(reviews),
                "positive_highlights": self._extract_positive_highlights(reviews),
                "improvement_suggestions": self._extract_improvement_suggestions(reviews),
                "competitive_mentions": self._find_competitor_mentions(reviews)
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"error": str(e)}
    
    def _analyze_overall_sentiment(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall sentiment metrics."""
        sentiments = []
        
        for review in reviews:
            text = review.get("text", "")
            if text:
                blob = TextBlob(text)
                sentiments.append(blob.sentiment.polarity)
        
        if not sentiments:
            return {"error": "No text content to analyze"}
        
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        # Categorize sentiment
        positive = sum(1 for s in sentiments if s > 0.1)
        negative = sum(1 for s in sentiments if s < -0.1)
        neutral = len(sentiments) - positive - negative
        
        return {
            "average_sentiment": round(avg_sentiment, 3),
            "sentiment_label": self._get_sentiment_label(avg_sentiment),
            "distribution": {
                "positive": positive,
                "negative": negative,
                "neutral": neutral,
                "positive_percentage": round((positive / len(sentiments)) * 100, 1),
                "negative_percentage": round((negative / len(sentiments)) * 100, 1),
                "neutral_percentage": round((neutral / len(sentiments)) * 100, 1)
            }
        }
    
    def _analyze_rating_distribution(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze distribution of ratings."""
        ratings = [r.get("rating", 0) for r in reviews if r.get("rating")]
        
        if not ratings:
            return {"error": "No ratings found"}
        
        rating_counts = Counter(ratings)
        total = len(ratings)
        
        distribution = {}
        for rating in range(1, 6):
            count = rating_counts.get(rating, 0)
            distribution[f"{rating}_star"] = {
                "count": count,
                "percentage": round((count / total) * 100, 1)
            }
        
        return {
            "average_rating": round(sum(ratings) / len(ratings), 2),
            "distribution": distribution,
            "mode_rating": max(rating_counts, key=rating_counts.get),
            "total_ratings": total
        }
    
    def _analyze_sentiment_by_rating(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment grouped by rating."""
        rating_sentiments = {1: [], 2: [], 3: [], 4: [], 5: []}
        
        for review in reviews:
            rating = review.get("rating")
            text = review.get("text", "")
            
            if rating and text:
                blob = TextBlob(text)
                sentiment = blob.sentiment.polarity
                if rating in rating_sentiments:
                    rating_sentiments[rating].append(sentiment)
        
        # Calculate average sentiment per rating
        results = {}
        for rating, sentiments in rating_sentiments.items():
            if sentiments:
                avg = sum(sentiments) / len(sentiments)
                results[f"{rating}_star"] = {
                    "average_sentiment": round(avg, 3),
                    "sentiment_label": self._get_sentiment_label(avg),
                    "review_count": len(sentiments),
                    "sentiment_consistency": self._check_sentiment_consistency(rating, avg)
                }
        
        return results
    
    def _extract_common_themes(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract common themes from reviews."""
        # Combine all review texts
        all_text = " ".join(r.get("text", "") for r in reviews)
        
        # Extract noun phrases as potential themes
        blob = TextBlob(all_text.lower())
        noun_phrases = [str(np) for np in blob.noun_phrases]
        
        # Count occurrences
        theme_counts = Counter(noun_phrases)
        
        # Get top themes
        top_themes = []
        for theme, count in theme_counts.most_common(15):
            if count > 2 and len(theme.split()) <= 3:  # Filter noise
                # Analyze sentiment for this theme
                theme_sentiment = self._analyze_theme_sentiment(theme, reviews)
                
                top_themes.append({
                    "theme": theme,
                    "mentions": count,
                    "sentiment": theme_sentiment,
                    "category": self._categorize_theme(theme)
                })
        
        return top_themes
    
    def _analyze_feature_sentiment(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze sentiment for specific app features."""
        # Common app feature keywords
        features = {
            "ui": ["ui", "interface", "design", "layout", "look", "appearance"],
            "performance": ["fast", "slow", "speed", "performance", "lag", "crash", "bug"],
            "usability": ["easy", "difficult", "simple", "complex", "intuitive", "confusing"],
            "functionality": ["feature", "function", "work", "useful", "helpful"],
            "price": ["price", "cost", "expensive", "cheap", "value", "worth"],
            "support": ["support", "help", "response", "customer service"],
            "content": ["content", "data", "information", "quality"],
            "updates": ["update", "version", "new", "change", "improvement"]
        }
        
        feature_sentiments = {}
        
        for feature_name, keywords in features.items():
            sentiments = []
            mentions = 0
            
            for review in reviews:
                text = review.get("text", "").lower()
                
                # Check if review mentions this feature
                if any(keyword in text for keyword in keywords):
                    mentions += 1
                    
                    # Extract sentences mentioning the feature
                    sentences = text.split('.')
                    for sentence in sentences:
                        if any(keyword in sentence for keyword in keywords):
                            blob = TextBlob(sentence)
                            sentiments.append(blob.sentiment.polarity)
            
            if sentiments:
                avg_sentiment = sum(sentiments) / len(sentiments)
                feature_sentiments[feature_name] = {
                    "mentions": mentions,
                    "average_sentiment": round(avg_sentiment, 3),
                    "sentiment_label": self._get_sentiment_label(avg_sentiment),
                    "sample_size": len(sentiments)
                }
        
        return feature_sentiments
    
    def _analyze_temporal_trends(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze how sentiment changes over time."""
        # Group reviews by time period
        time_periods = {}
        
        for review in reviews:
            date_str = review.get("date")
            if date_str:
                try:
                    # Parse date and group by month
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    period_key = date.strftime("%Y-%m")
                    
                    if period_key not in time_periods:
                        time_periods[period_key] = []
                    
                    text = review.get("text", "")
                    if text:
                        blob = TextBlob(text)
                        time_periods[period_key].append({
                            "sentiment": blob.sentiment.polarity,
                            "rating": review.get("rating", 0)
                        })
                except:
                    continue
        
        # Calculate trends
        trends = {}
        for period, data in sorted(time_periods.items()):
            if data:
                sentiments = [d["sentiment"] for d in data]
                ratings = [d["rating"] for d in data if d["rating"]]
                
                trends[period] = {
                    "average_sentiment": round(sum(sentiments) / len(sentiments), 3),
                    "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
                    "review_count": len(data)
                }
        
        return {
            "monthly_trends": trends,
            "trend_direction": self._calculate_trend_direction(trends)
        }
    
    def _identify_pain_points(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify common user pain points from negative reviews."""
        pain_points = []
        negative_reviews = [r for r in reviews if r.get("rating", 5) <= 2]
        
        # Common pain point patterns
        pain_patterns = {
            "crashes": r"crash|freeze|hang|stop working|force close",
            "bugs": r"bug|glitch|error|issue|problem",
            "performance": r"slow|lag|delay|takes forever|loading",
            "battery": r"battery|drain|power",
            "data_usage": r"data usage|bandwidth|mb|gb",
            "ads": r"ads|advertisement|annoying ads|too many ads",
            "subscription": r"subscription|payment|charge|expensive",
            "missing_features": r"missing|lack|need|want|wish|should have",
            "sync_issues": r"sync|synchronize|backup|lost data",
            "login_problems": r"login|sign in|password|account"
        }
        
        for pattern_name, pattern in pain_patterns.items():
            matches = []
            
            for review in negative_reviews:
                text = review.get("text", "")
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(text)
            
            if matches:
                pain_points.append({
                    "issue": pattern_name.replace("_", " ").title(),
                    "frequency": len(matches),
                    "percentage_of_negative": round((len(matches) / len(negative_reviews)) * 100, 1),
                    "severity": self._calculate_severity(pattern_name, matches),
                    "sample_complaints": matches[:3]  # First 3 examples
                })
        
        # Sort by frequency
        pain_points.sort(key=lambda x: x["frequency"], reverse=True)
        
        return pain_points[:10]  # Top 10 pain points
    
    def _extract_positive_highlights(self, reviews: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract what users love about the app."""
        positive_reviews = [r for r in reviews if r.get("rating", 0) >= 4]
        
        # Positive sentiment patterns
        love_patterns = {
            "ease_of_use": r"easy to use|simple|intuitive|user friendly",
            "great_design": r"beautiful|great design|nice looking|clean|modern",
            "helpful": r"helpful|useful|saves time|productive|efficient",
            "reliability": r"reliable|stable|works great|never crashes",
            "features": r"love the|great feature|amazing|fantastic|excellent",
            "value": r"worth|value|free|affordable|good price",
            "support": r"great support|responsive|helpful team",
            "regular_updates": r"regular updates|constantly improving|keeps getting better"
        }
        
        highlights = []
        
        for pattern_name, pattern in love_patterns.items():
            matches = []
            
            for review in positive_reviews:
                text = review.get("text", "")
                if re.search(pattern, text, re.IGNORECASE):
                    matches.append(text)
            
            if matches:
                highlights.append({
                    "aspect": pattern_name.replace("_", " ").title(),
                    "mentions": len(matches),
                    "percentage_of_positive": round((len(matches) / len(positive_reviews)) * 100, 1),
                    "sample_feedback": matches[:3]
                })
        
        highlights.sort(key=lambda x: x["mentions"], reverse=True)
        
        return highlights[:8]
    
    def _extract_improvement_suggestions(self, reviews: List[Dict[str, Any]]) -> List[str]:
        """Extract user suggestions for improvements."""
        suggestions = []
        
        # Patterns that indicate suggestions
        suggestion_patterns = [
            r"would be (better|great|nice) if",
            r"should (add|have|include)",
            r"wish (it|the app|this)",
            r"needs? (to|more)",
            r"please (add|include|make)",
            r"hope (to see|you add|for)",
            r"suggest",
            r"recommendation",
            r"feature request"
        ]
        
        for review in reviews:
            text = review.get("text", "")
            
            for pattern in suggestion_patterns:
                matches = re.findall(f"{pattern}[^.!?]*[.!?]", text, re.IGNORECASE)
                suggestions.extend(matches)
        
        # Clean and deduplicate suggestions
        cleaned_suggestions = []
        seen = set()
        
        for suggestion in suggestions:
            # Basic cleaning
            suggestion = suggestion.strip()
            if len(suggestion) > 20 and suggestion.lower() not in seen:
                seen.add(suggestion.lower())
                cleaned_suggestions.append(suggestion)
        
        return cleaned_suggestions[:10]  # Top 10 suggestions
    
    def _find_competitor_mentions(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find mentions of competitor apps."""
        # Common competitor app names (would be customized per category)
        competitors = [
            "competitor", "alternative", "other app", "switched from",
            "better than", "worse than", "compared to", "unlike"
        ]
        
        competitor_mentions = []
        
        for review in reviews:
            text = review.get("text", "").lower()
            
            for comp in competitors:
                if comp in text:
                    # Extract the sentence containing the mention
                    sentences = text.split('.')
                    for sentence in sentences:
                        if comp in sentence:
                            competitor_mentions.append({
                                "mention": sentence.strip(),
                                "sentiment": TextBlob(sentence).sentiment.polarity,
                                "rating": review.get("rating", 0)
                            })
        
        if competitor_mentions:
            avg_sentiment = sum(m["sentiment"] for m in competitor_mentions) / len(competitor_mentions)
            
            return {
                "found_mentions": True,
                "mention_count": len(competitor_mentions),
                "average_sentiment_in_comparisons": round(avg_sentiment, 3),
                "sample_mentions": [m["mention"] for m in competitor_mentions[:5]]
            }
        
        return {"found_mentions": False}
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label."""
        if score > 0.5:
            return "Very Positive"
        elif score > 0.1:
            return "Positive"
        elif score > -0.1:
            return "Neutral"
        elif score > -0.5:
            return "Negative"
        else:
            return "Very Negative"
    
    def _check_sentiment_consistency(self, rating: int, sentiment: float) -> str:
        """Check if sentiment matches rating."""
        if rating >= 4 and sentiment > 0.1:
            return "Consistent"
        elif rating <= 2 and sentiment < -0.1:
            return "Consistent"
        elif rating == 3 and -0.1 <= sentiment <= 0.1:
            return "Consistent"
        else:
            return "Inconsistent - review text doesn't match rating"
    
    def _analyze_theme_sentiment(self, theme: str, reviews: List[Dict[str, Any]]) -> float:
        """Analyze sentiment for a specific theme."""
        sentiments = []
        
        for review in reviews:
            text = review.get("text", "").lower()
            if theme in text:
                # Extract sentences containing the theme
                sentences = text.split('.')
                for sentence in sentences:
                    if theme in sentence:
                        blob = TextBlob(sentence)
                        sentiments.append(blob.sentiment.polarity)
        
        return round(sum(sentiments) / len(sentiments), 3) if sentiments else 0
    
    def _categorize_theme(self, theme: str) -> str:
        """Categorize a theme into predefined categories."""
        categories = {
            "functionality": ["feature", "function", "tool", "option"],
            "usability": ["easy", "simple", "interface", "design"],
            "performance": ["fast", "slow", "speed", "crash"],
            "content": ["content", "data", "information"],
            "pricing": ["price", "cost", "subscription", "free"]
        }
        
        theme_lower = theme.lower()
        for category, keywords in categories.items():
            if any(keyword in theme_lower for keyword in keywords):
                return category
        
        return "other"
    
    def _calculate_severity(self, issue_type: str, matches: List[str]) -> str:
        """Calculate severity of an issue based on language used."""
        severe_words = ["terrible", "horrible", "awful", "worst", "unacceptable", "disaster"]
        
        severe_count = sum(1 for match in matches if any(word in match.lower() for word in severe_words))
        
        severity_ratio = severe_count / len(matches)
        
        if severity_ratio > 0.5:
            return "Critical"
        elif severity_ratio > 0.2:
            return "High"
        elif issue_type in ["crashes", "data_loss", "security"]:
            return "High"
        else:
            return "Medium"
    
    def _calculate_trend_direction(self, trends: Dict[str, Dict[str, Any]]) -> str:
        """Calculate overall trend direction."""
        if len(trends) < 2:
            return "Insufficient data"
        
        # Get first and last periods
        sorted_periods = sorted(trends.keys())
        first_sentiment = trends[sorted_periods[0]]["average_sentiment"]
        last_sentiment = trends[sorted_periods[-1]]["average_sentiment"]
        
        change = last_sentiment - first_sentiment
        
        if change > 0.1:
            return "Improving"
        elif change < -0.1:
            return "Declining"
        else:
            return "Stable"