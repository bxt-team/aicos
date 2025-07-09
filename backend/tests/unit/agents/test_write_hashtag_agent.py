#!/usr/bin/env python3
"""
Test script for the Write and Hashtag Research Agent
"""

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from backend.agents.write_hashtag_research_agent import WriteHashtagResearchAgent

def test_agent():
    """Test the Write and Hashtag Research Agent"""
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: OPENAI_API_KEY environment variable is not set")
        return False
    
    print("🚀 Testing Write and Hashtag Research Agent...")
    
    try:
        # Initialize the agent
        agent = WriteHashtagResearchAgent(api_key)
        print("✅ Agent initialized successfully")
        
        # Test data
        test_cases = [
            {
                "affirmation": "Ich bin voller Energie und Lebenskraft",
                "period_name": "Energie",
                "style": "inspirational"
            },
            {
                "affirmation": "Ich vertraue auf meine Kreativität und lasse sie frei fließen",
                "period_name": "Kreativität",
                "style": "motivational"
            },
            {
                "affirmation": "Ich bin stolz auf mein authentisches Selbst",
                "period_name": "Image",
                "style": "empowering"
            }
        ]
        
        print("\n📝 Testing Instagram post generation...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n--- Test Case {i}: {test_case['period_name']} ---")
            print(f"Affirmation: {test_case['affirmation']}")
            
            # Generate Instagram post
            result = agent.generate_instagram_post(
                affirmation=test_case['affirmation'],
                period_name=test_case['period_name'],
                style=test_case['style']
            )
            
            if result['success']:
                post = result['post']
                print(f"✅ Post generated successfully!")
                print(f"📄 Post Text (first 100 chars): {post['post_text'][:100]}...")
                print(f"🏷️ Hashtags: {len(post['hashtags'])} hashtags")
                print(f"📞 Call-to-Action: {post['call_to_action'][:60]}...")
                print(f"📈 Engagement Strategies: {len(post['engagement_strategies'])}")
                print(f"🕐 Optimal Posting Time: {post['optimal_posting_time']}")
                print(f"🎨 Period Color: {post['period_color']}")
            else:
                print(f"❌ Failed to generate post: {result.get('error', 'Unknown error')}")
                return False
        
        print("\n🔍 Testing post retrieval...")
        
        # Test getting all posts
        all_posts = agent.get_generated_posts()
        if all_posts['success']:
            print(f"✅ Retrieved {all_posts['count']} total posts")
        else:
            print(f"❌ Failed to retrieve posts: {all_posts.get('error', 'Unknown error')}")
            return False
        
        # Test getting posts by period
        energie_posts = agent.get_generated_posts("Energie")
        if energie_posts['success']:
            print(f"✅ Retrieved {energie_posts['count']} posts for 'Energie' period")
        else:
            print(f"❌ Failed to retrieve Energie posts: {energie_posts.get('error', 'Unknown error')}")
            return False
        
        print("\n🎯 Testing with sample full post...")
        
        # Display a complete example
        if all_posts['count'] > 0:
            sample_post = all_posts['posts'][0]
            print(f"\n📱 Sample Instagram Post for {sample_post['period_name']}:")
            print(f"🎨 Color: {sample_post['period_color']}")
            print(f"📝 Affirmation: {sample_post['affirmation']}")
            print(f"\n📄 Post Text:\n{sample_post['post_text']}")
            print(f"\n🏷️ Hashtags ({len(sample_post['hashtags'])}):")
            print(" ".join(sample_post['hashtags'][:10]) + "..." if len(sample_post['hashtags']) > 10 else " ".join(sample_post['hashtags']))
            print(f"\n📞 Call-to-Action:\n{sample_post['call_to_action']}")
            print(f"\n📈 Engagement Strategies:")
            for strategy in sample_post['engagement_strategies'][:3]:
                print(f"  • {strategy}")
        
        print("\n✅ All tests completed successfully!")
        print("🎉 Write and Hashtag Research Agent is working correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent()
    sys.exit(0 if success else 1)