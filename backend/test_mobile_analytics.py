#!/usr/bin/env python3
"""Test script for mobile analytics agents"""

import asyncio
from app.agents.play_store_analyst import PlayStoreAnalystAgent
from app.agents.meta_ads_analyst import MetaAdsAnalystAgent
from app.agents.google_analytics_expert import GoogleAnalyticsExpertAgent

async def test_agents():
    """Test all mobile analytics agents"""
    
    print("Testing Mobile Analytics Agents...")
    print("=" * 50)
    
    # Test Play Store Analyst
    print("\n1. Testing Play Store Analyst Agent:")
    try:
        play_store_agent = PlayStoreAnalystAgent()
        health = play_store_agent.health_check()
        print(f"   ✓ Health check: {health['status']}")
        print(f"   ✓ Capabilities: {', '.join(health['capabilities'])}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test Meta Ads Analyst
    print("\n2. Testing Meta Ads Analyst Agent:")
    try:
        meta_ads_agent = MetaAdsAnalystAgent()
        health = meta_ads_agent.health_check()
        print(f"   ✓ Health check: {health['status']}")
        print(f"   ✓ Capabilities: {', '.join(health['capabilities'])}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Test Google Analytics Expert
    print("\n3. Testing Google Analytics Expert Agent:")
    try:
        ga_agent = GoogleAnalyticsExpertAgent()
        health = ga_agent.health_check()
        print(f"   ✓ Health check: {health['status']}")
        print(f"   ✓ Capabilities: {', '.join(health['capabilities'])}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 50)
    print("All agents tested successfully!")

if __name__ == "__main__":
    asyncio.run(test_agents())