"""Mock data for Threads profiles with realistic patterns."""

from typing import Dict, Any

# Mock data for different types of accounts
MOCK_PROFILES = {
    "iam.affirmations": {
        "handle": "iam.affirmations",
        "display_name": "I AM Affirmations",
        "bio": "Daily affirmations & positive mindset 🌟 Transform your life one thought at a time",
        "verified": False,
        "followers": 12543,
        "following": 487,
        "posts_count": 234,
        "posts_analyzed": 20,
        "engagement_metrics": {
            "avg_likes": 156.5,
            "avg_comments": 23.4,
            "avg_reposts": 8.2,
            "total_engagement": 188.1
        },
        "content_patterns": {
            "avg_post_length": 125,
            "post_types": {"text": 18, "media": 2},
            "uses_hashtags": False,  # Based on your observation
            "hashtag_count": 0,
            "top_hashtags": [],
            "hashtag_frequency": {},
            "mentions_others": True,
            "unique_mentions": 5
        },
        "content_themes": [
            "Affirmations",
            "Self-care",
            "Personal Growth",
            "Mindfulness",
            "Gratitude"
        ],
        "posting_behavior": {
            "total_posts_analyzed": 20,
            "has_consistent_style": True
        },
        "insights": {
            "uses_hashtags": False,
            "top_hashtags": [],
            "hashtag_strategy": "No hashtags used",
            "avg_engagement": 188.1,
            "content_mix": {
                "text_posts": "90%",
                "media_posts": "10%",
                "avg_post_length": 125
            },
            "posting_consistency": True
        }
    },
    "mindfulmoments": {
        "handle": "mindfulmoments",
        "display_name": "Mindful Moments",
        "bio": "Bringing peace to your feed 🧘‍♀️ Daily mindfulness practices",
        "verified": True,
        "followers": 45678,
        "following": 234,
        "posts_count": 567,
        "posts_analyzed": 20,
        "engagement_metrics": {
            "avg_likes": 423.7,
            "avg_comments": 67.3,
            "avg_reposts": 34.5,
            "total_engagement": 525.5
        },
        "content_patterns": {
            "avg_post_length": 180,
            "post_types": {"text": 12, "media": 8},
            "uses_hashtags": True,
            "hashtag_count": 15,
            "top_hashtags": ["#mindfulness", "#meditation", "#wellness", "#selfcare", "#mentalhealth"],
            "hashtag_frequency": {
                "#mindfulness": 18,
                "#meditation": 15,
                "#wellness": 12,
                "#selfcare": 10,
                "#mentalhealth": 8
            },
            "mentions_others": True,
            "unique_mentions": 12
        },
        "content_themes": [
            "Mindfulness",
            "Meditation",
            "Mental Health",
            "Wellness",
            "Self-care"
        ],
        "posting_behavior": {
            "total_posts_analyzed": 20,
            "has_consistent_style": True
        },
        "insights": {
            "uses_hashtags": True,
            "top_hashtags": ["#mindfulness", "#meditation", "#wellness", "#selfcare", "#mentalhealth"],
            "hashtag_strategy": "Uses hashtags",
            "avg_engagement": 525.5,
            "content_mix": {
                "text_posts": "60%",
                "media_posts": "40%",
                "avg_post_length": 180
            },
            "posting_consistency": True
        }
    }
}


def get_mock_profile_data(username: str) -> Dict[str, Any]:
    """Get mock profile data for a username."""
    # Clean username
    username = username.lstrip('@').lower()
    
    # Return specific mock data if available
    if username in MOCK_PROFILES:
        return MOCK_PROFILES[username]
    
    # Return generic mock data for unknown profiles
    return {
        "handle": username,
        "display_name": username,
        "bio": "Profile bio",
        "verified": False,
        "followers": 1000,
        "following": 100,
        "posts_count": 50,
        "posts_analyzed": 10,
        "engagement_metrics": {
            "avg_likes": 50,
            "avg_comments": 10,
            "avg_reposts": 5,
            "total_engagement": 65
        },
        "content_patterns": {
            "avg_post_length": 100,
            "post_types": {"text": 8, "media": 2},
            "uses_hashtags": True,
            "hashtag_count": 5,
            "top_hashtags": ["#inspiration", "#motivation"],
            "hashtag_frequency": {"#inspiration": 5, "#motivation": 3},
            "mentions_others": False,
            "unique_mentions": 0
        },
        "content_themes": ["General Content"],
        "posting_behavior": {
            "total_posts_analyzed": 10,
            "has_consistent_style": False
        },
        "insights": {
            "uses_hashtags": True,
            "top_hashtags": ["#inspiration", "#motivation"],
            "hashtag_strategy": "Uses hashtags",
            "avg_engagement": 65,
            "content_mix": {
                "text_posts": "80%",
                "media_posts": "20%",
                "avg_post_length": 100
            },
            "posting_consistency": False
        }
    }