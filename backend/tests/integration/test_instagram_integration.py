#!/usr/bin/env python3
"""
Integration test for Instagram Posts feature
Tests both the agent directly and the API endpoints
"""

import requests
import json
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api_endpoints():
    """Test the API endpoints for Instagram posts"""
    
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Instagram Posts API Integration")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check passed")
            print(f"   Write Hashtag Agent Enabled: {health_data.get('write_hashtag_agent_enabled', False)}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test 2: Generate Instagram post
    print("\n2. Testing Instagram post generation...")
    test_request = {
        "affirmation": "Ich bin voller Energie und Lebenskraft",
        "period_name": "Energie",
        "style": "inspirational"
    }
    
    try:
        response = requests.post(f"{base_url}/generate-instagram-post", 
                               json=test_request)
        if response.status_code == 200:
            post_data = response.json()
            if post_data.get("success"):
                print("✅ Instagram post generation successful")
                post = post_data["post"]
                print(f"   Post Text Length: {len(post['post_text'])} characters")
                print(f"   Hashtags Count: {len(post['hashtags'])}")
                print(f"   Period: {post['period_name']}")
                print(f"   Style: {post['style']}")
                print(f"   Has CTA: {'call_to_action' in post}")
                print(f"   Has Strategies: {'engagement_strategies' in post}")
            else:
                print(f"❌ Post generation failed: {post_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Post generation failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Post generation failed: {e}")
        return False
    
    # Test 3: Get all Instagram posts
    print("\n3. Testing Instagram posts retrieval...")
    try:
        response = requests.get(f"{base_url}/instagram-posts")
        if response.status_code == 200:
            posts_data = response.json()
            if posts_data.get("success"):
                print(f"✅ Posts retrieval successful")
                print(f"   Total Posts: {posts_data['count']}")
                if posts_data['count'] > 0:
                    sample_post = posts_data['posts'][0]
                    print(f"   Sample Post ID: {sample_post['id']}")
                    print(f"   Sample Period: {sample_post['period_name']}")
            else:
                print(f"❌ Posts retrieval failed: {posts_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Posts retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Posts retrieval failed: {e}")
        return False
    
    # Test 4: Get posts filtered by period
    print("\n4. Testing filtered posts retrieval...")
    try:
        response = requests.get(f"{base_url}/instagram-posts?period_name=Energie")
        if response.status_code == 200:
            filtered_data = response.json()
            if filtered_data.get("success"):
                print(f"✅ Filtered posts retrieval successful")
                print(f"   Energie Posts: {filtered_data['count']}")
            else:
                print(f"❌ Filtered posts retrieval failed: {filtered_data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Filtered posts retrieval failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Filtered posts retrieval failed: {e}")
        return False
    
    # Test 5: Test invalid inputs
    print("\n5. Testing error handling...")
    invalid_request = {
        "affirmation": "",
        "period_name": "InvalidPeriod",
        "style": "inspirational"
    }
    
    try:
        response = requests.post(f"{base_url}/generate-instagram-post", 
                               json=invalid_request)
        if response.status_code == 500:
            print("✅ Error handling works correctly for invalid inputs")
        else:
            print(f"⚠️ Unexpected response for invalid input: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error during error handling test: {e}")
    
    print("\n🎉 All API integration tests completed successfully!")
    return True

def test_direct_agent():
    """Test the agent directly"""
    
    print("\n🤖 Testing Write and Hashtag Research Agent Directly")
    print("=" * 55)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found. Skipping direct agent test.")
        return False
    
    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
        from app.agents.write_hashtag_research_agent import WriteHashtagResearchAgent
        
        print("✅ Agent imported successfully")
        
        # Initialize agent
        agent = WriteHashtagResearchAgent(api_key)
        print("✅ Agent initialized successfully")
        
        # Test generation
        result = agent.generate_instagram_post(
            affirmation="Ich bin kreativ und inspiriert",
            period_name="Kreativität",
            style="artistic"
        )
        
        if result['success']:
            print("✅ Direct agent test successful")
            post = result['post']
            print(f"   Generated Post ID: {post['id']}")
            print(f"   Period Color: {post['period_color']}")
            print(f"   Hashtags Preview: {' '.join(post['hashtags'][:5])}...")
        else:
            print(f"❌ Direct agent test failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Direct agent test failed: {e}")
        return False
    
    return True

def main():
    """Run all integration tests"""
    
    print("🚀 Instagram Posts Integration Test Suite")
    print("=" * 60)
    
    # Test API endpoints
    api_success = test_api_endpoints()
    
    # Test direct agent (optional, requires API key)
    agent_success = test_direct_agent()
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"API Endpoints Test: {'✅ PASSED' if api_success else '❌ FAILED'}")
    print(f"Direct Agent Test: {'✅ PASSED' if agent_success else '❌ FAILED'}")
    
    if api_success:
        print("\n🎉 Integration is working correctly!")
        print("\nNext steps:")
        print("1. Open http://localhost:3000/instagram-posts in your browser")
        print("2. Test the frontend interface manually")
        print("3. Generate some Instagram posts and verify the UI")
        print("4. Test the copy functionality")
    else:
        print("\n❌ Integration test failed. Please check:")
        print("1. Backend server is running on http://localhost:8000")
        print("2. OPENAI_API_KEY is set in your environment")
        print("3. All dependencies are installed")
    
    return api_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)